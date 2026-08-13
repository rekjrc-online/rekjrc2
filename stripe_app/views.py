from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from stores.models import Store

from .services import get_store_webhook_secret, mark_order_paid


@csrf_exempt
def stripe_webhook(request, store_pk):
    """
    Each store has its own standalone Stripe account (see stripe_app.
    services), so each needs its own webhook endpoint configured in that
    store's own Stripe dashboard, pointed at this URL, so we know which
    STRIPE_<pk>_WEBHOOK_SECRET to verify the signature against.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    store = get_object_or_404(Store, pk=store_pk)
    webhook_secret = get_store_webhook_secret(store)
    if not webhook_secret:
        return HttpResponseBadRequest(f"No webhook secret configured for store {store_pk}")

    import stripe

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest("Invalid Stripe webhook payload/signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_uuid = session.get("client_reference_id") or session.get("metadata", {}).get("order_uuid")
        if order_uuid:
            try:
                order = Order.objects.get(uuid=order_uuid, store=store)
            except Order.DoesNotExist:
                order = None
            if order is not None and session.get("payment_status") == "paid":
                mark_order_paid(order, session)

    return HttpResponse(status=200)
