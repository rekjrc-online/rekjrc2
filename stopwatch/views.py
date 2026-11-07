from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from . import services

class Start_(LoginRequiredMixin, View):
    template_name = 'races/stopwatch_start.html'
    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        return render(request, self.template_name, {
            'race': race,
            'sections': services.sections(race) })

class Race_(LoginRequiredMixin, View):
    template_name = "races/stopwatch_race.html"
    def get(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return redirect("stopwatch:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        mode = request.GET.get('mode', 'run')
        if mode not in ('run', 'enter'):
            mode = 'run'
        return render(request, self.template_name, {
            'race': race,
            'racedriver': racedriver,
            'mode': mode })
    def post(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to submit times for this race.")
        if race.race_finished==True:
            return redirect("stopwatch:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        seconds = services.parse_seconds(request.POST.get('elapsed_time'))
        if seconds is not None:
            services.record_time(race, racedriver, seconds)
        return redirect('stopwatch:start', race_uuid=race_uuid)

class Finish_(LoginRequiredMixin, View):
    def post(self, request, race_uuid, *args, **kwargs):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to finish this race.")
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        # A race with no recorded times can still be closed out. Rally races
        # fed by devices through the gateway left races unfinished forever
        # when this refused, and the Go /racedrivers/ lookup
        # (race_finished = false) kept serving their driver lists to devices
        # long after the event was over.
        services.finish(race)
        return redirect('races:start', uuid=race_uuid)
