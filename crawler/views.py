from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from posts.models import Post
from .models import CrawlerRun, CrawlerRunLog
import json

class Start_(LoginRequiredMixin, View):
    template_name = 'races/crawler_start.html'

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        racedrivers = RaceDriver.objects.filter(race=race).order_by('id')
        for racedriver in racedrivers:
            racedriver.run = CrawlerRun.objects.filter(race=race, racedriver=racedriver).first()
        return render(request, self.template_name, {
            'race': race,
            'racedrivers': racedrivers })

class Crawl_(LoginRequiredMixin, View):
    template_name = "races/crawler_crawl.html"

    def get(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return redirect("crawler:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid)
        run, _ = CrawlerRun.objects.get_or_create(race=race, racedriver=racedriver)
        return render(request, self.template_name, {
            'race': race,
            'racedriver': racedriver,
            'run': run })

    def post(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return redirect("crawler:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid)
        run = get_object_or_404(CrawlerRun, race=race, racedriver=racedriver)
        elapsed = request.POST.get('elapsed_time')
        points = request.POST.get('penalty_points')
        if elapsed is not None:
            run.elapsed_time = float(elapsed)
        if points is not None:
            run.penalty_points = int(points)
        run.save()
        run_log_json = request.POST.get('run_log')
        if run_log_json:
            log_entries = json.loads(run_log_json)
            run.log_entries.all().delete()
            post_text=str(racedriver) + '\r\n'
            post_text += 'Points: ' + str(points) + '\r\n'
            for entry in log_entries:
                post_text += entry['label'] + '\r\n'
                CrawlerRunLog.objects.create(
                    run=run,
                    milliseconds=entry['milliseconds'],
                    label=entry['label'],
                    delta=entry['delta'])
            Post.objects.create(
                author_content_type=ContentType.objects.get_for_model(Race),
                author_object_id=race.id,
                content=post_text)
        return redirect('crawler:start', race_uuid=race_uuid)

class Finish_(LoginRequiredMixin, View):
    def post(self, request, race_uuid, *args, **kwargs):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        runs = CrawlerRun.objects.filter(race=race).select_related('racedriver', 'racedriver__driver', 'racedriver__build')
        if not runs.exists():
            return HttpResponseForbidden("No runs found.")
        sorted_runs = runs.order_by('penalty_points', 'elapsed_time')
        lowest_points = sorted_runs.first().penalty_points
        winners = [run for run in sorted_runs if run.penalty_points == lowest_points]
        if len(winners) == 1:
            winner = winners[0]
            content = f"🏁 Winner 🏁\r\nDriver: {winner.racedriver.driver}\r\nModel: {winner.racedriver.build}\r\n"
        else:
            content = "🏁 Winners (tie) 🏁\r\n"
            for run in winners:
                content += f"Driver: {run.racedriver.driver} | Model: {run.racedriver.build}\r\n"
        result_lines = [content]
        result_lines += "\r\nFinal Leaderboard:"
        for idx, run in enumerate(sorted_runs, start=1):
            elapsed = f"{run.elapsed_time:.2f}s" if run.elapsed_time is not None else "No time"
            points = run.penalty_points
            match idx:
                case 1: idx_str = "🥇"
                case 2: idx_str = "🥈"
                case 3: idx_str = "🥉"
                case _: idx_str = f"{idx}"
            result_lines.append(f"{idx_str}. {run.racedriver.driver} | {run.racedriver.build} | {points} pts | {elapsed}")
        results_text = "\r\n".join(result_lines) or "No runs recorded."
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=results_text)
        race.race_finished = True
        race.entry_locked = True
        race.save()
        return redirect('races:start', uuid=race_uuid)
