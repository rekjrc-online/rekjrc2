"""
Stopwatch / Rally result recording + ranking. (Rally races use the stopwatch
views -- see races.views.Start_.) Shared by the web views and (later) the
device-payload processor. Every submitted time is a new StopwatchRun; a
driver ranks on their fastest.
"""
import math

from races.results import (
    Metric, class_suffix, entry_sections, finish_race, has_ranked_entries,
    post_to_race, standings_text)
from races.templatetags.race_filters import format_seconds
from .models import StopwatchRun


METRIC = Metric(
    model=StopwatchRun,
    is_valid=lambda run: run.elapsed_time is not None and run.elapsed_time > 0,
    sort_key=lambda run: (run.elapsed_time,),   # lowest time first
    display=lambda run: format_seconds(run.elapsed_time),
)


def parse_seconds(raw):
    """'12.34' -> 12.34; None if missing/invalid/not positive."""
    try:
        secs = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(secs) or secs <= 0:
        return None
    return secs


def record_time(race, racedriver, seconds, device=None):
    """Create a new run for `racedriver` and post it to the race feed."""
    run = StopwatchRun.objects.create(race=race, racedriver=racedriver, elapsed_time=seconds)
    text = (f"{race} - Stopwatch Run Recorded{class_suffix(racedriver)}\r\n\r\n"
            f"{racedriver} - {seconds:.2f}s\r\n")
    if device is not None:
        text += f"📡 via {device.name}\r\n"
    post_to_race(race, text)
    return run


def sections(race):
    return entry_sections(race, METRIC)


def finish(race):
    """
    Post per-class standings and close the race. Unlike the other run-based
    types, a Stopwatch/Rally race may be finished with no times at all --
    see the note in views.Finish_.
    """
    secs = sections(race)
    if has_ranked_entries(secs):
        text = standings_text(race, secs, display=lambda row: f"{row.best.elapsed_time:.2f}s")
    else:
        text = f"{race} - Race Finished\r\n\r\nNo stopwatch times recorded.\r\n"
    post_to_race(race, text)
    finish_race(race)
