from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin, CrudAuthMixin
from .models import Location, LocationTrack
from .forms import LocationForm

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Location
    template_name = "crud/list.html"

class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Location
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Location
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Location
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Location
    template_name = "crud/confirm_delete.html"
    success_url = "/locations/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Advanced_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Location
    template_name = "locations/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class LocationTrackAdd_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = LocationTrack
    fields = ["track"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Location Track"

    def form_valid(self, form):
        location = get_object_or_404(Location, uuid=self.kwargs["uuid"])
        form.instance.location = location
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("locations:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class LocationTrackRemove_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = LocationTrack
    template_name = "crud/confirm_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        location = super().get_object(queryset)
        return location.location_tracks.get(pk=self.kwargs["pk"])

    def get_success_url(self):
        return reverse("locations:advanced", kwargs={"uuid": self.kwargs["uuid"]})