from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient

from clubs.models import Club
from locations.models import Location
from teams.models import Team

from .forms import DeviceClaimForm, get_owner_choices, resolve_owner_choice
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


class DeviceOwnerChoiceTests(TestCase):
    """
    devices.forms.get_owner_choices / resolve_owner_choice -- the
    permission logic behind DeviceClaimForm's "assign to" field. A user may
    only assign a device to themselves, or to a Team/Club/Location they own
    or belong to.
    """
    def setUp(self):
        self.user = User.objects.create_user(email="scanner@example.com", password="testpass123")

    def test_get_owner_choices_includes_self_and_owned_entities(self):
        team = Team.objects.create(owner=self.user, display_name="My Team")
        club = Club.objects.create(owner=self.user, display_name="My Club")
        location = Location.objects.create(owner=self.user, display_name="My Shop")
        choices = dict(get_owner_choices(self.user))
        self.assertIn('user', choices)
        self.assertIn(f'team-{team.id}', choices)
        self.assertIn(f'club-{club.id}', choices)
        self.assertIn(f'location-{location.id}', choices)

    def test_get_owner_choices_excludes_entities_user_does_not_own(self):
        other_user = User.objects.create_user(email="someoneelse@example.com", password="testpass123")
        other_team = Team.objects.create(owner=other_user, display_name="Not Mine")
        choices = dict(get_owner_choices(self.user))
        self.assertNotIn(f'team-{other_team.id}', choices)

    def test_resolve_owner_choice_self(self):
        ct, oid = resolve_owner_choice(self.user, 'user')
        self.assertEqual(ct, ContentType.objects.get_for_model(User))
        self.assertEqual(oid, self.user.id)

    def test_resolve_owner_choice_owned_team(self):
        team = Team.objects.create(owner=self.user, display_name="My Team")
        ct, oid = resolve_owner_choice(self.user, f'team-{team.id}')
        self.assertEqual(ct, ContentType.objects.get_for_model(Team))
        self.assertEqual(oid, team.id)

    def test_resolve_owner_choice_rejects_team_user_does_not_own(self):
        other_user = User.objects.create_user(email="otherowner2@example.com", password="testpass123")
        other_team = Team.objects.create(owner=other_user, display_name="Not Mine")
        with self.assertRaises(forms.ValidationError):
            resolve_owner_choice(self.user, f'team-{other_team.id}')

    def test_resolve_owner_choice_rejects_unknown_kind(self):
        with self.assertRaises(forms.ValidationError):
            resolve_owner_choice(self.user, 'spaceship-1')


class DeviceClaimFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="claimer@example.com", password="testpass123")
        self.device = Device.objects.create(mac="AA:BB:CC:DD:EE:20", name="Unlinked Device")

    def test_valid_claim_to_self(self):
        form = DeviceClaimForm(data={"device": self.device.pk, "owner": "user"}, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['owner_object_id'], self.user.id)

    def test_claiming_entity_not_owned_is_rejected(self):
        other_user = User.objects.create_user(email="otherclaimer@example.com", password="testpass123")
        other_team = Team.objects.create(owner=other_user, display_name="Not Mine")
        form = DeviceClaimForm(
            data={"device": self.device.pk, "owner": f"team-{other_team.id}"}, user=self.user)
        self.assertFalse(form.is_valid())

    def test_already_claimed_device_not_offered_in_queryset(self):
        # DeviceClaimForm's device field queryset is filtered to
        # content_type__isnull=True -- an already-claimed device shouldn't
        # validate as a choice, even if its pk is submitted directly.
        self.device.content_type = ContentType.objects.get_for_model(User)
        self.device.object_id = self.user.id
        self.device.save()
        form = DeviceClaimForm(data={"device": self.device.pk, "owner": "user"}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("device", form.errors)


class DeviceScanViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="scanview@example.com", password="testpass123")
        self.device = Device.objects.create(mac="AA:BB:CC:DD:EE:21", name="Scannable Device")

    def test_claim_device_for_self_via_scan_view(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/devices/scan/", {"device": self.device.pk, "owner": "user"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.device.refresh_from_db()
        self.assertEqual(self.device.claimed_by, self.user)
        self.assertEqual(self.device.owner_type, "user")
        self.assertFalse(self.device.is_unlinked)
