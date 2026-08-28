from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from stores.models import Store

from .models import Product, ProductImage, ProductVariant


def product_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    products = Product.objects.filter(store=store, is_active=True).prefetch_related("images", "variants")
    return render(request, "products/list.html", {"store": store, "products": products})


def product_detail(request, store_slug, slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    product = get_object_or_404(
        Product.objects.prefetch_related("images", "variants"),
        store=store,
        slug=slug,
        is_active=True,
    )
    return render(request, "products/detail.html", {"store": store, "product": product})


# ----------------------------------------------------------------------
# Owner-facing product management (added 2026-08-20). Scoped to a single
# store the requesting user owns -- store.owner, not a `owner` field on
# Product itself (Product isn't Ownable; see products/models.py docstring).
# Variants and images are managed on their own nested pages below rather
# than inline on the product form, to keep this consistent with the rest
# of the site's one-model-per-page CRUD style.
# ----------------------------------------------------------------------

PRODUCT_EDITABLE_FIELDS = ["name", "description", "base_price", "is_active", "sort_order"]


class ProductManageMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, slug=kwargs["store_slug"])
        if self.store.owner != request.user:
            raise PermissionDenied("You don't manage this store.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Product.objects.filter(store=self.store)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        ctx["action"] = getattr(self, "action", None)
        return ctx

    def get_success_url(self):
        return reverse("products:manage_list", kwargs={"store_slug": self.store.slug})


class ManageList(ProductManageMixin, ListView):
    model = Product
    template_name = "products/manage_list.html"
    context_object_name = "products"

    def get_queryset(self):
        # manage_list.html lists each product's variants (price/override)
        # inline, so prefetch them here to avoid an N+1 query per product.
        return super().get_queryset().prefetch_related("variants")


class ManageCreate(ProductManageMixin, CreateView):
    model = Product
    fields = PRODUCT_EDITABLE_FIELDS
    template_name = "products/manage_form.html"
    action = "Add"

    def form_valid(self, form):
        form.instance.store = self.store
        return super().form_valid(form)


class ManageUpdate(ProductManageMixin, UpdateView):
    model = Product
    fields = PRODUCT_EDITABLE_FIELDS
    template_name = "products/manage_form.html"
    action = "Edit"


class ManageDelete(ProductManageMixin, DeleteView):
    model = Product
    template_name = "products/manage_confirm_delete.html"


# ----------------------------------------------------------------------
# Variant management, nested under a specific product. ProductVariant has
# no `store` field of its own -- ownership is checked via the product's
# store, same as ProductManageMixin above, so this mixin duplicates that
# check rather than trying to reuse it (the URL also carries the product's
# slug, which ProductManageMixin doesn't expect).
# ----------------------------------------------------------------------

class ProductChildManageMixin(LoginRequiredMixin):
    login_url = "/accounts/login/"
    redirect_field_name = "next"

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, slug=kwargs["store_slug"])
        if self.store.owner != request.user:
            raise PermissionDenied("You don't manage this store.")
        self.product = get_object_or_404(Product, store=self.store, slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        ctx["product"] = self.product
        ctx["action"] = getattr(self, "action", None)
        return ctx


class VariantManageMixin(ProductChildManageMixin):
    def get_queryset(self):
        return self.product.variants.all()

    def get_success_url(self):
        return reverse("products:manage_variants", kwargs={"store_slug": self.store.slug, "slug": self.product.slug})


VARIANT_EDITABLE_FIELDS = ["name", "sku", "price_override", "is_active", "sort_order"]


class ManageVariantList(VariantManageMixin, ListView):
    model = ProductVariant
    template_name = "products/manage_variant_list.html"
    context_object_name = "variants"


class ManageVariantCreate(VariantManageMixin, CreateView):
    model = ProductVariant
    fields = VARIANT_EDITABLE_FIELDS
    template_name = "products/manage_variant_form.html"
    action = "Add"

    def form_valid(self, form):
        form.instance.product = self.product
        return super().form_valid(form)


class ManageVariantUpdate(VariantManageMixin, UpdateView):
    model = ProductVariant
    fields = VARIANT_EDITABLE_FIELDS
    template_name = "products/manage_variant_form.html"
    action = "Edit"
    slug_field = "uuid"
    slug_url_kwarg = "variant_uuid"


class ManageVariantDelete(VariantManageMixin, DeleteView):
    model = ProductVariant
    template_name = "products/manage_variant_confirm_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "variant_uuid"


# ----------------------------------------------------------------------
# Image management, nested under a specific product. ProductImage.save()/
# delete() already queue a thumbnail refresh (see products/models.py) --
# nothing extra needed here for that to keep working from these views.
# ----------------------------------------------------------------------

class ImageManageMixin(ProductChildManageMixin):
    def get_queryset(self):
        return self.product.images.all()

    def get_success_url(self):
        return reverse("products:manage_images", kwargs={"store_slug": self.store.slug, "slug": self.product.slug})


IMAGE_EDITABLE_FIELDS = ["image", "alt_text", "sort_order"]


class ManageImageList(ImageManageMixin, ListView):
    model = ProductImage
    template_name = "products/manage_image_list.html"
    context_object_name = "images"


class ManageImageCreate(ImageManageMixin, CreateView):
    model = ProductImage
    fields = IMAGE_EDITABLE_FIELDS
    template_name = "products/manage_image_form.html"
    action = "Add"

    def form_valid(self, form):
        form.instance.product = self.product
        return super().form_valid(form)


class ManageImageUpdate(ImageManageMixin, UpdateView):
    model = ProductImage
    fields = IMAGE_EDITABLE_FIELDS
    template_name = "products/manage_image_form.html"
    action = "Edit"
    slug_field = "uuid"
    slug_url_kwarg = "image_uuid"


class ManageImageDelete(ImageManageMixin, DeleteView):
    model = ProductImage
    template_name = "products/manage_image_confirm_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "image_uuid"
