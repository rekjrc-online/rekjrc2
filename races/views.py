from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, CreateView, UpdateView, DeleteView
from builds.models import Build
from crud.views import CrudContextMixin, CrudAuthMixin, PublicDetailMixin
from drivers.models import Driver
from races.models import Race
from .forms import RaceForm, RaceJudgeDeviceForm
from .models import Race, RaceClass, RaceDriver, RaceJudgeDevice

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
            case "Rally":
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
        # Races I'm entered in: a RaceDriver registered by me, or for a
        # Driver I own. Races I own are already listed above, so skip them.
        driver_races = Race.objects.filter(
            Q(race_drivers__user=request.user) | Q(race_drivers__driver__owner=request.user),
            race_finished=False,
            is_active=True
        ).exclude(owner=request.user).distinct()

        return render(request, self.template_name, {
            'races': races,
            'judge_races': judge_races,
            'driver_races': driver_races,
        })

class Detail_(PublicDetailMixin, CrudContextMixin, DetailView):
    model = Race
    template_name = "races/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        race = self.object
        context['racedrivers'] = RaceDriver.objects.filter(race=race).select_related('driver', 'race_class')
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

    def _render(self, request, race, error=None):
        context = {
            "race": race,
            "drivers": Driver.objects.filter(owner=request.user, is_active=True),
            "builds": Build.objects.filter(owner=request.user, is_active=True),
            "race_classes": race.race_classes.all(),
            "error": error,
        }
        return render(request, self.template_name, context)

    def get(self, request, uuid):
        race = get_object_or_404(Race, uuid=uuid)
        if race.entry_locked==True:
            return render(request, "races/full.html", {'uuid': uuid})
        return self._render(request, race)

    def post(self, request, uuid):
        # NOT Race.for_user(request.user) -- that's owner/judge-scoped and
        # would 404 for the exact people this view exists for: a
        # participant who is neither the race owner nor a judge, joining
        # via the QR code Race.save() generates (races/<uuid>/join). GET
        # above already fetches the race unrestricted for the same reason;
        # POST used to disagree with it, which broke self-registration for
        # everyone except the organizer.
        race = get_object_or_404(Race, uuid=uuid)
        if race.entry_locked==True:
            return redirect("races:detail", uuid=uuid)
        driver_uuid = request.POST.get("driver_uuid")
        build_uuid = request.POST.get("build_uuid")
        transponder = request.POST.get("transponder")
        race_class_uuid = request.POST.get("race_class_uuid")
        # is_active=True mirrors the dropdowns in _render(), so a deactivated
        # driver/build can't be entered via a hand-crafted POST either.
        driver = Driver.objects.filter(uuid=driver_uuid, owner=request.user, is_active=True).first() if driver_uuid else None
        build = Build.objects.filter(uuid=build_uuid, owner=request.user, is_active=True).first() if build_uuid else None
        # Class is required only when this race defines at least one. Scoped
        # to race.race_classes so a class UUID from a different race can't be
        # submitted.
        race_class = None
        if race.race_classes.exists():
            try:
                race_class = race.race_classes.filter(uuid=race_class_uuid).first() if race_class_uuid else None
            except ValidationError:
                race_class = None
            if race_class is None:
                return self._render(request, race, error="Please select a class.")
        # race_class is part of the dedupe key: the same driver+build may enter
        # the same race once per class (matches unique_race_driver_build).
        existing = RaceDriver.objects.filter(race=race, user=request.user, driver=driver, build=build, race_class=race_class).exists()
        if not existing:
            RaceDriver.objects.create(
                race=race,
                user=request.user,
                driver=driver,
                build=build,
                race_class=race_class,
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


class Flyer_(LoginRequiredMixin, View):
    """
    Owner-only printable flyer. Deliberately standalone plain HTML (does not
    extend base.html) so there's no site chrome/JS to fight with when
    printing. The QR code is rendered inline as a vector SVG (same join URL
    Race.save() encodes into the PNG) so it prints sharp at any size and
    doesn't depend on the media file existing.
    """
    template_name = "races/flyer.html"

    def get(self, request, uuid):
        import datetime
        import qrcode
        import qrcode.image.svg
        from django.utils.safestring import mark_safe

        race = get_object_or_404(
            Race.objects.select_related('event', 'location', 'track__location', 'judge_team', 'owner'),
            uuid=uuid, owner=request.user)

        join_url = f"https://www.rekjrc.com/races/{race.uuid}/join"
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
            image_factory=qrcode.image.svg.SvgPathImage)
        qr.add_data(join_url)
        qr.make(fit=True)
        qr_svg = qr.make_image().to_string(encoding='unicode')

        event = race.event
        event_end_date = None
        if event and event.event_days and event.event_days > 1:
            event_end_date = event.event_date + datetime.timedelta(days=event.event_days - 1)

        # Race's own location wins; otherwise fall back to the track's.
        location = race.location or (race.track.location if race.track else None)

        return render(request, self.template_name, {
            'race': race,
            'event': event,
            'event_end_date': event_end_date,
            'location': location,
            'race_classes': race.race_classes.all(),
            'join_url': join_url,
            'qr_svg': mark_safe(qr_svg),
        })


class RaceClasses_(LoginRequiredMixin, View):
    """
    Owner-only page to add / rename / delete a race's classes. Everything
    posts back to this one URL with an "action" field (add|rename|delete),
    then redirects here (post/redirect/get) with a flash message.
    """
    template_name = "races/classes.html"

    def _get_race(self, request, uuid):
        return get_object_or_404(Race, uuid=uuid, owner=request.user)

    def get(self, request, uuid):
        race = self._get_race(request, uuid)
        race_classes = race.race_classes.annotate(entry_count=Count('race_drivers'))
        return render(request, self.template_name, {
            'race': race,
            'race_classes': race_classes,
        })

    def post(self, request, uuid):
        race = self._get_race(request, uuid)
        action = request.POST.get('action')
        name = (request.POST.get('name') or '').strip()[:100]

        if action in ('rename', 'delete'):
            try:
                race_class = race.race_classes.filter(uuid=request.POST.get('class_uuid')).first()
            except ValidationError:
                race_class = None
            if race_class is None:
                messages.error(request, "Class not found.")
                return redirect('races:classes', uuid=uuid)

        if action in ('add', 'rename'):
            if not name:
                messages.error(request, "Class name can't be blank.")
                return redirect('races:classes', uuid=uuid)
            dupes = race.race_classes.filter(name__iexact=name)
            if action == 'rename':
                dupes = dupes.exclude(pk=race_class.pk)
            if dupes.exists():
                messages.error(request, f'This race already has a class named "{name}".')
                return redirect('races:classes', uuid=uuid)

        if action == 'add':
            RaceClass.objects.create(race=race, name=name)
            messages.success(request, f'Added class "{name}".')
        elif action == 'rename':
            old_name = race_class.name
            race_class.name = name
            race_class.save(update_fields=['name', 'updated_at'])
            messages.success(request, f'Renamed "{old_name}" to "{name}".')
        elif action == 'delete':
            # RaceDriver.race_class is SET_NULL, so entries in this class
            # stay in the race, just without a class.
            race_class.delete()
            messages.success(request, f'Deleted class "{race_class.name}".')
        return redirect('races:classes', uuid=uuid)


class JudgeDeviceRemove_(LoginRequiredMixin, View):
    """Remove a judge device assignment."""
    def post(self, request, uuid, assignment_id):
        race = get_object_or_404(Race, uuid=uuid, owner=request.user)
        RaceJudgeDevice.objects.filter(id=assignment_id, race=race).delete()
        return redirect('races:judge-device-add', uuid=uuid)