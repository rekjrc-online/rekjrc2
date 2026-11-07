from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from . import services

class Start_(LoginRequiredMixin, View):
    template_name = 'races/topspeed_start.html'
    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        return render(request, self.template_name, {
            'race': race,
            'sections': services.sections(race) })

class Race_(LoginRequiredMixin, View):
    template_name = "races/topspeed_race.html"

    def get(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished==True:
            return HttpResponseForbidden("This race is already finished.")
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        return render(request, self.template_name, {
            'race': race,
            'racedriver': racedriver,
            'device': race.device,
        })

    def post(self, request, race_uuid, racedriver_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to submit times for this race.")
        if race.race_finished==True:
            return redirect("topspeed:start", race_uuid=race.uuid)
        racedriver = get_object_or_404(RaceDriver, uuid=racedriver_uuid, race=race)
        mph = services.parse_mph(request.POST.get('topspeed'))
        if mph is not None:
            services.record_topspeed(race, racedriver, mph)
        return redirect('topspeed:start', race_uuid=race_uuid)

class Finish_(LoginRequiredMixin, View):
    def post(self, request, race_uuid, *args, **kwargs):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You are not allowed to finish this race.")
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        if not services.finish(race):
            return HttpResponseForbidden("No runs found.")
        return redirect('races:start', uuid=race_uuid)
