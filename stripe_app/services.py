"""
Stripe integration: one standalone Stripe account per Store.

`stripe` is imported lazily inside each function (not at module import
time) so the rest of the site still boots even before `pip install -r
requirements.txt` has pulled in the stripe package on a given machine.

Payment model (revised 2026-08-07): no Stripe Connect. Each store's
Stripe account is set up by hand, off-platform -- Jason creates/confirms
the store owner's own standalone Stripe account and drops its three keys
into rekjrc/.env as STRIPE_<store.pk>_SECRET_KEY, STRIPE_<store.pk>_
PUBLIC_KEY, and STRIPE_<store.pk>_WEBHOOK_SECRET. Checkout runs directly
against that store's own account for the full order amount -- there's no
platform account, no application_fee_amount, and no automatic revenue
split. (An earlier version of this file used Stripe Connect destination
charges with a 5% platform fee; that was dropped in favor of manual
per-store key management, see the 2026-08-07 discussion.)
"""
import os

from django.urls import reverse


def get_store_secret_key(store):
    return os.environ.get(f"STRIPE_{store.pk}_SECRET_KEY")


def get_store_webhook_secret(store):
    return os.environ.get(f"STRIPE_{store.pk}_WEBHOOK_SECRET")


def _stripe_for_store(store):
    """Returns the `stripe` module with api_key set to this store's own secret key."""
    import stripe

    secret_key = get_store_secret_key(store)
    if not secret_key:
        raise ValueError(
            f"No Stripe secret key configured for {store} -- "
            f"add STRIPE_{store.pk}_SECRET_KEY to .env first."
        )
    stripe.api_key = secret_key
    return stripe


def create_checkout_session_for_order(order, request):
    """
    Builds a Stripe Checkout Session from an Order's line items, charged
    directly against order.store's own Stripe account for the full order
    amount. Caller is responsible for saving session.id onto the order.
    """
    store = order.store
    if not store or not store.can_accept_payments:
        raise ValueError(f"Store {store} cannot accept payments yet (no Stripe key in .env).")

    stripe = _stripe_for_store(store)

    line_items = []
    for item in order.items.all():
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(round(item.unit_price * 100)),
                "product_data": {
                    "name": f"{item.product_name} - {item.variant_name}" if item.variant_name else item.product_name,
                },
            },
            "quantity": item.quantity,
        })

    success_url = request.build_absolute_uri(
        reverse("orders:confirmation", kwargs={"store_slug": store.slug, "uuid": order.uuid})
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("cart:detail", kwargs={"store_slug": store.slug}))

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=line_items,
        customer_email=order.email,
        client_reference_id=str(order.uuid),
        metadata={"order_uuid": str(order.uuid), "store_uuid": str(store.uuid)},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session


def mark_order_paid(order, session):
    """
    Applies a completed/paid Stripe Checkout Session to an Order (and logs
    it to StripePaymentLog) idempotently -- safe to call from both the
    webhook and the confirmation-page fallback check.
    """
    from django.utils import timezone
    from stripe_app.models import StripePaymentLog

    if order.status != order.STATUS_PAID:
        order.status = order.STATUS_PAID
        order.stripe_payment_intent = getattr(session, "payment_intent", None) or order.stripe_payment_intent
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "stripe_payment_intent", "paid_at"])

    StripePaymentLog.objects.update_or_create(
        stripe_session_id=session.id,
        defaults={
            "user": order.user,
            "product_slug": f"order:{order.uuid}",
            "stripe_payment_intent": getattr(session, "payment_intent", None),
            "amount_total": getattr(session, "amount_total", None),
            "currency": getattr(session, "currency", "usd") or "usd",
            "status": "paid",
            "paid_at": order.paid_at,
        },
    )


def sync_order_from_checkout_session(order, session_id):
    """
    Fallback used by the confirmation page: if the webhook hasn't landed
    yet, ask Stripe directly (via this order's store's own key) whether
    this session is paid.
    """
    stripe = _stripe_for_store(order.store)
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        mark_order_paid(order, session)
