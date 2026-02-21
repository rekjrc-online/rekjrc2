from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.models import User
from crud.views import CrudContextMixin, CrudAuthMixin
from .models import Team, TeamMember

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Team
    template_name = "teams/list.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = Team.objects.filter(owner=self.request.user)
        context['member_teams'] = Team.objects.filter(members__user=self.request.user).exclude(owner=self.request.user)
        return context

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Team
    template_name = "teams/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Team
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Team
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Team
    template_name = "crud/confirm_delete.html"
    success_url = "/teams/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Advanced_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Team
    template_name = "teams/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class TeamMemberAdd(CrudAuthMixin, CreateView):
    model = TeamMember
    fields = []
    template_name = "teams/add_member.html"

    def form_valid(self, form):
        team = get_object_or_404(Team, uuid=self.kwargs["uuid"], owner=self.request.user)
        user_uuid = self.request.POST.get("profile_uuid")
        user = get_object_or_404(User, uuid=user_uuid)
        if TeamMember.objects.filter(team=team, user=user).exists():
            return redirect(self.get_success_url())
        form.instance.user = user
        form.instance.team = team
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("teams:detail", kwargs={"uuid": self.kwargs["uuid"]})

class TeamMemberRemove(CrudAuthMixin, View):
    def get(self, request, uuid, member_id):
        team = get_object_or_404(Team, uuid=uuid, owner=request.user)
        member = get_object_or_404(TeamMember, id=member_id, team=team)
        member.delete()
        return redirect("teams:detail", uuid=uuid)