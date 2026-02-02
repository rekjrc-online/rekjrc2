from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin
from .models import Track

class List_(CrudContextMixin, ListView):
    model = Track
    template_name = "crud/list.html"
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

class Detail_(CrudContextMixin, DetailView):
    model = Track
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudContextMixin, CreateView):
    model = Track
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Track
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Track
    template_name = "crud/confirm_delete.html"
    success_url = "/tracks/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
