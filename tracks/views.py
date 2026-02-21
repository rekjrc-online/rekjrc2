from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin, CrudAuthMixin
from .models import Track

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Track
    template_name = "crud/list.html"

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Track
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Track
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Track
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Track
    template_name = "crud/confirm_delete.html"
    success_url = "/tracks/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
