import hashlib
import hmac
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from . import tasks, webhooks
from .models import Device, DevicePayload, WebhookDelivery, WebhookEndpoint

User = get_user_model()


class SigningTests(SimpleTestCase):

    def test_sign_matches_reference_hmac(self):
        body = b'{"a":1}'
        expected = hmac.new(b"s3cret", b"1700000000." + body, hashlib.sha256).hexdigest()
        self.assertEqual(webhooks.sign("s3cret", 1700000000, body), expected)

    def test_signature_changes_with_secret_timestamp_and_body(self):
        base = webhooks.sign("k", 100, b"body")
        self.assertNotEqual(base, webhooks.sign("other", 100, b"body"))
        self.assertNotEqual(base, webhooks.sign("k", 101, b"body"))
        self.assertNotEqual(base, webhooks.sign("k", 100, b"body2"))

    def test_sign_is_deterministic(self):
        self.assertEqual(webhooks.sign("k", 5, b"x"), webhooks.sign("k", 5, b"x"))


class PostTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="shop", password="pw")
        self.device = Device.objects.create(mac="AA:BB:CC:DD:EE:01", name="Beam 1")
        self.endpoint = WebhookEndpoint.objects.create(
            account=self.user, url="https://shop.example.com/hook", secret="topsecret")
        self.payload = DevicePayload.objects.create(
            device=self.device, value="12.34", name="speed")

    def _fake_response(self, status=200):
        resp = mock.MagicMock()
        resp.status_code = status
        return resp

    def test_request_carries_verifiable_signature_and_body(self):
        with mock.patch.object(webhooks, "_assert_public_https"), \
             mock.patch.object(webhooks.requests, "post",
                               return_value=self._fake_response()) as post:
            code = webhooks.post(self.endpoint, self.payload)
        self.assertEqual(code, 200)
        kwargs = post.call_args.kwargs
        headers, body = kwargs["headers"], kwargs["data"]
        self.assertFalse(kwargs["allow_redirects"])
        parts = dict(kv.split("=", 1) for kv in headers["X-Rekj-Signature"].split(","))
        self.assertEqual(parts["v1"], webhooks.sign("topsecret", int(parts["t"]), body))
        self.assertEqual(headers["X-Rekj-Event-Id"], str(self.payload.id))
        data = json.loads(body)
        self.assertEqual(data["event_id"], self.payload.id)
        self.assertEqual(data["value"], "12.34")
        self.assertEqual(data["device"]["mac"], "AA:BB:CC:DD:EE:01")

    def test_non_2xx_raises_with_status_code(self):
        with mock.patch.object(webhooks, "_assert_public_https"), \
             mock.patch.object(webhooks.requests, "post",
                               return_value=self._fake_response(500)):
            with self.assertRaises(webhooks.WebhookError) as cm:
                webhooks.post(self.endpoint, self.payload)
        self.assertEqual(cm.exception.status_code, 500)

    def test_rejects_http_url(self):
        with self.assertRaises(webhooks.WebhookError):
            webhooks._assert_public_https("http://shop.example.com/hook")

    def test_rejects_private_and_loopback_resolution(self):
        for ip in ("127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1"):
            fake = [(2, 1, 6, "", (ip, 443))]
            with mock.patch.object(webhooks.socket, "getaddrinfo", return_value=fake):
                with self.assertRaises(webhooks.WebhookError, msg=ip):
                    webhooks._assert_public_https("https://evil.example.com/")

    def test_allows_public_address(self):
        fake = [(2, 1, 6, "", ("93.184.216.34", 443))]
        with mock.patch.object(webhooks.socket, "getaddrinfo", return_value=fake):
            webhooks._assert_public_https("https://ok.example.com/")


class DeliveryRetryTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="shop", password="pw")
        self.endpoint = WebhookEndpoint.objects.create(
            account=self.user, url="https://shop.example.com/hook")
        self.device = Device.objects.create(
            mac="AA:BB:CC:DD:EE:02", name="Beam 2",
            webhook_enabled=True, webhook_endpoint=self.endpoint)
        self.payload = DevicePayload.objects.create(device=self.device, value="1.0")
        self.delivery = WebhookDelivery.objects.create(
            payload=self.payload, endpoint=self.endpoint)

    def _run(self, side_effect=None, return_value=200):
        with mock.patch.object(webhooks, "post", side_effect=side_effect,
                               return_value=return_value) as post, \
             mock.patch.object(tasks.deliver_webhook, "apply_async") as retry:
            tasks.deliver_webhook(self.delivery.id)
        self.delivery.refresh_from_db()
        self.endpoint.refresh_from_db()
        return post, retry

    def test_success_marks_delivered_and_resets_failures(self):
        self.endpoint.consecutive_failures = 4
        self.endpoint.save()
        _, retry = self._run(return_value=200)
        self.assertEqual(self.delivery.status, WebhookDelivery.SUCCESS)
        self.assertEqual(self.delivery.attempts, 1)
        self.assertIsNotNone(self.delivery.delivered_at)
        self.assertEqual(self.endpoint.consecutive_failures, 0)
        self.assertIsNotNone(self.endpoint.last_success_at)
        retry.assert_not_called()

    def test_failure_schedules_retry_with_first_backoff(self):
        err = webhooks.WebhookError("HTTP 503")
        err.status_code = 503
        _, retry = self._run(side_effect=err)
        self.assertEqual(self.delivery.status, WebhookDelivery.PENDING)
        self.assertEqual(self.delivery.attempts, 1)
        self.assertEqual(self.delivery.status_code, 503)
        self.assertEqual(self.delivery.error, "HTTP 503")
        retry.assert_called_once_with((self.delivery.id,), countdown=tasks.RETRY_DELAYS[0])
        self.assertGreater(self.delivery.next_attempt_at, timezone.now())

    def test_backoff_grows_with_each_attempt(self):
        self.delivery.attempts = 2
        self.delivery.save()
        _, retry = self._run(side_effect=webhooks.WebhookError("timeout"))
        self.assertEqual(self.delivery.attempts, 3)
        retry.assert_called_once_with((self.delivery.id,), countdown=tasks.RETRY_DELAYS[2])

    def test_exhausted_retries_mark_failed_and_count_against_endpoint(self):
        self.delivery.attempts = len(tasks.RETRY_DELAYS)
        self.delivery.save()
        _, retry = self._run(side_effect=webhooks.WebhookError("HTTP 500"))
        self.assertEqual(self.delivery.status, WebhookDelivery.FAILED)
        self.assertEqual(self.delivery.attempts, len(tasks.RETRY_DELAYS) + 1)
        self.assertEqual(self.endpoint.consecutive_failures, 1)
        self.assertIsNotNone(self.endpoint.last_failure_at)
        self.assertTrue(self.endpoint.is_active)
        retry.assert_not_called()

    def test_endpoint_auto_disabled_after_threshold(self):
        self.endpoint.consecutive_failures = tasks.DISABLE_AFTER_FAILED_DELIVERIES - 1
        self.endpoint.save()
        self.delivery.attempts = len(tasks.RETRY_DELAYS)
        self.delivery.save()
        self._run(side_effect=webhooks.WebhookError("HTTP 500"))
        self.assertFalse(self.endpoint.is_active)
        self.assertIn("Auto-disabled", self.endpoint.disabled_reason)

    def test_non_pending_delivery_is_not_resent(self):
        self.delivery.status = WebhookDelivery.SUCCESS
        self.delivery.save()
        post, _ = self._run()
        post.assert_not_called()

    def test_inactive_endpoint_skips_delivery(self):
        self.endpoint.is_active = False
        self.endpoint.save()
        post, _ = self._run()
        post.assert_not_called()
        self.assertEqual(self.delivery.status, WebhookDelivery.SKIPPED)

    def test_disabled_device_skips_delivery(self):
        self.device.webhook_enabled = False
        self.device.save()
        post, _ = self._run()
        post.assert_not_called()
        self.assertEqual(self.delivery.status, WebhookDelivery.SKIPPED)


class DispatchTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="shop", password="pw")
        self.endpoint = WebhookEndpoint.objects.create(
            account=self.user, url="https://shop.example.com/hook")

    def _device(self, mac, **kw):
        return Device.objects.create(mac=mac, name=mac, **kw)

    def _dispatch(self):
        with mock.patch.object(tasks.deliver_webhook, "delay") as delay:
            tasks.dispatch_webhooks()
        return delay

    def test_creates_delivery_and_enqueues_for_enabled_device(self):
        d = self._device("AA:00:00:00:00:01", webhook_enabled=True,
                         webhook_endpoint=self.endpoint)
        p = DevicePayload.objects.create(device=d, value="1")
        delay = self._dispatch()
        delivery = WebhookDelivery.objects.get(payload=p, endpoint=self.endpoint)
        delay.assert_called_once_with(delivery.id)

    def test_ignores_disabled_unassigned_and_inactive_endpoint(self):
        off = self._device("AA:00:00:00:00:02", webhook_endpoint=self.endpoint)
        none = self._device("AA:00:00:00:00:03", webhook_enabled=True)
        dead = WebhookEndpoint.objects.create(
            account=self.user, url="https://x.example.com/", is_active=False)
        inactive = self._device("AA:00:00:00:00:04", webhook_enabled=True,
                                webhook_endpoint=dead)
        for d in (off, none, inactive):
            DevicePayload.objects.create(device=d, value="1")
        delay = self._dispatch()
        self.assertEqual(WebhookDelivery.objects.count(), 0)
        delay.assert_not_called()

    def test_second_run_does_not_duplicate(self):
        d = self._device("AA:00:00:00:00:05", webhook_enabled=True,
                         webhook_endpoint=self.endpoint)
        DevicePayload.objects.create(device=d, value="1")
        self._dispatch()
        delay = self._dispatch()
        self.assertEqual(WebhookDelivery.objects.count(), 1)
        delay.assert_not_called()

    def test_old_payloads_outside_lookback_are_ignored(self):
        d = self._device("AA:00:00:00:00:06", webhook_enabled=True,
                         webhook_endpoint=self.endpoint)
        p = DevicePayload.objects.create(device=d, value="1")
        DevicePayload.objects.filter(pk=p.pk).update(
            created_at=timezone.now() - tasks.LOOKBACK - timedelta(minutes=1))
        self._dispatch()
        self.assertEqual(WebhookDelivery.objects.count(), 0)

    def test_stuck_pending_delivery_is_reenqueued(self):
        d = self._device("AA:00:00:00:00:07", webhook_enabled=True,
                         webhook_endpoint=self.endpoint)
        p = DevicePayload.objects.create(device=d, value="1")
        delivery = WebhookDelivery.objects.create(
            payload=p, endpoint=self.endpoint,
            next_attempt_at=timezone.now() - tasks.STUCK_AFTER - timedelta(minutes=1))
        delay = self._dispatch()
        delay.assert_called_once_with(delivery.id)
