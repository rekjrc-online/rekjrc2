from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.models import UserProfile
from crud.views import CrudContextMixin
from .models import Club, ClubLocation, ClubMember, ClubTeam

class Advanced_(CrudContextMixin, DetailView):
    model = Club
    template_name = "clubs/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class List_(CrudContextMixin, ListView):
    model = Club
    template_name = "crud/list.html"
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

class Detail_(CrudContextMixin, DetailView):
    model = Club
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudContextMixin, CreateView):
    model = Club
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Club
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Club
    template_name = "crud/confirm_delete.html"
    success_url = "/clubs/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class ClubLocationAdd(CrudContextMixin, CreateView):
    model = ClubLocation
    fields = ["location"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Club Location"
    def form_valid(self, form):
        club = get_object_or_404(Club, uuid=self.kwargs["uuid"])
        form.instance.club = club
        return super().form_valid(form)
    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubLocationRemove(CrudContextMixin, View):
    def get(self, request, uuid, club_location_id):
        cl = get_object_or_404(
            ClubLocation,
            id=club_location_id,
            club__uuid=uuid)
        cl.delete()
        return redirect("clubs:advanced", uuid=uuid)

class ClubMemberAdd(CreateView):
    model = ClubMember
    fields = [ ]
    template_name = "clubs/add_member.html"

    def form_valid(self, form):
        club = get_object_or_404(Club, uuid=self.kwargs["uuid"])
        profile_uuid = self.request.POST.get("profile_uuid")
        profile = get_object_or_404(UserProfile, uuid=profile_uuid)
        if ClubMember.objects.filter(club=club,user=profile.user).exists():
            return redirect(self.get_success_url())
        form.instance.user = profile.user
        form.instance.club = club
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubMemberRemove(CrudContextMixin, View):
    def get(self, request, uuid, club_member_id):
        member = get_object_or_404(
            ClubMember,
            id=club_member_id,
            club__uuid=uuid)
        member.delete()
        return redirect("clubs:advanced", uuid=uuid)

class ClubTeamAdd(CrudContextMixin, CreateView):
    model = ClubTeam
    fields = ["team"]
    template_name = "crud/form.html"
    def form_valid(self, form):
        club = get_object_or_404(Club, uuid=self.kwargs["uuid"])
        form.instance.club = club
        return super().form_valid(form)
    def get_success_url(self):
        return reverse("clubs:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class ClubTeamRemove(CrudContextMixin, View):
    def get(self, request, uuid, club_team_id):
        ct = get_object_or_404(
            ClubTeam,
            id=club_team_id,
            club__uuid=uuid)
        ct.delete()
        return redirect("clubs:advanced", uuid=uuid)
