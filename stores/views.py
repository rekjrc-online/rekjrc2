from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from crud.views import CrudContextMixin, CrudAuthMixin, PublicDetailMixin
from .models import Store

# Owner-editable fields for the Create/Edit CRUD forms below. Deliberately
# excludes slug (auto-generated). Stripe setup for a store is handled by
# hand, off-platform (its keys go into rekjrc/.env, not this form) -- see
# Store.can_accept_payments and the 2026-08-07 payment-model note in
# stores/models.py.
STORE_EDITABLE_FIELDS = [
    "display_name",
    "is_active",
    "is_public",
    "location",
    "description",
    "website",
    "email",
    "phone_number",
    "is_storefront_enabled",
    "avatar",
    "allow_followers",
    "enable_chat",
]

class List_(CrudAuthMixin, CrudContextMixin, ListView):
    model = Store
    template_name = "crud/list.html"

class Detail_(PublicDetailMixin, CrudContextMixin, DetailView):
    model = Store
    template_name = "crud/detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Create_(CrudAuthMixin, CrudContextMixin, CreateView):
    model = Store
    fields = STORE_EDITABLE_FIELDS
    action = "Create"
    template_name = "crud/form.html"

class Update_(CrudAuthMixin, CrudContextMixin, UpdateView):
    model = Store
    fields = STORE_EDITABLE_FIELDS
    action = "Edit"
    template_name = "crud/form.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

class Delete_(CrudAuthMixin, CrudContextMixin, DeleteView):
    model = Store
    template_name = "crud/confirm_delete.html"
    success_url = "/stores/"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"


def storefront_directory(request):
    """Public /shop/ landing page -- every store that's live for online sales."""
    stores = [s for s in Store.objects.filter(is_storefront_enabled=True, is_active=True) if s.can_accept_payments]
    return render(request, "stores/storefront_directory.html", {"stores": stores})
