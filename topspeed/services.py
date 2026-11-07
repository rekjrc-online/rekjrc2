"""
Top Speed result recording + ranking. Shared by the web views and (later)
the device-payload processor, so both paths record and rank identically.
Every submitted speed is a new TopSpeedRun; a driver ranks on their fastest.
"""
from decimal import Decimal, InvalidOperation

from races.results import (
    Metric, class_suffix, entry_sections, finish_race, has_ranked_entries,
    post_to_race, standings_text)
from .models import TopSpeedRun


def _display(run):
    return f"{run.topspeed:.2f} mph"


METRIC = Metric(
    model=TopSpeedRun,
    is_valid=lambda run: run.topspeed is not None,
    sort_key=lambda run: (-run.topspeed,),   # highest speed first
    display=_display,
)


def parse_mph(raw):
    """'45.2' -> Decimal('45.20'); None if missing/invalid/out of range
    (TopSpeedRun.topspeed is max_digits=5, decimal_places=2)."""
    try:
        mph = Decimal(str(raw).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not mph.is_finite() or mph <= 0 or mph >= 1000:
        return None
    return mph


def record_topspeed(race, racedriver, mph, device=None):
    """Create a new run for `racedriver` and post it to the race feed."""
    mph = Decimal(str(mph)).quantize(Decimal("0.01"))
    run = TopSpeedRun.objects.create(race=race, racedriver=racedriver, topspeed=mph)
    text = (f"Top Speed Recorded{class_suffix(racedriver)}\r\n"
            f"Driver: {racedriver.driver}\r\nBuild: {racedriver.build}\r\n"
            f"Top Speed: {run.topspeed:.2f}mph")
    if device is not None:
        text += f"\r\n📡 via {device.name}"
    post_to_race(race, text)
    return run


def sections(race):
    return entry_sections(race, METRIC)


def finish(race):
    """Post per-class standings and close the race. False if nothing to rank."""
    secs = sections(race)
    if not has_ranked_entries(secs):
        return False
    post_to_race(race, standings_text(
        race, secs, display=lambda row: f"{row.best.topspeed:.2f}mph"))
    finish_race(race)
    return True
