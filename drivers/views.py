from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin, CrudAuthMixin
from .models import Driver

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Driver
    template_name = "crud/list.html"

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Driver
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Driver
    template_name = "crud/form.html"
    fields = "__all__"
    action = "Create"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Driver
    template_name = "crud/form.html"
    fields = "__all__"
    action = "Edit"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Driver
    template_name = "crud/confirm_delete.html"
    success_url = "/drivers/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
