"""
Shared result-ranking helpers for the run-based race types (Top Speed,
Stopwatch/Rally, Long Jump, Crawler Comp, Judged Event).

Two rules apply to every one of those race types:

  * Every run is kept. A driver may have any number of runs (re-runs); the
    web forms and, later, the device-payload processor each create a NEW run
    row per submitted result instead of filling in one per-driver row.
    A driver is ranked on their single BEST run.

  * Standings are per RaceClass. When a race has classes, drivers are ranked
    only against others in the same class and Finish posts a winner per
    class. When a race has no classes, there is one overall section, same as
    before classes existed.

Each race type describes itself with a `Metric` (which runs count, how to
order them best-first, how to display one) and then uses `entry_sections()`
for its Start page and `standings_text()` for its Finish post, so web and
device results are always ranked the same way.
"""
from dataclasses import dataclass
from typing import Any, Callable, Optional

from django.contrib.contenttypes.models import ContentType

from posts.models import Post
from .models import Race, RaceDriver


@dataclass(frozen=True)
class Metric:
    # Model with `race` and `racedriver` FKs (e.g. TopSpeedRun).
    model: Any
    # Returns True if this run carries a real result. Placeholder rows (the
    # empty runs the old one-run-per-driver views created on page load) are
    # ignored for ranking and display.
    is_valid: Callable[[Any], bool]
    # Sort key; LOWER sorts first (best). Equal keys are ties.
    sort_key: Callable[[Any], tuple]
    # Human-readable result for one run, e.g. "45.20 mph".
    display: Callable[[Any], str]


@dataclass
class EntryRow:
    racedriver: RaceDriver
    runs: list                 # valid runs, newest first
    best: Optional[Any]        # best valid run, or None
    position: Optional[int]    # rank within its class section, None if unranked
    best_display: str = ""     # Metric.display(best), for templates
    run_displays: tuple = ()   # Metric.display() of each run, newest first

    @property
    def attempts(self):
        return len(self.runs)


@dataclass
class ClassSection:
    race_class: Any            # races.RaceClass, or None
    rows: list                 # [EntryRow], ranked first, unranked after

    @property
    def title(self):
        return self.race_class.name if self.race_class else ""


def post_to_race(race, text):
    """Post `text` to the race's feed (author = the Race)."""
    Post.objects.create(
        author_content_type=ContentType.objects.get_for_model(Race),
        author_object_id=race.id,
        content=text)


def class_suffix(racedriver):
    """' [Stock]' when the entry has a class, '' otherwise -- for post text."""
    return f" [{racedriver.race_class.name}]" if racedriver.race_class_id else ""


def assign_positions(items, key):
    """
    Standard competition ranking ("1, 2, 2, 4"): items with equal `key` share
    a position. `items` must already be sorted best-first by `key`.
    Returns [(position, item)].
    """
    out, prev, pos = [], object(), 0
    for idx, item in enumerate(items, start=1):
        k = key(item)
        if k != prev:
            pos, prev = idx, k
        out.append((pos, item))
    return out


def group_into_sections(race, rows, row_class_id, sort_key):
    """
    Split `rows` into one ClassSection per RaceClass of `race` (in RaceClass
    order), plus a trailing "no class" section for entries whose class was
    deleted/never set -- or a single untitled section when the race has no
    classes at all. Within a section, rows with a non-None `sort_key(row)`
    are ranked (best first) and the rest follow unranked.
    """
    classes = list(race.race_classes.all())
    buckets = {rc.id: [] for rc in classes}
    unclassed = []
    for row in rows:
        cid = row_class_id(row)
        (buckets[cid] if cid in buckets else unclassed).append(row)

    def build(rc, bucket):
        ranked = sorted((r for r in bucket if sort_key(r) is not None), key=sort_key)
        unranked = [r for r in bucket if sort_key(r) is None]
        for pos, r in assign_positions(ranked, sort_key):
            r.position = pos
        return ClassSection(race_class=rc, rows=ranked + unranked)

    sections = [build(rc, buckets[rc.id]) for rc in classes]
    if unclassed or not classes:
        sections.append(build(None, unclassed))
    return sections


def entry_sections(race, metric):
    """
    Every RaceDriver in `race`, with all their valid runs and best run, ranked
    within their class. Drivers with no valid run are listed unranked at the
    bottom of their section. Used by each race type's Start page.
    """
    racedrivers = list(
        RaceDriver.objects
        .filter(race=race)
        .select_related('driver', 'build', 'race_class')
        .order_by('id'))
    runs_by_rd = {rd.id: [] for rd in racedrivers}
    for run in metric.model.objects.filter(race=race).order_by('-created_at', '-id'):
        if run.racedriver_id in runs_by_rd and metric.is_valid(run):
            runs_by_rd[run.racedriver_id].append(run)

    rows = []
    for rd in racedrivers:
        runs = runs_by_rd[rd.id]
        best = min(runs, key=metric.sort_key) if runs else None
        rows.append(EntryRow(
            racedriver=rd, runs=runs, best=best, position=None,
            best_display=metric.display(best) if best else "",
            run_displays=tuple(metric.display(r) for r in runs)))

    return group_into_sections(
        race, rows,
        row_class_id=lambda r: r.racedriver.race_class_id,
        sort_key=lambda r: metric.sort_key(r.best) if r.best else None)


def has_ranked_entries(sections):
    return any(row.position is not None for s in sections for row in s.rows)


def standings_text(race, sections, display):
    """
    Finish-post text: a winner block and a numbered leaderboard per class
    section (each headed by the class name when the race has classes).
    `display(row)` renders one ranked row's result, e.g. "45.20mph".
    Unranked entries (no valid run) are left out.
    """
    blocks = []
    multi = any(s.race_class for s in sections)
    for section in sections:
        ranked = [r for r in section.rows if r.position is not None]
        if not ranked:
            continue
        lines = []
        if multi:
            lines.append(f"== {section.title or 'No class'} ==")
        winners = [r for r in ranked if r.position == 1]
        if len(winners) == 1:
            w = winners[0].racedriver
            lines.append(f"🏁 Winner 🏁\r\nDriver: {w.driver}\r\nBuild: {w.build}\r\n")
        else:
            lines.append("🏁 Winners (tie) 🏁")
            for r in winners:
                lines.append(f"Driver: {r.racedriver.driver} | Build: {r.racedriver.build}")
            lines.append("")
        for r in ranked:
            lines.append(f"{r.position}. {display(r)} | {r.racedriver.driver} | {r.racedriver.build}")
        blocks.append("\r\n".join(lines))
    return "\r\n\r\n".join(blocks) or "No runs recorded."


def finish_race(race):
    race.race_finished = True
    race.entry_locked = True
    race.save()
