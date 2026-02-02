from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from crud.views import CrudContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from drivers.models import Driver
from builds.models import Build
from .models import Race, RaceDriver

from django.shortcuts import get_object_or_404, redirect
from django.views import View
from races.models import Race


class Start_(View):
    def get(self, request, *args, **kwargs):
        race = get_object_or_404(Race, uuid=kwargs.get("uuid"))
        match race.race_type:
            case "Lap Race":
                return redirect("laprace:start", race_uuid=race.uuid)
            case "Drag Race":
                return redirect("dragrace:start", race_uuid=race.uuid)
            case "Crawler Comp":
                return redirect("crawler:start", race_uuid=race.uuid)
            case "Stopwatch Race":
                return redirect("stopwatch:start", race_uuid=race.uuid)
            case "Long Jump":
                return redirect("longjump:start", race_uuid=race.uuid)
            case "Top Speed":
                return redirect("topspeed:start", race_uuid=race.uuid)
            case "Judged Event":
                return redirect("judgedevent:start", race_uuid=race.uuid)
            case _:
                return redirect("races:detail", uuid=race.uuid)

class List_(CrudContextMixin, ListView):
    model = Race
    template_name = "races/list.html"
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

class Detail_(CrudContextMixin, DetailView):
    model = Race
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        race = self.object
        context['racedrivers'] = RaceDriver.objects.filter(race=race).select_related('driver')
        return context

class Create_(CrudContextMixin, CreateView):
    model = Race
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Race
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Race
    template_name = "crud/confirm_delete.html"
    success_url = "/races/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Join_(LoginRequiredMixin, View):
    template_name = "races/join.html"
    def get(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid)
        if race.entry_locked==True:
            return render(request, "races/full.html", {'uuid': uuid})
        drivers = Driver.objects.filter(owner=request.user)
        builds = Build.objects.filter(owner=request.user)
        context = {
            "race": race,
            "drivers": drivers,
            "builds": builds,
        }
        return render(request, self.template_name, context)
    def post(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid)
        if race.entry_locked==True:
            return redirect("races:detail", uuid=uuid)
        driver_uuid = request.POST.get("driver_uuid")
        build_uuid = request.POST.get("build_uuid")
        transponder = request.POST.get("transponder")
        driver = Driver.objects.filter(uuid=driver_uuid, owner=request.user).first() if driver_uuid else None
        build = Build.objects.filter(uuid=build_uuid, owner=request.user).first() if build_uuid else None
        existing = RaceDriver.objects.filter(race=race, user=request.user, driver=driver, build=build).exists()
        if not existing:
            RaceDriver.objects.create(
                race=race,
                user=request.user,
                driver=driver,
                build=build,
                transponder=transponder)
        return redirect("races:detail", uuid=uuid)

class Lock_(LoginRequiredMixin, View):
    def post(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid)
        if race.owner != request.user:
            return HttpResponseForbidden("You do not have permission to lock/unlock this race.")
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        if race.entry_locked==True:
            race.entry_locked=False
        else:
            race.entry_locked=True
        race.save()
        match race.race_type:
            case "Lap Race":
                return redirect("laprace:start", race_uuid=race.uuid)
            case "Drag Race":
                return redirect("dragrace:start", race_uuid=race.uuid)
            case "Crawler Comp":
                return redirect("crawler:start", race_uuid=race.uuid)
            case "Stopwatch Race":
                return redirect("stopwatch:start", race_uuid=race.uuid)
            case "Long Jump":
                return redirect("longjump:start", race_uuid=race.uuid)
            case "Top Speed":
                return redirect("topspeed:start", race_uuid=race.uuid)
            case "Judged Event":
                return redirect("judgedevent:start", race_uuid=race.uuid)
            case _:
                return redirect("races:detail", uuid=race.uuid)
