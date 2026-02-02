from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin
from .models import Team

class List_(CrudContextMixin, ListView):
    model = Team
    template_name = "teams/list.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = Team.objects.filter(owner=self.request.user)
        context['member_teams'] = Team.objects.filter(members__user=self.request.user).exclude(owner=self.request.user)
        return context

class Detail_(CrudContextMixin, DetailView):
    model = Team
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudContextMixin, CreateView):
    model = Team
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Team
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Team
    template_name = "crud/confirm_delete.html"
    success_url = "/teams/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
