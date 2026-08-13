from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import ProductVariant
from stores.models import Store

from .models import CartItem
from .utils import get_or_create_cart


def cart_detail(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    cart = get_or_create_cart(request, store)
    return render(request, "cart/cart.html", {"store": store, "cart": cart})


@require_POST
def add_to_cart(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    cart = get_or_create_cart(request, store)
    variant = get_object_or_404(
        ProductVariant, uuid=request.POST.get("variant_uuid"), is_active=True, product__store=store)
    try:
        quantity = max(1, int(request.POST.get("quantity", 1)))
    except (TypeError, ValueError):
        quantity = 1

    item, created = CartItem.objects.get_or_create(
        cart=cart, variant=variant, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity"])

    messages.success(request, f"Added {variant} to your cart.")
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("cart:detail", store_slug)


@require_POST
def update_cart_item(request, store_slug, uuid):
    store = get_object_or_404(Store, slug=store_slug)
    cart = get_or_create_cart(request, store)
    item = get_object_or_404(CartItem, uuid=uuid, cart=cart)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = item.quantity

    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
    return redirect("cart:detail", store_slug)


@require_POST
def remove_cart_item(request, store_slug, uuid):
    store = get_object_or_404(Store, slug=store_slug)
    cart = get_or_create_cart(request, store)
    item = get_object_or_404(CartItem, uuid=uuid, cart=cart)
    item.delete()
    return redirect("cart:detail", store_slug)
