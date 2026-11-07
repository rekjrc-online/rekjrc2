"""
Long Jump result recording + ranking. Shared by the web views and (later)
the device-payload processor. Every submitted jump is a new LongJumpRun; a
driver ranks on their longest.
"""
from races.results import (
    Metric, class_suffix, entry_sections, finish_race, has_ranked_entries,
    post_to_race, standings_text)
from .models import LongJumpRun

FEET_MAX = 999     # LongJumpRun.feet validators
INCHES_MAX = 11    # LongJumpRun.inches validators


METRIC = Metric(
    model=LongJumpRun,
    is_valid=lambda run: run.feet is not None and run.inches is not None,
    sort_key=lambda run: (-run.total_inches,),   # longest first
    display=lambda run: run.display_distance,
)


def parse_distance(feet_raw, inches_raw):
    """('12', '7') -> (12, 7); None if missing/invalid/out of range."""
    try:
        feet, inches = int(str(feet_raw).strip()), int(str(inches_raw).strip())
    except (TypeError, ValueError):
        return None
    if not (0 <= feet <= FEET_MAX and 0 <= inches <= INCHES_MAX):
        return None
    if feet == 0 and inches == 0:
        return None
    return feet, inches


def record_jump(race, racedriver, feet, inches, device=None):
    """Create a new run for `racedriver` and post it to the race feed."""
    run = LongJumpRun.objects.create(race=race, racedriver=racedriver, feet=feet, inches=inches)
    text = (f"Long Jump Recorded{class_suffix(racedriver)}\r\n"
            f"Driver: {racedriver.driver}\r\nBuild: {racedriver.build}\r\n"
            f"Distance: {run.display_distance}")
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
        race, secs, display=lambda row: row.best.display_distance))
    finish_race(race)
    return True
