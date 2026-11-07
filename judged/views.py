from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver, RaceJudgeDevice
from . import services

# Kept under their old names -- other code/tests import these from here.
_is_judge = services.is_judge
_judge_count = services.judge_count


class Start_(LoginRequiredMixin, View):
    template_name = "races/judged_start.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        race.is_judge = _is_judge(race, request.user)
        if not race.is_judge and race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)
        race.judge_count = _judge_count(race)
        return render(request, self.template_name, {
            'race': race,
            'sections': services.sections(race, user=request.user),
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
        judge_device = RaceJudgeDevice.objects.filter(
            race=race, judge=request.user
        ).select_related('device').first()
        return render(request, self.template_name, {
            "race": race,
            "racedriver": racedriver,
            "run_number": services.next_run_number(race, racedriver, request.user),
            "judge_device": judge_device,
        })

    def post(self, request, race_uuid, racedriver_id):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        if not _is_judge(race, request.user):
            return redirect("races:detail", uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, id=racedriver_id, race=race)
        try:
            score = float(request.POST.get('score'))
        except (TypeError, ValueError):
            return redirect("judged:start", race_uuid=race.uuid)
        if not 0.0 <= score <= 10.0:
            return redirect("judged:start", race_uuid=race.uuid)
        services.record_score(race, racedriver, request.user, score)
        return redirect("judged:start", race_uuid=race.uuid)


class Finish_(LoginRequiredMixin, View):
    template_name = "races/judged_finish_confirm.html"

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return redirect("races:detail", uuid=race.uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        if _judge_count(race) == 0:
            return redirect("judged:start", race_uuid=race.uuid)
        secs = services.sections(race)
        # Runs some judges haven't scored yet don't count toward standings.
        # Make the owner confirm before finishing past them, rather than
        # blocking Finish until every run is complete (with re-runs, one
        # abandoned run would otherwise block the race forever).
        incomplete = services.incomplete_runs(secs)
        if incomplete and request.POST.get('confirm') != '1':
            return render(request, self.template_name, {
                'race': race,
                'incomplete': incomplete,
            })
        if not services.finish(race, secs):
            return redirect("judged:start", race_uuid=race.uuid)
        return redirect("races:start", uuid=race_uuid)
