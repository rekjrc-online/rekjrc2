from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from posts.models import Post
from .models import StopwatchRun
import json

class Start_(LoginRequiredMixin, View):
    template_name = 'races/stopwatch_start.html'
    def get(self, request, race_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        racedrivers = RaceDriver.objects.filter(race=race).order_by('id')
        for racedriver in racedrivers:
            racedriver.run = StopwatchRun.objects.filter(race=race, racedriver=racedriver).first()
        return render(request, self.template_name, {
            'race': race,
            'racedrivers': racedrivers })

class Race_(LoginRequiredMixin, View):
    template_name = "races/stopwatch_race.html"
    def get(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        if race.race_finished==True:
            return redirect("stopwatch:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid)
        run, _ = StopwatchRun.objects.get_or_create(race=race, racedriver=racedriver)
        return render(request, self.template_name, {
            'race': race,
            'racedriver': racedriver,
            'run': run })
    def post(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race, uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to submit times for this race.")
        if race.race_finished==True:
            return redirect("stopwatch:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid)
        run = get_object_or_404(StopwatchRun, race=race, racedriver=racedriver)
        if run.elapsed_time is not None:
            return HttpResponseForbidden("A time has already been recorded for this run.")
        elapsed = request.POST.get('elapsed_time')
        if elapsed is not None:
            run.elapsed_time = float(elapsed)
        run.save()
        post_text = f"{race} - Stopwatch Run Recorded\r\n\r\n{racedriver} - {run.elapsed_time:.2f}s\r\n"
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=post_text)
        return redirect('stopwatch:start', race_uuid=race_uuid)

class Finish_(LoginRequiredMixin, View):
    def post(self, request, race_uuid, *args, **kwargs):
        race = get_object_or_404(Race, uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to finish this race.")
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        runs = StopwatchRun.objects.filter(race=race).select_related('racedriver', 'racedriver__driver', 'racedriver__build')
        if not runs.exists():
            return HttpResponseForbidden("No runs found.")
        sorted_runs = runs.order_by('elapsed_time')
        fastest_time = sorted_runs.first().elapsed_time
        winners = [run for run in sorted_runs if run.elapsed_time == fastest_time]
        if len(winners) == 1:
            winner = winners[0]
            content = f"🏁 Winner 🏁\r\nDriver: {winner.racedriver.driver}\r\nBuild: {winner.racedriver.build}\r\n"
        else:
            content = "🏁 Winners (tie) 🏁\r\n"
            for run in winners:
                content += f"Driver: {run.racedriver.driver} | Model: {run.racedriver.build}\r\n"
        result_lines = [content]
        for idx, run in enumerate(sorted_runs, start=1):
            elapsed = f"{run.elapsed_time:.2f}s" if run.elapsed_time is not None else "No time"
            result_lines.append(f"{idx}. {elapsed} | {run.racedriver.driver} | {run.racedriver.build}")
        results_text = "\r\n".join(result_lines) or "No runs recorded."
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=results_text)
        race.race_finished = True
        race.entry_locked = True
        race.save()
        return redirect('races:start', uuid=race_uuid)
