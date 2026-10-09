from datetime import timedelta

from celery import shared_task
from django.db.models import Exists, OuterRef
from django.utils import timezone

# Delay before attempt N+1 after attempt N fails; len+1 = max attempts.
RETRY_DELAYS = [30, 120, 600, 1800, 3600, 3 * 3600, 6 * 3600]
DISABLE_AFTER_FAILED_DELIVERIES = 10
LOOKBACK = timedelta(hours=1)
STUCK_AFTER = timedelta(minutes=10)
BATCH = 500


@shared_task
def dispatch_webhooks():
    """
    Beat task. Go inserts DevicePayload rows directly (no Django signal), and
    `processed` is consumed by other pollers, so webhooks track their own state
    in WebhookDelivery: create a row for each recent payload from a
    webhook-enabled device that lacks one, then enqueue delivery. Also
    re-enqueues deliveries stuck pending (e.g. worker died mid-retry).
    """
    from .models import DevicePayload, WebhookDelivery

    now = timezone.now()
    existing = WebhookDelivery.objects.filter(
        payload=OuterRef('pk'), endpoint=OuterRef('device__webhook_endpoint'))
    new_payloads = (
        DevicePayload.objects
        .filter(created_at__gte=now - LOOKBACK,
                device__webhook_enabled=True,
                device__webhook_endpoint__isnull=False,
                device__webhook_endpoint__is_active=True)
        .annotate(already=Exists(existing))
        .filter(already=False)
        .select_related('device')
        .order_by('id')[:BATCH]
    )
    for p in new_payloads:
        delivery, created = WebhookDelivery.objects.get_or_create(
            payload=p, endpoint_id=p.device.webhook_endpoint_id)
        if created:
            deliver_webhook.delay(delivery.id)

    stuck = WebhookDelivery.objects.filter(
        status=WebhookDelivery.PENDING,
        next_attempt_at__lt=now - STUCK_AFTER,
    ).values_list('id', flat=True)[:BATCH]
    for delivery_id in stuck:
        deliver_webhook.delay(delivery_id)


@shared_task
def deliver_webhook(delivery_id):
    from .models import WebhookDelivery
    from . import webhooks

    try:
        d = (WebhookDelivery.objects
             .select_related('endpoint', 'payload__device')
             .get(pk=delivery_id))
    except WebhookDelivery.DoesNotExist:
        return
    if d.status != WebhookDelivery.PENDING:
        return

    ep, device = d.endpoint, d.payload.device
    now = timezone.now()
    if not (ep.is_active and device.webhook_enabled
            and device.webhook_endpoint_id == ep.id):
        d.status = WebhookDelivery.SKIPPED
        d.error = "Endpoint inactive or device no longer enabled"
        d.save(update_fields=['status', 'error'])
        return

    d.attempts += 1
    try:
        d.status_code = webhooks.post(ep, d.payload)
    except webhooks.WebhookError as e:
        d.status_code = getattr(e, 'status_code', None)
        d.error = str(e)[:500]
        if d.attempts > len(RETRY_DELAYS):
            d.status = WebhookDelivery.FAILED
            d.save(update_fields=['attempts', 'status', 'status_code', 'error'])
            _record_final_failure(ep, now)
            return
        delay = RETRY_DELAYS[d.attempts - 1]
        d.next_attempt_at = now + timedelta(seconds=delay)
        d.save(update_fields=['attempts', 'status_code', 'error', 'next_attempt_at'])
        deliver_webhook.apply_async((d.id,), countdown=delay)
        return

    d.status = WebhookDelivery.SUCCESS
    d.error = ''
    d.delivered_at = now
    d.save(update_fields=['attempts', 'status', 'status_code', 'error', 'delivered_at'])
    type(ep).objects.filter(pk=ep.pk).update(
        consecutive_failures=0, last_success_at=now)


def _record_final_failure(ep, now):
    from django.db.models import F
    type(ep).objects.filter(pk=ep.pk).update(
        consecutive_failures=F('consecutive_failures') + 1, last_failure_at=now)
    ep.refresh_from_db(fields=['consecutive_failures'])
    if ep.consecutive_failures >= DISABLE_AFTER_FAILED_DELIVERIES:
        type(ep).objects.filter(pk=ep.pk, is_active=True).update(
            is_active=False,
            disabled_reason=f"Auto-disabled after {ep.consecutive_failures} "
                            f"consecutive failed deliveries")


@shared_task
def prune_webhook_deliveries(days=30):
    from .models import WebhookDelivery
    WebhookDelivery.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=days)
    ).exclude(status=WebhookDelivery.PENDING).delete()
