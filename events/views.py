import uuid as uuid_lib

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from crud.views import CrudContextMixin, CrudAuthMixin, PublicDetailMixin
from devices.models import Device, DevicePayload
from .forms import EventCheckinForm
from .models import Event, EventLocation, EventTeam, EventClub, EventStore, EventRace, EventCheckin
from django.shortcuts import get_object_or_404, redirect

User = get_user_model()


def _event_staff_queryset(user):
    """
    Events `user` is allowed to run check-in for: the ones they own, OR any
    event whose staff_team (a plain FK, set on the event itself -- NOT
    EventTeam, which is an unrelated many-to-many list of teams associated
    with the event some other way, e.g. participating/sponsoring) `user`
    belongs to (teams.TeamMember). Lets more than one person staff check-in
    at a real event without sharing the owner account -- set the event's
    staff_team once and every member of that team can then run check-in.

    .distinct() isn't needed here the way it was for the old EventTeam-based
    version: staff_team is a single FK per event, so the join can produce at
    most one Event row per TeamMember match, never a duplicate.
    """
    return Event.objects.filter(
        Q(owner=user) | Q(staff_team__members__user=user)
    )


class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Event
    template_name = "events/list.html"

    def get_context_data(self, **kwargs):
        # object_list (from CrudContextMixin/ListView's default get_queryset)
        # is already owner-scoped -- events this user created. This adds a
        # second section, same pattern as teams.List_'s member_teams: events
        # the user hasn't necessarily created but has a checked-in lanyard/
        # card for (events.EventCheckin, keyed on event+rfid_code, set via
        # the event's Checkin_ staff flow). Excludes events already shown
        # above so an owner who also checked themselves in doesn't see it
        # twice.
        context = super().get_context_data(**kwargs)
        context['checked_in_events'] = Event.objects.filter(
            checkins__user=self.request.user
        ).exclude(owner=self.request.user).distinct()
        return context

class Detail_(PublicDetailMixin, CrudContextMixin, DetailView):
    model = Event
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    # PublicDetailMixin now covers what this view used to override by hand:
    # any logged-in user can view any Event, and (new) an anonymous visitor
    # can too if the event's is_public flag is set. Update_/Delete_/
    # Advanced_ below still use CrudAuthMixin + CrudContextMixin's
    # owner-scoped default, and the "Owner functions" block in
    # crud/detail.html stays gated by is_owner, so this doesn't loosen
    # anything but read access to the detail page itself.

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Event
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Event
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Event
    template_name = "crud/confirm_delete.html"
    success_url = "/events/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Advanced_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Event
    template_name = "events/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class EventClubAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = EventClub
    fields = ["club"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Club"

    def form_valid(self, form):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventClubRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventClub
    template_name = "crud/confirm_delete.html"
    model_name = "Event Club"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        return get_object_or_404(EventClub, id=self.kwargs["id"], event=event)

class EventLocationAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = EventLocation
    fields = ["location"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Location"

    def form_valid(self, form):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventLocationRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventLocation
    template_name = "crud/confirm_delete.html"
    model_name = "Event Location"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        return get_object_or_404(EventLocation, id=self.kwargs["id"], event=event)

class EventRaceAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = EventRace
    fields = ["race"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Race"

    def form_valid(self, form):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventRaceRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventRace
    template_name = "crud/confirm_delete.html"
    model_name = "Event Race"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        return get_object_or_404(EventRace, id=self.kwargs["id"], event=event)

class EventStoreAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = EventStore
    fields = ["store"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Store"

    def form_valid(self, form):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventStoreRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventStore
    template_name = "crud/confirm_delete.html"
    model_name = "Event Store"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        return get_object_or_404(EventStore, id=self.kwargs["id"], event=event)

class EventTeamAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = EventTeam
    fields = ["team"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Team"

    def form_valid(self, form):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventTeamRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventTeam
    template_name = "crud/confirm_delete.html"
    model_name = "Event Team"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # owner=self.request.user: these Add/Remove endpoints previously had
        # no ownership check at all (only LoginRequiredMixin via
        # CrudAuthMixin) -- the "Advanced" button that links here is hidden
        # from non-owners in the template, but the URL itself was wide open
        # to any logged-in user who had or guessed the event uuid.
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"], owner=self.request.user)
        return get_object_or_404(EventTeam, id=self.kwargs["id"], event=event)


class Checkin_(CrudAuthMixin, FormView):
    """
    Staff walk-up check-in for one event: search for a participant's
    account, then scan or type their RFID lanyard code to link it to that
    account for this event. Re-submitting a code already linked for this
    event re-points it instead of erroring -- cards are physical hardware
    that gets lost/reissued/handed to someone else during the same event --
    see EventCheckinForm and the update_or_create below.

    Runnable by the event owner OR any member of the event's staff_team
    (a plain FK on Event, distinct from the EventTeam many-to-many list on
    the Advanced page) -- see _event_staff_queryset(). That's the
    delegation mechanism: set staff_team on the event (edit page or admin)
    to a Team whose members should be able to staff check-in without
    sharing the owner's account.

    Deliberately does NOT inherit CrudContextMixin -- like devices.Scan_,
    that mixin assumes a `self.model` (a ListView/DetailView-family
    attribute) which this FormView doesn't have, and would try to strip
    form fields this view never sets anyway.
    """
    form_class = EventCheckinForm
    template_name = "events/checkin.html"

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(_event_staff_queryset(request.user), uuid=kwargs["uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.event
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["event"] = self.event
        ctx["checkins"] = (
            self.event.checkins.select_related("user").order_by("-created_at")
        )
        q = self.request.GET.get("q", "").strip()
        ctx["query"] = q
        if q:
            # Name/email substring match for a typed search, OR an exact
            # match on User.uuid -- lets the "Scan account QR" flow
            # (events/checkin.html) drop the decoded QR payload's uuid
            # straight into this same search box and reuse this one query
            # instead of needing a separate lookup endpoint. The QR on
            # /accounts/ encodes {"uuid": "<account uuid>", "type": "user"}
            # (accounts.User._generate_qr()) -- accepting a bare uuid string
            # here is what makes that payload usable without extra plumbing.
            filters = Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
            try:
                filters |= Q(uuid=uuid_lib.UUID(q))
            except (ValueError, AttributeError, TypeError):
                pass
            ctx["user_results"] = User.objects.filter(filters).order_by("email")[:20]
        else:
            ctx["user_results"] = []
        # Set only by the QR-scan JS (as a hidden field appended before
        # submit) -- lets the template auto-select a single search result
        # without changing behavior for a normal typed search, where a
        # lone match should still require a manual click to confirm.
        ctx["scanned"] = self.request.GET.get("scanned") == "1"
        # Device picker for the RFID-scan poll (see CheckinRfidPoll_ below):
        # every known Device, not scoped to this event or to devices this
        # user owns/claimed -- an Event Checkin handheld is just whichever
        # physical unit is at the check-in table right now, and access to
        # the scans it reports is already gated by _event_staff_queryset on
        # the poll endpoint itself, so a wider device list here is harmless.
        ctx["devices"] = Device.objects.order_by("name")
        return ctx

    def form_valid(self, form):
        checkin, created = EventCheckin.objects.update_or_create(
            event=self.event,
            rfid_code=form.cleaned_data["rfid_code"],
            defaults={
                "user": form.cleaned_data["user"],
                "checked_in_by": self.request.user,
            },
        )
        verb = "Checked in" if created else "Re-linked"
        messages.success(
            self.request,
            f'{verb} card "{checkin.rfid_code}" to {checkin.user}.'
        )
        return redirect("events:checkin", uuid=self.event.uuid)

    def form_invalid(self, form):
        messages.error(self.request, "Pick an account and enter a card code.")
        return super().form_invalid(form)


class CheckinRfidPoll_(CrudAuthMixin, View):
    """
    GET /events/<uuid>/checkin/rfid-poll/?device=<device uuid>

    Bridges the Universal Keypad's Event Checkin firmware mode
    (rfid_checkin_mode.h, main menu -> A) to this check-in page: that mode
    only ever scans a lanyard and reports the UID to the normal ingest
    pipeline tagged name="rfidscan" (devices.DevicePayload) -- it never
    looks up or picks an account. Polled from checkin.html's JS every
    couple seconds while a device is selected in the picker; returns the
    oldest not-yet-consumed rfidscan payload for that device (if any) as
    {"uid": "<value>"} and marks it (and any other still-unconsumed
    rfidscan rows for that device, so switching away and back to this
    device doesn't replay a backlog) processed on the way out. {"uid":
    null} means nothing new since the last poll.

    Gated the same way as the rest of check-in (_event_staff_queryset) --
    a device's scan queue isn't otherwise tied to a specific event, so
    this is what stops an unrelated logged-in user from reading it.
    """
    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(_event_staff_queryset(request.user), uuid=kwargs["uuid"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        device_uuid = request.GET.get("device", "").strip()
        if not device_uuid:
            return JsonResponse({"uid": None})
        device = Device.objects.filter(uuid=device_uuid).first()
        if device is None:
            return JsonResponse({"uid": None})

        pending = list(
            DevicePayload.objects
            .filter(device=device, name="rfidscan", processed=False)
            .order_by("created_at")
        )
        if not pending:
            return JsonResponse({"uid": None})

        for payload in pending:
            payload.mark_processed()

        # If several scans queued up between polls (shouldn't normally
        # happen at a couple-second interval, but a network hiccup could
        # do it), only the most recent one is useful -- the earlier ones
        # were presumably already superseded by the next attendee's tap.
        return JsonResponse({"uid": pending[-1].value})


class CheckinRemove(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = EventCheckin
    template_name = "crud/confirm_delete.html"
    model_name = "Check-in"

    def get_success_url(self):
        return reverse("events:checkin", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        # Same access rule as Checkin_.dispatch() -- owner or event-linked
        # team member may revoke a check-in too.
        event = get_object_or_404(_event_staff_queryset(self.request.user), uuid=self.kwargs["uuid"])
        return get_object_or_404(EventCheckin, id=self.kwargs["checkin_id"], event=event)
