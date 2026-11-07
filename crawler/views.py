from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from . import services

class Start_(LoginRequiredMixin, View):
    template_name = 'races/crawler_start.html'

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        return render(request, self.template_name, {
            'race': race,
            'sections': services.sections(race) })

class Crawl_(LoginRequiredMixin, View):
    template_name = "races/crawler_crawl.html"

    def get(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return redirect("crawler:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        return render(request, self.template_name, {
            'race': race,
            'racedriver': racedriver })

    def post(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return redirect("crawler:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        parsed = services.parse_run(request.POST.get('elapsed_time'), request.POST.get('penalty_points'))
        if parsed is not None:
            elapsed, points = parsed
            services.record_run(
                race, racedriver, elapsed, points,
                log_entries=services.parse_log(request.POST.get('run_log')))
        return redirect('crawler:start', race_uuid=race_uuid)

class Finish_(LoginRequiredMixin, View):
    def post(self, request, race_uuid, *args, **kwargs):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        if not services.finish(race):
            return HttpResponseForbidden("No runs found.")
        return redirect('races:start', uuid=race_uuid)
