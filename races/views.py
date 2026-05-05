from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from builds.models import Build
from crud.views import CrudContextMixin, CrudAuthMixin
from drivers.models import Driver
from races.models import Race
from .forms import RaceForm, RaceJudgeDeviceForm
from .models import Race, RaceDriver, RaceJudgeDevice

class Start_(View):
    def get(self, request, *args, **kwargs):
        race = get_object_or_404(Race.for_user(request.user), uuid=kwargs.get("uuid"))
        match race.race_type:
            case "Lap Race":
                return redirect("laprace:start", race_uuid=race.uuid)
            case "Drag Race":
                return redirect("dragrace:start", race_uuid=race.uuid)
            case "Drag Double":
                return redirect("dragdouble:start", race_uuid=race.uuid)
            case "Crawler Comp":
                return redirect("crawler:start", race_uuid=race.uuid)
            case "Stopwatch Race":
                return redirect("stopwatch:start", race_uuid=race.uuid)
            case "Long Jump":
                return redirect("longjump:start", race_uuid=race.uuid)
            case "Top Speed":
                return redirect("topspeed:start", race_uuid=race.uuid)
            case "Judged Event":
                return redirect("judged:start", race_uuid=race.uuid)
            case "Round Robin":
                return redirect("roundrobin:start", race_uuid=race.uuid)
            case "Swiss System":
                return redirect("swiss:start", race_uuid=race.uuid)
            case _:
                print("Unknown race_type=", race.race_type)
                return redirect("races:detail", uuid=race.uuid)

class List_(LoginRequiredMixin, View):
    template_name = "races/list.html"

    def get(self, request):
        races = Race.objects.filter(owner=request.user, is_active=True, race_finished=False)
        judge_races = Race.objects.filter(
            judge_team__members__user=request.user,
            race_finished=False,
            is_active=True
        ).distinct()

        return render(request, self.template_name, {
            'races': races,
            'judge_races': judge_races,
        })

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Race
    template_name = "races/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        race = self.object
        context['racedrivers'] = RaceDriver.objects.filter(race=race).select_related('driver')
        return context

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Race
    form_class = RaceForm
    action = "Create"
    template_name = "crud/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Race
    form_class = RaceForm
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
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
        race = get_object_or_404(Race.for_user(request.user), uuid=uuid)
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
        race = get_object_or_404(Race.for_user(request.user), uuid=uuid)
        if race.race_finished==True:
            return HttpResponseForbidden("Race is already finished.")
        if race.entry_locked==True:
            race.entry_locked=False
        else:
            race.entry_locked=True
        race.save()
        return redirect("races:detail", uuid=uuid)


class JudgeDeviceAdd_(LoginRequiredMixin, View):
    """Assign a device to a judge for a judged race."""
    template_name = "races/judge_devices.html"

    def get(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid, owner=request.user)
        assignments = RaceJudgeDevice.objects.filter(race=race).select_related('judge', 'device')
        form = RaceJudgeDeviceForm(race=race, user=request.user)
        return render(request, self.template_name, {
            'race': race,
            'form': form,
            'assignments': assignments,
        })

    def post(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid, owner=request.user)
        form = RaceJudgeDeviceForm(request.POST, race=race, user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.race = race
            assignment.save()
        return redirect('races:judge-device-add', uuid=uuid)


class JudgeDeviceRemove_(LoginRequiredMixin, View):
    """Remove a judge device assignment."""
    def post(self, request, uuid, assignment_id):
        race = get_object_or_404(Race, uuid=uuid, owner=request.user)
        RaceJudgeDevice.objects.filter(id=assignment_id, race=race).delete()
        return redirect('races:judge-device-add', uuid=uuid)