from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin
from .models import Event, EventLocation, EventTeam, EventClub, EventStore, EventRace
from django.shortcuts import get_object_or_404, redirect

class List_(CrudContextMixin, ListView):
    model = Event
    template_name = "crud/list.html"
    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

class Detail_(CrudContextMixin, DetailView):
    model = Event
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudContextMixin, CreateView):
    model = Event
    fields = "__all__"
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudContextMixin, UpdateView):
    model = Event
    fields = "__all__"
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudContextMixin, DeleteView):
    model = Event
    template_name = "crud/confirm_delete.html"
    success_url = "/events/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Advanced_(CrudContextMixin, DetailView):
    model = Event
    template_name = "events/advanced.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class EventClubAdd(CrudContextMixin, CreateView):
    model = EventClub
    fields = ["club"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Club"

    def form_valid(self, form):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventClubRemove(CrudContextMixin, DeleteView):
    model = EventClub
    template_name = "crud/confirm_delete.html"
    model_name = "Event Club"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        return get_object_or_404(EventClub, id=self.kwargs["id"], event=event)

class EventLocationAdd(CrudContextMixin, CreateView):
    model = EventLocation
    fields = ["location"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Location"

    def form_valid(self, form):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventLocationRemove(CrudContextMixin, DeleteView):
    model = EventLocation
    template_name = "crud/confirm_delete.html"
    model_name = "Event Location"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        return get_object_or_404(EventLocation, id=self.kwargs["id"], event=event)

class EventRaceAdd(CrudContextMixin, CreateView):
    model = EventRace
    fields = ["race"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Race"

    def form_valid(self, form):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventRaceRemove(CrudContextMixin, DeleteView):
    model = EventRace
    template_name = "crud/confirm_delete.html"
    model_name = "Event Race"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        return get_object_or_404(EventRace, id=self.kwargs["id"], event=event)

class EventStoreAdd(CrudContextMixin, CreateView):
    model = EventStore
    fields = ["store"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Store"

    def form_valid(self, form):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventStoreRemove(CrudContextMixin, DeleteView):
    model = EventStore
    template_name = "crud/confirm_delete.html"
    model_name = "Event Store"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        return get_object_or_404(EventStore, id=self.kwargs["id"], event=event)

class EventTeamAdd(CrudContextMixin, CreateView):
    model = EventTeam
    fields = ["team"]
    template_name = "crud/form.html"
    action = "Add"
    model_name = "Event Team"

    def form_valid(self, form):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        form.instance.event = event
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

class EventTeamRemove(CrudContextMixin, DeleteView):
    model = EventTeam
    template_name = "crud/confirm_delete.html"
    model_name = "Event Team"

    def get_success_url(self):
        return reverse("events:advanced", kwargs={"uuid": self.kwargs["uuid"]})

    def get_object(self, queryset=None):
        event = get_object_or_404(Event, uuid=self.kwargs["uuid"])
        return get_object_or_404(EventTeam, id=self.kwargs["id"], event=event)
