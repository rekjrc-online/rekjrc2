from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.models import User
from crud.views import CrudContextMixin, CrudAuthMixin
from .models import Club, ClubLocation, ClubMember, ClubTeam
from .forms import ClubLocationForm

class Advanced_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Club
    template_name = "clubs/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Club
    template_name = "crud/list.html"

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Club
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Club
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Club
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Club
    template_name = "crud/confirm_delete.html"
    success_url = "/clubs/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class ClubLocationAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = ClubLocation
    form_class = ClubLocationForm
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Club Location"

    def get_club(self):
        return get_object_or_404(Club, uuid=self.kwargs["uuid"], owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["club"] = self.get_club()
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        club = self.get_club()

        # Locations owned by the user
        from locations.models import Location
        from django.db.models import Q
        user_location_ids = Location.objects.filter(
            owner=self.request.user
        ).values_list("id", flat=True)

        # Locations owned by members of any team attached to this club
        team_member_location_ids = Location.objects.filter(
            owner__team_memberships__team__teams__club=club
        ).values_list("id", flat=True)

        # Locations owned by club members directly
        member_location_ids = Location.objects.filter(
            owner__club_memberships__club=club
        ).values_list("id", flat=True)

        # Exclude locations already attached to this club
        already_added = club.locations.values_list("location_id", flat=True)

        allowed = Location.objects.filter(
            Q(id__in=user_location_ids) |
            Q(id__in=team_member_location_ids) |
            Q(id__in=member_location_ids)
        ).exclude(id__in=already_added).distinct()

        form.fields["location"].queryset = allowed
        return form

    def form_valid(self, form):
        form.instance.club = self.get_club()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubLocationRemove(CrudAuthMixin, CrudContextMixin, View):
    def get(self, request, uuid, club_location_id):
        club = get_object_or_404(Club, uuid=uuid, owner=self.request.user)
        cl = get_object_or_404(
            ClubLocation,
            id=club_location_id,
            club__uuid=uuid)
        cl.delete()
        return redirect("clubs:advanced", uuid=uuid)

class ClubMemberAdd(CrudAuthMixin, CreateView):
    model = ClubMember
    fields = [ ]
    template_name = "clubs/add_member.html"

    def form_valid(self, form):
        club = get_object_or_404(Club, uuid=self.kwargs["uuid"], owner=self.request.user)
        user_uuid = self.request.POST.get("profile_uuid")
        user = get_object_or_404(User, uuid=user_uuid)
        if ClubMember.objects.filter(club=club,user=user).exists():
            return redirect(self.get_success_url())
        form.instance.user = user
        form.instance.club = club
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubMemberRemove(CrudAuthMixin, CrudContextMixin, View):
    def get(self, request, uuid, club_member_id):
        club = get_object_or_404(Club, uuid=uuid, owner=request.user)
        member = get_object_or_404(
            ClubMember,
            id=club_member_id,
            club__uuid=uuid)
        member.delete()
        return redirect("clubs:advanced", uuid=uuid)

class ClubTeamAdd(CrudAuthMixin, CrudContextMixin, CreateView):
    model = ClubTeam
    fields = ["team"]
    template_name = "crud/form.html"
    def form_valid(self, form):
        club = get_object_or_404(Club, uuid=self.kwargs["uuid"], owner=self.request.user)
        form.instance.club = club
        return super().form_valid(form)
    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubTeamRemove(CrudAuthMixin, CrudContextMixin, View):
    def get(self, request, uuid, club_team_id):
        club = get_object_or_404(Club, uuid=uuid, owner=request.user)
        ct = get_object_or_404(
            ClubTeam,
            id=club_team_id,
            club__uuid=uuid)
        ct.delete()
        return redirect("clubs:advanced", uuid=uuid)