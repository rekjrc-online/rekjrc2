from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max, Count, Sum, Exists, OuterRef, Value, FloatField
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from crud.views import CrudContextMixin
from posts.models import Post
from races.models import Race, RaceDriver
from .models import Judge, JudgedEventRun, JudgedEventRunScore
import json


class Start_(LoginRequiredMixin, View):
    template_name = "races/judged_start.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        # ---- Race-level ----
        judges = Judge.objects.filter(race=race).order_by('id')
        race.is_judge = judges.filter(user=request.user).exists()
        race.judge_count = judges.count()
        # ---- Driver-level (everything here) ----
        racedrivers = (
            RaceDriver.objects
            .filter(race=race)
            .annotate(
                score_count=Count('judgedeventrun__scores'),
                score_total=Coalesce(
                    Sum('judgedeventrun__scores__score'),
                    Value(0.0),
                    output_field=FloatField()
                ),
                judge_done=Exists(
                    JudgedEventRunScore.objects.filter(
                        run__racedriver=OuterRef('pk'),
                        judge=request.user
                    )
                )
            )
            .order_by('id')
        )
        return render(request, self.template_name, {
            'race': race,
            'racedrivers': racedrivers,
            'judges': judges,
        })

class JudgeAdd(View):
    template_name = "races/judge_add.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        return render(request, self.template_name, {"race":race})

    def post(self, request, *args, **kwargs):
        qr_text = request.POST.get("qr_data")
        if not qr_text:
            return HttpResponseBadRequest("No QR code data received.")
        try:
            data = json.loads(qr_text)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid QR code format.")
        print()
        print()
        print("DATA",data)
        print()
        print()
        race = get_object_or_404(Race, uuid=self.kwargs["race_uuid"])
        judge_id = data.get("id")
        if Judge.objects.filter(race=race, user_id=judge_id).exists():
            return HttpResponseBadRequest("Judge already exists for this race.")
        if RaceDriver.objects.filter(race=race, user=request.user).exists():
            return HttpResponseBadRequest("Cannot judge a race you have already entered.")
        judge = Judge.objects.create(
            race = race,
            user_id = judge_id)
        return redirect("races:detail", uuid=race.uuid)

class JudgeRemove(CrudContextMixin, View):
    def get(self, request, race_uuid, judge_uuid):
        judge = get_object_or_404(Judge, uuid=judge_uuid)
        judge.delete()
        return redirect("races:detail", uuid=race_uuid)

class Race_(LoginRequiredMixin, View):
    template_name = "races/dragrace.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        rounds = (JudgedEventRun.objects.filter(race=race).order_by("round_number", "id"))
        final_winner = None
        if rounds.exists():
            max_round = rounds.aggregate(max_round=Max("round_number"))["max_round"]
            current_round = rounds.filter(round_number=max_round)
            if current_round.exists() and all(r.winner for r in current_round):
                winners = [r.winner for r in current_round]
                if len(winners) > 1:
                    for i in range(0, len(winners), 2):
                        JudgedEventRun.objects.create(
                            race=race,
                            model1=winners[i],
                            model2=winners[i + 1] if i + 1 < len(winners) else None,
                            round_number=max_round + 1)
                    return redirect("dragrace:dragrace", race_uuid=race.uuid)
                if len(winners) == 1 and not race.race_finished:
                    final_winner = winners[0]

        return render(request, self.template_name, {
            "race": race,
            "rounds": rounds,
            "final_winner": final_winner,
        })

    # --------------------------------------------------
    # POST — save match winners only
    # --------------------------------------------------
    def post(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)

        if race.race_finished or race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)

        for match in JudgedEventRun.objects.filter(race=race):
            winner_id = request.POST.get(f"winner_{match.id}")
            if not winner_id:
                continue

            winner = RaceDriver.objects.filter(id=winner_id).first()
            if winner:
                match.winner = winner
                match.save(update_fields=["winner"])

        return redirect("dragrace:dragrace", race_uuid=race.uuid)


class Finish_(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)

        if race.race_finished or race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)

        rounds = JudgedEventRun.objects.filter(race=race)

        max_round = rounds.aggregate(
            max_round=Max("round_number")
        )["max_round"]

        final_round = rounds.filter(round_number=max_round)

        # Must be exactly one final match
        if final_round.count() != 1:
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        final_match = final_round.first()
        if not final_match.winner:
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        racedriver1=final_match.model1
        racedriver2=final_match.model2
        if final_match.winner == final_match.model1:
            racedriver1.finish_position = 1
            racedriver2.finish_position = 2
        else:
            racedriver1.finish_position = 2
            racedriver2.finish_position = 1
        racedriver1.save(update_fields=["finish_position"])
        racedriver2.save(update_fields=["finish_position"])

        final_winner = final_match.winner

        # --------------------------------------------------
        # Build results content
        # --------------------------------------------------
        lines = [
            "🏁 Winner 🏁",
            f"Driver: {final_winner.driver}",
            f"Build: {final_winner.build}",
            "",
        ]

        current_round = None
        for match in rounds.order_by("round_number", "id"):
            if match.round_number != current_round:
                current_round = match.round_number
                lines.append(f"= Round {current_round} =")

            if match.winner == match.model1:
                lines.append(
                    f"🏁 {match.model1.driver} vs {match.model2.driver}"
                )
            else:
                lines.append(
                    f"{match.model1.driver} vs 🏁 {match.model2.driver}"
                )

        content = "\r\n".join(lines)

        # --------------------------------------------------
        # Create Post (GenericForeignKey)
        # --------------------------------------------------
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content)

        race.race_finished = True
        race.save(update_fields=["race_finished"])

        return redirect("races:detail", uuid=race.uuid)
