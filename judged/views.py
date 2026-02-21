from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Sum, Exists, OuterRef, Value, FloatField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from posts.models import Post
from races.models import Race, RaceDriver
from .models import JudgedScore


def _is_judge(race, user):
    """True if user is a member of the race's judge_team."""
    if not race.judge_team:
        return False
    return race.judge_team.members.filter(user=user).exists()


def _judge_count(race):
    """Number of judges = members of judge_team, or 0 if no judge_team."""
    if not race.judge_team:
        return 0
    return race.judge_team.members.count()


class Start_(LoginRequiredMixin, View):
    template_name = "races/judged_start.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        race.is_judge = _is_judge(race, request.user)
        if not race.is_judge and race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)
        race.judge_count = _judge_count(race)
        racedrivers = (
            RaceDriver.objects
            .filter(race=race)
            .annotate(
                score_count=Count('judged_scores'),
                score_total=Coalesce(
                    Sum('judged_scores__score'),
                    Value(0.0),
                    output_field=FloatField()
                ),
                judge_done=Exists(
                    JudgedScore.objects.filter(
                        race=race,
                        racedriver=OuterRef('pk'),
                        judge=request.user
                    )
                )
            )
            .order_by('id')
        )
        return render(request, self.template_name, {
            'race': race,
            'racedrivers': racedrivers,
        })


class Judge_(LoginRequiredMixin, View):
    template_name = "races/judged_judge.html"

    def get(self, request, race_uuid, racedriver_id):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        if not _is_judge(race, request.user):
            return redirect("races:detail", uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, id=racedriver_id, race=race)
        if JudgedScore.objects.filter(race=race, racedriver=racedriver, judge=request.user).exists():
            return redirect("judged:start", race_uuid=race.uuid)
        return render(request, self.template_name, {
            "race": race,
            "racedriver": racedriver,
        })

    def post(self, request, race_uuid, racedriver_id):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        if not _is_judge(race, request.user):
            return redirect("races:detail", uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, id=racedriver_id, race=race)
        if JudgedScore.objects.filter(race=race, racedriver=racedriver, judge=request.user).exists():
            return redirect("judged:start", race_uuid=race.uuid)
        try:
            score = float(request.POST.get('score'))
        except (TypeError, ValueError):
            return redirect("judged:start", race_uuid=race.uuid)
        JudgedScore.objects.create(
            race=race,
            racedriver=racedriver,
            judge=request.user,
            score=score)
        return redirect("judged:start", race_uuid=race.uuid)


class Finish_(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        judge_count = _judge_count(race)
        if judge_count == 0:
            return redirect("judged:start", race_uuid=race.uuid)
        racedrivers = (
            RaceDriver.objects
            .filter(race=race)
            .annotate(
                score_count=Count('judged_scores__score'),
                score_total=Coalesce(
                    Sum('judged_scores__score'),
                    Value(0.0),
                    output_field=FloatField()
                ),
            )
            .order_by('-score_total')
        )
        for rd in racedrivers:
            if rd.score_count < judge_count:
                return redirect("judged:start", race_uuid=race.uuid)

        high_score = racedrivers[0].score_total
        winners = [rd for rd in racedrivers if rd.score_total == high_score]

        if len(winners) == 1:
            winner = winners[0]
            content = f"🏁 Winner 🏁\r\nDriver: {winner.driver}\r\nBuild: {winner.build}\r\n"
        else:
            content = "🏁 Winners (tie) 🏁\r\n"
            for rd in winners:
                content += f"Driver: {rd.driver} | Build: {rd.build}\r\n"

        result_lines = [content]
        for idx, rd in enumerate(racedrivers, start=1):
            result_lines.append(f"{idx}. {rd.score_total:.1f} pts | {rd.driver} | {rd.build}")
        results_text = "\r\n".join(result_lines)

        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=results_text)

        race.race_finished = True
        race.entry_locked = True
        race.save()

        return redirect("races:start", uuid=race_uuid)