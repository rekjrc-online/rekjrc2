"""
Crawler Comp result recording + ranking. Shared by the web views and (later)
the device-payload processor. Every submitted run is a new CrawlerRun; a
driver ranks on their best (fewest penalty points, then fastest time).
"""
import json
import math

from django.db import transaction

from races.results import (
    Metric, class_suffix, entry_sections, finish_race, has_ranked_entries,
    post_to_race, standings_text)
from races.templatetags.race_filters import format_seconds
from .models import CrawlerRun, CrawlerRunLog


def _display(run):
    return f"{run.penalty_points} pts · {format_seconds(run.elapsed_time)}"


METRIC = Metric(
    model=CrawlerRun,
    # Placeholder rows the old views created on page load have no time;
    # without this they'd rank as a perfect 0-point run.
    is_valid=lambda run: run.elapsed_time is not None and run.elapsed_time > 0,
    sort_key=lambda run: (run.penalty_points, run.elapsed_time),
    display=_display,
)


def parse_run(elapsed_raw, points_raw):
    """('83.2', '4') -> (83.2, 4); None if the time is missing/invalid."""
    try:
        elapsed = float(str(elapsed_raw).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(elapsed) or elapsed <= 0:
        return None
    try:
        points = int(str(points_raw).strip()) if points_raw not in (None, "") else 0
    except (TypeError, ValueError):
        return None
    return elapsed, points


def parse_log(raw):
    """The crawl page's run_log JSON -> list of entry dicts; [] if absent/bad."""
    if not raw:
        return []
    try:
        entries = json.loads(raw)
        return [
            {"milliseconds": int(e["milliseconds"]), "label": str(e["label"])[:255],
             "delta": int(e["delta"])}
            for e in entries
        ]
    except (TypeError, ValueError, KeyError):
        return []


@transaction.atomic
def record_run(race, racedriver, elapsed, points, log_entries=(), device=None):
    """Create a new run (plus its event log) and post it to the race feed."""
    run = CrawlerRun.objects.create(
        race=race, racedriver=racedriver, elapsed_time=elapsed, penalty_points=points)
    lines = [f"{racedriver}{class_suffix(racedriver)}",
             f"Points: {points} | Time: {format_seconds(elapsed)}"]
    for entry in log_entries:
        CrawlerRunLog.objects.create(run=run, **entry)
        lines.append(entry["label"])
    if device is not None:
        lines.append(f"📡 via {device.name}")
    post_to_race(race, "\r\n".join(lines) + "\r\n")
    return run


def sections(race):
    return entry_sections(race, METRIC)


def finish(race):
    """Post per-class standings and close the race. False if nothing to rank."""
    secs = sections(race)
    if not has_ranked_entries(secs):
        return False
    post_to_race(race, standings_text(
        race, secs,
        display=lambda row: f"{row.best.penalty_points} pts | {row.best.elapsed_time:.2f}s"))
    finish_race(race)
    return True
