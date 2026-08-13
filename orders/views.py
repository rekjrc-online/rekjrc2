from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from cart.utils import get_or_create_cart
from stores.models import Store

from .models import Order, OrderItem


def checkout(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    cart = get_or_create_cart(request, store)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart:detail", store_slug)

    if not store.can_accept_payments:
        messages.error(request, f"{store.display_name} isn't able to accept payments yet -- try again later.")
        return redirect("cart:detail", store_slug)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "An email address is required.")
            return render(request, "orders/checkout.html", {"store": store, "cart": cart})

        order = Order.objects.create(
            store=store,
            user=request.user if request.user.is_authenticated else None,
            email=email,
            shipping_name=request.POST.get("shipping_name", "").strip(),
            shipping_address_line1=request.POST.get("shipping_address_line1", "").strip(),
            shipping_address_line2=request.POST.get("shipping_address_line2", "").strip(),
            shipping_city=request.POST.get("shipping_city", "").strip(),
            shipping_state=request.POST.get("shipping_state", "").strip(),
            shipping_postal_code=request.POST.get("shipping_postal_code", "").strip(),
            shipping_country=request.POST.get("shipping_country", "").strip(),
        )

        for cart_item in cart.items.select_related("variant__product"):
            OrderItem.objects.create(
                order=order,
                variant=cart_item.variant,
                product_name=cart_item.variant.product.name,
                variant_name=cart_item.variant.name,
                sku=cart_item.variant.sku,
                unit_price=cart_item.variant.price,
                quantity=cart_item.quantity,
            )

        order.subtotal = sum((i.line_total for i in order.items.all()), Decimal("0.00"))
        order.total = order.subtotal + order.shipping_cost
        order.save(update_fields=["subtotal", "total"])

        # Import here (not at module top) to avoid a hard import-time
        # dependency on stripe_app / the stripe package from every request
        # that merely renders the checkout form.
        from stripe_app.services import create_checkout_session_for_order

        session = create_checkout_session_for_order(order, request)
        order.stripe_checkout_session_id = session.id
        order.save(update_fields=["stripe_checkout_session_id"])

        cart.checked_out = True
        cart.save(update_fields=["checked_out"])

        return redirect(session.url, permanent=False)

    return render(request, "orders/checkout.html", {"store": store, "cart": cart})


def confirmation(request, store_slug, uuid):
    store = get_object_or_404(Store, slug=store_slug)
    order = get_object_or_404(Order, uuid=uuid, store=store)

    # Belt-and-suspenders alongside the webhook: if Stripe redirected the
    # customer back here with a session_id and the webhook hasn't landed
    # yet, check the session directly so the confirmation page doesn't show
    # "pending" for longer than necessary.
    session_id = request.GET.get("session_id")
    if order.status == Order.STATUS_PENDING and session_id and session_id == order.stripe_checkout_session_id:
        from stripe_app.services import sync_order_from_checkout_session
        sync_order_from_checkout_session(order, session_id)
        order.refresh_from_db()

    return render(request, "orders/confirmation.html", {"store": store, "order": order})
