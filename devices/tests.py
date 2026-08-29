from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient

from teams.models import Team

from .models import Device, DevicePayload, DeviceWhitelist

User = get_user_model()


class DeviceModelTests(TestCase):

    def test_device_str(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:FF", name="Sensor 1")
        self.assertEqual(str(device), "Sensor 1 (AA:BB:CC:DD:EE:FF)")

    def test_device_unique_mac(self):
        Device.objects.create(mac="AA:BB:CC:DD:EE:FF", name="First")
        with self.assertRaises(Exception):
            Device.objects.create(mac="AA:BB:CC:DD:EE:FF", name="Duplicate")

    def test_device_payload_str(self):
        device = Device.objects.create(mac="11:22:33:44:55:66", name="Speed Sensor")
        payload = DevicePayload.objects.create(device=device, value="42.5")
        self.assertIn("Speed Sensor", str(payload))
        self.assertIn("42.5", str(payload))

    def test_device_payload_mark_processed(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:01", name="Test Device")
        payload = DevicePayload.objects.create(device=device, value="10.0")
        self.assertFalse(payload.processed)
        payload.mark_processed()
        payload.refresh_from_db()
        self.assertTrue(payload.processed)
        self.assertIsNotNone(payload.processed_at)

    def test_device_payload_mark_error(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:02", name="Error Device")
        payload = DevicePayload.objects.create(device=device, value="99.9")
        payload.mark_error("timeout")
        payload.refresh_from_db()
        self.assertEqual(payload.error, "timeout")
        self.assertEqual(payload.retry_count, 1)

    def test_mark_error_increments_retry_count_across_calls(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:14", name="Retry Device")
        payload = DevicePayload.objects.create(device=device, value="5.0")
        payload.mark_error("timeout")
        payload.mark_error("timeout again")
        payload.refresh_from_db()
        self.assertEqual(payload.retry_count, 2)
        self.assertEqual(payload.error, "timeout again")

    def test_is_unlinked_true_and_owner_display_empty_when_no_owner(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:10", name="Fresh Device")
        self.assertTrue(device.is_unlinked)
        self.assertIsNone(device.owner_type)
        self.assertEqual(device.owner_display, '')

    def test_is_unlinked_false_and_owner_display_uses_display_name_for_team_owner(self):
        owner_user = User.objects.create_user(email="teamowner@example.com", password="testpass123")
        team = Team.objects.create(owner=owner_user, display_name="Speed Demons")
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:11", name="Team Device")
        device.content_type = ContentType.objects.get_for_model(Team)
        device.object_id = team.id
        device.save()
        self.assertFalse(device.is_unlinked)
        self.assertEqual(device.owner_type, "team")
        self.assertEqual(device.owner_display, "Speed Demons")

    def test_owner_display_falls_back_to_email_for_user_owner(self):
        # User has no display_name attribute and get_full_name() is empty
        # (no first/last name set) -- owner_display should fall through to
        # email rather than raising or returning an empty string.
        person = User.objects.create_user(email="soloracer@example.com", password="testpass123")
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:12", name="Personal Device")
        device.content_type = ContentType.objects.get_for_model(User)
        device.object_id = person.id
        device.save()
        self.assertEqual(device.owner_display, "soloracer@example.com")

    def test_device_whitelist_normalizes_mac_on_save(self):
        entry = DeviceWhitelist.objects.create(mac="  aa:bb:cc:dd:ee:13 ")
        self.assertEqual(entry.mac, "AA:BB:CC:DD:EE:13")


class DevicePayloadIngestAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_ingest_creates_payload_and_device(self):
        response = self.client.post("/api/devices/ingest/", {
            "node": "AA:BB:CC:DD:EE:FF",
            "value": "75.51",
            "name": "Test Driver",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data)
        self.assertTrue(Device.objects.filter(mac="AA:BB:CC:DD:EE:FF").exists())
        self.assertEqual(DevicePayload.objects.count(), 1)

    def test_ingest_reuses_existing_device(self):
        Device.objects.create(mac="AA:BB:CC:DD:EE:FF", name="Existing")
        self.client.post("/api/devices/ingest/", {
            "node": "AA:BB:CC:DD:EE:FF",
            "value": "10.0",
        }, format="json")
        self.assertEqual(Device.objects.count(), 1)

    def test_ingest_missing_fields_returns_400(self):
        response = self.client.post("/api/devices/ingest/", {"node": "AA:BB:CC:DD:EE:FF"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_payload_list_filter_by_processed(self):
        device = Device.objects.create(mac="AA:BB:CC:DD:EE:03", name="Filter Device")
        p1 = DevicePayload.objects.create(device=device, value="1.0")
        p2 = DevicePayload.objects.create(device=device, value="2.0")
        p1.mark_processed()

        response = self.client.get("/api/devices/payloads/?processed=false")
        self.assertEqual(response.status_code, 200)
        ids = [item["id"] for item in response.data]
        self.assertIn(p2.id, ids)
        self.assertNotIn(p1.id, ids)

    def test_payload_list_filter_by_device_mac(self):
        d1 = Device.objects.create(mac="AA:BB:CC:DD:EE:04", name="Device A")
        d2 = Device.objects.create(mac="AA:BB:CC:DD:EE:05", name="Device B")
        DevicePayload.objects.create(device=d1, value="1.0")
        DevicePayload.objects.create(device=d2, value="2.0")

        response = self.client.get("/api/devices/payloads/?device=AA:BB:CC:DD:EE:04")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["device_mac"], "AA:BB:CC:DD:EE:04")
