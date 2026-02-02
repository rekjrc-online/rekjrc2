from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin
from .models import Driver

class List_(CrudContextMixin, ListView):
    model = Driver
    template_name = "crud/list.html"
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

class Detail_(CrudContextMixin, DetailView):
    model = Driver
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudContextMixin, CreateView):
    model = Driver
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Driver
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Driver
    template_name = "crud/confirm_delete.html"
    success_url = "/drivers/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
