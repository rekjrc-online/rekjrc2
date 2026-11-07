from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from crawler.models import CrawlerRun
from devices.models import Device, DevicePayload, DeviceWhitelist
from judged.models import JudgedScore
from longjump.models import LongJumpRun
from posts.models import Post
from stopwatch.models import StopwatchRun
from teams.models import Team, TeamMember
from topspeed.models import TopSpeedRun
from . import device_results
from .models import RaceJudgeDevice
from .testing_factories import make_entry, make_race, make_user

ON = dict(DEVICE_RESULTS_ENABLED=True, DEVICE_RESULTS_SINCE="2000-01-01T00:00:00Z")


@override_settings(**ON)
class DeviceResultsTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.device = Device.objects.create(mac="AA:BB:CC:DD:EE:01", name="Radar 1", claimed_by=self.owner)
        self.race = make_race(self.owner, "Top Speed")
        self.rd = make_entry(self.race, "A")

    def send(self, value, name="topspeed", rd=None, device=None):
        rd = self.rd if rd is None else rd
        return DevicePayload.objects.create(
            device=device or self.device, name=name, value=value,
            racedriver_id=rd.id if rd else None)

    def run_processor(self):
        return device_results.process_pending()

    def assertOutcome(self, payload, error_contains=None):
        payload.refresh_from_db()
        self.assertTrue(payload.processed)
        self.assertIsNotNone(payload.processed_at)
        if error_contains is None:
            self.assertEqual(payload.error, "")
        else:
            self.assertIn(error_contains, payload.error)

    # ── switches ──────────────────────────────────────────────

    @override_settings(DEVICE_RESULTS_ENABLED=False)
    def test_disabled_does_nothing(self):
        p = self.send("45.20")
        self.run_processor()
        p.refresh_from_db()
        self.assertFalse(p.processed)

    @override_settings(DEVICE_RESULTS_SINCE="")
    def test_no_cutoff_does_nothing(self):
        p = self.send("45.20")
        self.run_processor()
        p.refresh_from_db()
        self.assertFalse(p.processed)

    @override_settings(DEVICE_RESULTS_SINCE="2026-01-01T00:00:00Z")
    def test_payloads_before_cutoff_are_left_alone(self):
        p = self.send("45.20")
        DevicePayload.objects.filter(pk=p.pk).update(created_at=timezone.make_aware(timezone.datetime(2025, 6, 1)))
        self.run_processor()
        p.refresh_from_db()
        self.assertFalse(p.processed)
        self.assertFalse(TopSpeedRun.objects.exists())

    def test_other_tags_are_left_alone(self):
        rfid = self.send("04A1B2C3", name="rfidscan", rd=False)
        drag = self.send("12.345", name="drag")
        self.run_processor()
        for p in (rfid, drag):
            p.refresh_from_db()
            self.assertFalse(p.processed)
            self.assertEqual(p.error, "")

    # ── recording ─────────────────────────────────────────────

    def test_topspeed_recorded_and_posted_via_device(self):
        p = self.send("45.20")
        self.assertEqual(self.run_processor()["recorded"], 1)
        self.assertOutcome(p)
        self.assertEqual(TopSpeedRun.objects.get().topspeed, Decimal("45.20"))
        self.assertIn("📡 via Radar 1", Post.objects.filter(author_object_id=self.race.id).latest('id').content)

    def test_topspeed_kph_suffix_is_converted(self):
        self.send("72.42k")
        self.run_processor()
        self.assertEqual(TopSpeedRun.objects.get().topspeed, Decimal("45.00"))

    def test_every_result_becomes_its_own_run(self):
        self.send("40")
        self.send("41")
        self.run_processor()
        self.assertEqual(TopSpeedRun.objects.count(), 2)

    def test_rally_stopwatch_longjump_crawler(self):
        cases = [
            ("Rally", "rally", "12.34", lambda: StopwatchRun.objects.get().elapsed_time == 12.34),
            ("Stopwatch Race", "stopwatch", "9.5", lambda: StopwatchRun.objects.filter(elapsed_time=9.5).exists()),
            ("Long Jump", "longjump", "12 7", lambda: LongJumpRun.objects.filter(feet=12, inches=7).exists()),
            ("Crawler Comp", "crawler", "83.20|4",
             lambda: CrawlerRun.objects.filter(elapsed_time=83.2, penalty_points=4).exists()),
        ]
        for race_type, tag, value, check in cases:
            with self.subTest(tag=tag):
                rd = make_entry(make_race(self.owner, race_type), f"{tag}-driver")
                p = self.send(value, name=tag, rd=rd)
                self.run_processor()
                self.assertOutcome(p)
                self.assertTrue(check())

    def test_judged_score_goes_to_the_assigned_judge(self):
        judge = make_user()
        team = Team.objects.create(display_name="Judges", owner=self.owner)
        TeamMember.objects.create(team=team, user=judge)
        race = make_race(self.owner, "Judged Event", judge_team=team)
        rd = make_entry(race, "J")
        RaceJudgeDevice.objects.create(race=race, judge=judge, device=self.device)
        p1 = self.send("8.5", name="judged", rd=rd)
        self.run_processor()
        self.assertOutcome(p1)
        score = JudgedScore.objects.get()
        self.assertEqual((score.judge, score.score, score.run_number), (judge, 8.5, 1))
        self.send("9.0", name="judged", rd=rd)            # a re-run: next run
        self.run_processor()
        self.assertEqual(JudgedScore.objects.latest('id').run_number, 2)

    # ── rejections ────────────────────────────────────────────

    def test_untrusted_device_rejected_whitelisted_accepted(self):
        stranger = Device.objects.create(mac="AA:BB:CC:DD:EE:99", name="Unknown")
        p = self.send("45", device=stranger)
        self.run_processor()
        self.assertOutcome(p, "not claimed or whitelisted")
        DeviceWhitelist.objects.create(mac=stranger.mac)
        p2 = self.send("46", device=stranger)
        self.run_processor()
        self.assertOutcome(p2)

    def test_rejections(self):
        stopwatch_rd = make_entry(make_race(self.owner, "Stopwatch Race"), "S")
        finished = make_race(self.owner, "Top Speed", race_finished=True)
        cases = [
            (dict(value="45", rd=False), "no driver selected"),
            (dict(value="45", rd=stopwatch_rd), "sent to a Stopwatch Race race"),
            (dict(value="45", rd=make_entry(finished, "F")), "already finished"),
            (dict(value="fast"), "unreadable speed"),
            (dict(value="0"), "out of range"),
            (dict(value="12", name="longjump", rd=make_entry(make_race(self.owner, "Long Jump"), "L")),
             "expected '<feet> <inches>'"),
            (dict(value="8", name="judged", rd=make_entry(make_race(self.owner, "Judged Event"), "J")),
             "not assigned to a judge"),
        ]
        for kwargs, error in cases:
            with self.subTest(error=error):
                p = self.send(**kwargs)
                self.run_processor()
                self.assertOutcome(p, error)

    def test_missing_race_entry_rejected(self):
        p = DevicePayload.objects.create(device=self.device, name="topspeed", value="45", racedriver_id=999999)
        self.run_processor()
        self.assertOutcome(p, "does not exist")

    def test_identical_redelivery_within_window_is_a_duplicate(self):
        first = self.send("45.20")
        self.run_processor()
        dup = self.send("45.20")
        self.run_processor()
        self.assertOutcome(dup, f"duplicate of payload {first.pk}")
        self.assertEqual(TopSpeedRun.objects.count(), 1)

    def test_identical_result_outside_window_is_a_new_run(self):
        first = self.send("45.20")
        self.run_processor()
        DevicePayload.objects.filter(pk=first.pk).update(created_at=timezone.now() - timedelta(minutes=5))
        later = self.send("45.20")
        self.run_processor()
        self.assertOutcome(later)
        self.assertEqual(TopSpeedRun.objects.count(), 2)

    # ── transient failures ────────────────────────────────────

    def test_transient_failure_retries_then_gives_up(self):
        p = self.send("45")
        with mock.patch.dict(device_results.HANDLERS, {"topspeed": mock.Mock(side_effect=RuntimeError("db blip"))}):
            self.assertEqual(self.run_processor()["retry"], 1)
            p.refresh_from_db()
            self.assertEqual((p.processed, p.retry_count, p.error), (False, 1, "db blip"))
            for _ in range(device_results.MAX_RETRIES - 1):
                self.run_processor()
        self.assertOutcome(p, "gave up after")
        self.assertFalse(TopSpeedRun.objects.exists())

    def test_failed_handler_leaves_no_partial_rows(self):
        def half_then_fail(payload, rd, race):
            TopSpeedRun.objects.create(race=race, racedriver=rd, topspeed=1)
            raise RuntimeError("boom")
        self.send("45")
        with mock.patch.dict(device_results.HANDLERS, {"topspeed": half_then_fail}):
            self.run_processor()
        self.assertFalse(TopSpeedRun.objects.exists())

    def test_parse_speed(self):
        self.assertEqual(device_results.parse_speed_mph("45.2mph"), Decimal("45.2"))
        self.assertEqual(round(device_results.parse_speed_mph("100 kph"), 2), Decimal("62.14"))
