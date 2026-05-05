from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin, CrudAuthMixin
from .forms import DeviceForm
from .models import Device


def _user_devices(user):
    """Devices owned by the user directly, or by a team they belong to."""
    return Device.objects.filter(
        Q(owner_user=user) |
        Q(owner_team__members__user=user)
    ).distinct()


class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Device
    template_name = "crud/list.html"

    def get_queryset(self):
        return _user_devices(self.request.user).order_by("name")


class Detail_(CrudAuthMixin, CrudContextMixin, DetailView):
    model = Device
    template_name = "crud/detail.html"
    slug_field = "mac"
    slug_url_kwarg = "mac"

    def get_queryset(self):
        return _user_devices(self.request.user)


class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Device
    form_class = DeviceForm
    action = "Create"
    template_name = "crud/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner_user = self.request.user
        return super().form_valid(form)


class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Device
    form_class = DeviceForm
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "mac"
    slug_url_kwarg = "mac"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return _user_devices(self.request.user)


class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Device
    template_name = "crud/confirm_delete.html"
    success_url = "/devices/"
    slug_field = "mac"
    slug_url_kwarg = "mac"

    def get_queryset(self):
        # Only the direct owner can delete
        return Device.objects.filter(owner_user=self.request.user)
