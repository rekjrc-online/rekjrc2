from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView,
)

from crud.views import CrudContextMixin, CrudAuthMixin
from clubs.models import Club
from locations.models import Location
from teams.models import Team

from .forms import DeviceForm, DeviceClaimForm
from .models import Device


def _user_devices(user):
    """
    Devices the user can see/manage:
      - claimed by this user
      - owned by the user themselves (GFK)
      - owned by any Team they own or belong to
      - owned by any Club they own or belong to
      - owned by any Location they own
    """
    user_ct = ContentType.objects.get_for_model(user.__class__)
    team_ct = ContentType.objects.get_for_model(Team)
    club_ct = ContentType.objects.get_for_model(Club)
    loc_ct  = ContentType.objects.get_for_model(Location)

    team_ids = (Team.objects
                .filter(Q(owner=user) | Q(members__user=user))
                .values_list('id', flat=True).distinct())
    club_ids = (Club.objects
                .filter(Q(owner=user) | Q(members__user=user))
                .values_list('id', flat=True).distinct())
    loc_ids  = (Location.objects.filter(owner=user)
                .values_list('id', flat=True))

    return Device.objects.filter(
        Q(claimed_by=user) |
        Q(content_type=user_ct, object_id=user.id) |
        Q(content_type=team_ct, object_id__in=list(team_ids)) |
        Q(content_type=club_ct, object_id__in=list(club_ids)) |
        Q(content_type=loc_ct,  object_id__in=list(loc_ids))
    ).distinct()


class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Device
    template_name = "devices/list.html"

    def get_queryset(self):
        return _user_devices(self.request.user).order_by("name")


class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Device
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        # Any logged-in user may view any device's detail page (this used
        # to be scoped to _user_devices(), which 404'd the page for anyone
        # who didn't claim/own the device -- the same bug as the other
        # Detail_ views). Device isn't an Ownable model, so unlike
        # Race/Team/Club/etc. there's no is_public flag/anonymous-access
        # path here: MAC address and claim info stay behind login for
        # everyone. Update_/Delete_ below still use _user_devices()/
        # claimed_by scoping and are unaffected.
        return Device.objects.all()


class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Device
    form_class = DeviceForm
    action = "Create"
    template_name = "crud/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Default ownership for a manually-created device: the creating user.
        # Re-assignment to a Team/Club/Location happens via Scan_ or a future
        # Reassign flow.
        user = self.request.user
        form.instance.claimed_by   = user
        form.instance.content_type = ContentType.objects.get_for_model(user.__class__)
        form.instance.object_id    = user.id
        return super().form_valid(form)


class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Device
    form_class = DeviceForm
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return _user_devices(self.request.user)


class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Device
    template_name = "crud/confirm_delete.html"
    success_url = "/devices/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        # Only the user who claimed the device may delete it.
        return Device.objects.filter(claimed_by=self.request.user)


class Scan_(CrudAuthMixin, FormView):
    """
    Lists all unlinked devices and lets the current user claim one by
    assigning it to themselves or to a Team / Club / Location they control.

    Note: deliberately does NOT inherit CrudContextMixin — that mixin auto-strips
    any form field named "owner" (its `auto_exclude` list), which would silently
    delete this form's owner dropdown.
    """
    form_class = DeviceClaimForm
    template_name = "devices/scan.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['unlinked_devices'] = (
            Device.objects.filter(content_type__isnull=True).order_by('name')
        )
        return ctx

    def form_valid(self, form):
        device = form.cleaned_data['device']
        # Re-check: another user may have claimed it between page-load and submit.
        device.refresh_from_db()
        if not device.is_unlinked:
            messages.error(
                self.request,
                "That device was just claimed by someone else."
            )
            return redirect('devices:scan')

        device.content_type = form.cleaned_data['owner_content_type']
        device.object_id    = form.cleaned_data['owner_object_id']
        device.claimed_by   = self.request.user
        device.save(update_fields=[
            'content_type', 'object_id', 'claimed_by', 'updated_at',
        ])
        messages.success(
            self.request,
            f'Device "{device.name}" claimed successfully.'
        )
        return redirect('devices:detail', uuid=device.uuid)
