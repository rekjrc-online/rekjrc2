"""
Device-payload -> race-result processor.

The Go ingest service (rekjrc_ingest, /ingest/) writes every result a
handheld sends into devices_devicepayload and stops there. This module
turns those rows into the same per-race-type run rows the web forms create,
by calling each race type's services.py -- so a device result is recorded,
posted to the race feed and ranked exactly like one typed in on the web.

Run periodically by races.tasks.process_device_payloads (Celery beat).

Which rows are handled
----------------------
Only rows with processed=False whose `name` is one of HANDLERS' tags, and
created at/after settings.DEVICE_RESULTS_SINCE. Everything else is left
untouched: `rfidscan` belongs to events' check-in poller, `drag` waits for
the bracket handler (not built yet), unknown tags wait for a future handler,
and rows from before the cutoff are never imported into races.

The payload's `name` field carries the firmware's event-type tag
(node_core.h evTypeStr()), NOT a driver name, despite the Go/Django comments
calling it one.

Outcome bookkeeping (existing DevicePayload fields, no migration)
------------------------------------------------------------------
  recorded              processed=True,  error=''
  rejected (permanent)  processed=True,  error=<reason>
  transient failure     processed=False, error=<last error>, retry_count+1;
                        becomes a rejection after MAX_RETRIES attempts
Admin's "Reprocess selected" action resets a row to try again.
"""
import logging
import math
import re
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from devices.models import DevicePayload, DeviceWhitelist
from .models import RaceDriver, RaceJudgeDevice

log = logging.getLogger(__name__)

MAX_RETRIES = 5
BATCH = 200
# Safety net under Go's in-memory packet_id dedup (which has a small
# check-then-insert gap): an identical result from the same device for the
# same entry within this window is treated as a duplicate delivery.
DUPLICATE_WINDOW = timedelta(seconds=60)
KPH_PER_MPH = Decimal("1.609344")


class Rejected(Exception):
    """Permanent problem with a payload -- retrying won't help."""


# ── Tag -> accepted race types ────────────────────────────────────────────
# Mirrors eventRaceTypes in Go/racedrivers.go (the list the device's driver
# roster was served from). KEEP THE TWO IN SYNC. Only tags with a handler
# below are listed; Go's laprace/lapcounter/drag entries have none yet.
TAG_RACE_TYPES = {
    "topspeed":  {"Top Speed"},
    "trapspeed": {"Top Speed"},
    "longjump":  {"Long Jump"},
    "stopwatch": {"Stopwatch Race"},
    "rally":     {"Rally"},
    "judged":    {"Judged Event"},
    "crawler":   {"Crawler Comp"},
}


# ── Value parsers (payload `value` is a free-form string, max 32 chars) ────

_SPEED_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(kph|k|mph)?\s*$", re.IGNORECASE)


def parse_speed_mph(value):
    """
    '45.20' / '45.20mph' -> mph as-is; '72.70k' / '72.70 kph' -> converted
    to mph. Unsuffixed values are mph -- today's firmware sends the bare
    number even in kph mode (to be fixed firmware-side by adding a 'k'
    suffix), so until then a kph-mode device's result will read high.
    """
    m = _SPEED_RE.match(value or "")
    if not m:
        raise Rejected(f"unreadable speed {value!r}")
    speed = Decimal(m.group(1))
    if (m.group(2) or "").lower() in ("k", "kph"):
        speed = speed / KPH_PER_MPH
    return speed


def parse_seconds(value):
    try:
        secs = float((value or "").strip())
    except ValueError:
        raise Rejected(f"unreadable time {value!r}")
    if not math.isfinite(secs) or secs <= 0:
        raise Rejected(f"time must be positive, got {value!r}")
    return secs


# ── Handlers: (payload, racedriver, race) -> None, raise Rejected on bad data

def _topspeed(payload, rd, race):
    from topspeed import services
    mph = services.parse_mph(parse_speed_mph(payload.value))
    if mph is None:
        raise Rejected(f"speed out of range: {payload.value!r}")
    services.record_topspeed(race, rd, mph, device=payload.device)


def _stopwatch(payload, rd, race):
    from stopwatch import services
    services.record_time(race, rd, parse_seconds(payload.value), device=payload.device)


def _longjump(payload, rd, race):
    from longjump import services
    parts = (payload.value or "").split()
    if len(parts) != 2:
        raise Rejected(f"expected '<feet> <inches>', got {payload.value!r}")
    distance = services.parse_distance(*parts)
    if distance is None:
        raise Rejected(f"distance out of range: {payload.value!r}")
    services.record_jump(race, rd, *distance, device=payload.device)


def _crawler(payload, rd, race):
    from crawler import services
    parts = (payload.value or "").split("|")
    if len(parts) != 2:
        raise Rejected(f"expected '<seconds>|<points>', got {payload.value!r}")
    parsed = services.parse_run(*parts)
    if parsed is None:
        raise Rejected(f"unreadable crawler run {payload.value!r}")
    services.record_run(race, rd, *parsed, device=payload.device)


def _judged(payload, rd, race):
    from judged import services
    assignment = (RaceJudgeDevice.objects
                  .filter(race=race, device=payload.device)
                  .select_related('judge').first())
    if assignment is None:
        raise Rejected("device is not assigned to a judge for this race")
    if not services.is_judge(race, assignment.judge):
        raise Rejected(f"{assignment.judge} is no longer on this race's judge team")
    try:
        score = float((payload.value or "").strip())
    except ValueError:
        raise Rejected(f"unreadable score {payload.value!r}")
    if not 0.0 <= score <= 10.0:
        raise Rejected(f"score must be 0-10, got {payload.value!r}")
    services.record_score(race, rd, assignment.judge, score)


HANDLERS = {
    "topspeed":  _topspeed,
    "trapspeed": _topspeed,
    "longjump":  _longjump,
    "stopwatch": _stopwatch,
    "rally":     _stopwatch,   # Rally races use the stopwatch app
    "judged":    _judged,
    "crawler":   _crawler,
}


# ── Processing ────────────────────────────────────────────────────────────

def results_since():
    """settings.DEVICE_RESULTS_SINCE as an aware datetime, or None if unset."""
    raw = getattr(settings, "DEVICE_RESULTS_SINCE", None)
    if not raw:
        return None
    dt = raw if hasattr(raw, "tzinfo") else parse_datetime(str(raw))
    if dt is None:
        raise ValueError(f"DEVICE_RESULTS_SINCE is not a datetime: {raw!r}")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def device_is_trusted(device):
    """Claimed by a user, or pre-approved on the device whitelist."""
    return (device.claimed_by_id is not None
            or DeviceWhitelist.objects.filter(mac=device.mac).exists())


def _resolve(payload):
    """Validate a payload and return (handler, racedriver, race)."""
    tag = (payload.name or "").strip().lower()
    handler = HANDLERS[tag]
    if not device_is_trusted(payload.device):
        raise Rejected("device is not claimed or whitelisted")
    if not payload.racedriver_id:
        raise Rejected("no driver selected on the device")
    rd = (RaceDriver.objects
          .select_related('race', 'driver', 'build', 'race_class')
          .filter(pk=payload.racedriver_id).first())
    if rd is None:
        raise Rejected(f"race entry {payload.racedriver_id} does not exist")
    race = rd.race
    if race.race_type not in TAG_RACE_TYPES[tag]:
        raise Rejected(f"'{tag}' result sent to a {race.race_type} race")
    if race.race_finished:
        raise Rejected("race is already finished")
    return handler, rd, race


def _duplicate_of(payload):
    """An earlier recorded payload this one is a re-delivery of, or None."""
    return (DevicePayload.objects
            .filter(device_id=payload.device_id,
                    racedriver_id=payload.racedriver_id,
                    name=payload.name, value=payload.value,
                    processed=True, error="",
                    created_at__gte=payload.created_at - DUPLICATE_WINDOW,
                    created_at__lte=payload.created_at)
            .exclude(pk=payload.pk)
            .order_by('-id').first())


def _finish(payload, error=""):
    payload.processed = True
    payload.processed_at = timezone.now()
    payload.error = error
    payload.save(update_fields=['processed', 'processed_at', 'error', 'retry_count'])


def process_payload(payload_id):
    """
    Process one payload under a row lock (skip_locked, so overlapping task
    runs never double-process). Returns 'recorded', 'rejected', 'retry',
    or None if the row was already taken/done.
    """
    with transaction.atomic():
        payload = (DevicePayload.objects
                   .select_for_update(skip_locked=True)
                   .select_related('device')
                   .filter(pk=payload_id, processed=False).first())
        if payload is None:
            return None
        try:
            # Savepoint: a failure rolls back any half-written result rows
            # but keeps the lock so the outcome can still be recorded.
            with transaction.atomic():
                handler, rd, race = _resolve(payload)
                dup = _duplicate_of(payload)
                if dup is not None:
                    raise Rejected(f"duplicate of payload {dup.pk}")
                handler(payload, rd, race)
        except Rejected as e:
            _finish(payload, error=str(e)[:500])
            log.info("device payload %s rejected: %s", payload.pk, e)
            return "rejected"
        except Exception as e:  # transient (DB hiccup etc.) -- retry later
            payload.retry_count += 1
            if payload.retry_count >= MAX_RETRIES:
                _finish(payload, error=f"gave up after {payload.retry_count} attempts: {e}"[:500])
                log.exception("device payload %s failed permanently", payload.pk)
                return "rejected"
            payload.error = str(e)[:500]
            payload.save(update_fields=['error', 'retry_count'])
            log.warning("device payload %s failed (attempt %s): %s",
                        payload.pk, payload.retry_count, e)
            return "retry"
        _finish(payload)
        return "recorded"


def pending_payload_ids(since, limit=BATCH):
    return list(DevicePayload.objects
                .filter(processed=False, name__in=HANDLERS.keys(), created_at__gte=since)
                .order_by('id')
                .values_list('id', flat=True)[:limit])


def process_pending(limit=BATCH):
    """
    Process up to `limit` pending payloads, oldest first. Returns a dict of
    outcome counts. Does nothing unless DEVICE_RESULTS_ENABLED is on and
    DEVICE_RESULTS_SINCE is set.
    """
    counts = {"recorded": 0, "rejected": 0, "retry": 0}
    if not getattr(settings, "DEVICE_RESULTS_ENABLED", False):
        return counts
    since = results_since()
    if since is None:
        log.warning("DEVICE_RESULTS_ENABLED is on but DEVICE_RESULTS_SINCE is unset; "
                    "not processing device results")
        return counts
    for pid in pending_payload_ids(since, limit):
        outcome = process_payload(pid)
        if outcome:
            counts[outcome] += 1
    return counts
