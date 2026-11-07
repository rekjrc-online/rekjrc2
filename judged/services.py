"""
Judged Event scoring with re-runs. Shared by the web views and (later) the
device-payload processor.

A "run" is one set of scores for an entry, one per judge (JudgedScore.
run_number). Judges never pick a run: a judge's score goes into the lowest
run of that entry they haven't scored yet, or starts the next one, so judges
stay in step even if they score out of order. A run is complete once every
judge (the race's judge_team members) has scored it; its total is the sum of
its scores. An entry ranks on its best complete run, within its RaceClass.
"""
from dataclasses import dataclass

from django.db import transaction

from races.models import RaceDriver
from races.results import (
    EntryRow, finish_race, group_into_sections, has_ranked_entries,
    post_to_race, standings_text)
from .models import JudgedScore


def is_judge(race, user):
    """True if user is a member of the race's judge_team."""
    if not race.judge_team:
        return False
    return race.judge_team.members.filter(user=user).exists()


def judge_count(race):
    """Number of judges = members of judge_team, or 0 if no judge_team."""
    if not race.judge_team:
        return 0
    return race.judge_team.members.count()


def next_run_number(race, racedriver, judge):
    """The run this judge's next score for this entry belongs to."""
    all_runs = set(JudgedScore.objects
                   .filter(race=race, racedriver=racedriver)
                   .values_list('run_number', flat=True))
    mine = set(JudgedScore.objects
               .filter(race=race, racedriver=racedriver, judge=judge)
               .values_list('run_number', flat=True))
    open_runs = sorted(all_runs - mine)
    if open_runs:
        return open_runs[0]
    return max(all_runs, default=0) + 1


def record_score(race, racedriver, judge, score):
    """
    Save `judge`'s score for `racedriver` into the right run. The entry row
    is locked so two simultaneous scores can't pick the same run number
    (the unique constraint backs this up).
    """
    with transaction.atomic():
        RaceDriver.objects.select_for_update().filter(pk=racedriver.pk).first()
        run_number = next_run_number(race, racedriver, judge)
        return JudgedScore.objects.create(
            race=race, racedriver=racedriver, judge=judge,
            score=score, run_number=run_number)


@dataclass
class JudgedRun:
    run_number: int
    scores: list          # [JudgedScore]
    judges: int           # judge_count(race) at the time of ranking

    @property
    def scored(self):
        return len(self.scores)

    @property
    def complete(self):
        return self.judges > 0 and self.scored >= self.judges

    @property
    def total(self):
        return sum(s.score for s in self.scores)

    def display(self):
        if self.complete:
            return f"Run {self.run_number}: {self.total:.1f}"
        return f"Run {self.run_number}: {self.scored}/{self.judges} judges"


def sections(race, user=None):
    """
    Per-class standings. Each row gets .runs (all runs, newest first),
    .best (best complete run or None), .incomplete (runs still being
    scored), and -- when `user` is given -- .next_run (the run that user
    would score next for this entry).
    """
    judges = judge_count(race)
    racedrivers = list(RaceDriver.objects.filter(race=race)
                       .select_related('driver', 'build', 'race_class').order_by('id'))
    by_rd = {rd.id: {} for rd in racedrivers}
    mine = {rd.id: set() for rd in racedrivers}
    for s in JudgedScore.objects.filter(race=race).order_by('run_number', 'id'):
        if s.racedriver_id not in by_rd:
            continue
        by_rd[s.racedriver_id].setdefault(s.run_number, []).append(s)
        if user is not None and s.judge_id == user.id:
            mine[s.racedriver_id].add(s.run_number)

    rows = []
    for rd in racedrivers:
        runs = [JudgedRun(n, scores, judges)
                for n, scores in sorted(by_rd[rd.id].items(), reverse=True)]
        complete = [r for r in runs if r.complete]
        best = max(complete, key=lambda r: r.total) if complete else None
        row = EntryRow(
            racedriver=rd, runs=runs, best=best, position=None,
            best_display=f"{best.total:.1f}" if best else "",
            run_displays=tuple(r.display() for r in runs))
        row.incomplete = [r for r in runs if not r.complete]
        if user is not None:
            numbers = set(by_rd[rd.id])
            open_runs = sorted(numbers - mine[rd.id])
            row.next_run = open_runs[0] if open_runs else max(numbers, default=0) + 1
        rows.append(row)

    return group_into_sections(
        race, rows,
        row_class_id=lambda r: r.racedriver.race_class_id,
        sort_key=lambda r: (-r.best.total,) if r.best else None)


def incomplete_runs(secs):
    """[(RaceDriver, JudgedRun)] for every run still missing a judge's score."""
    return [(row.racedriver, run)
            for s in secs for row in s.rows for run in row.incomplete]


def finish(race, secs=None):
    """Post per-class standings and close the race. False if nothing to rank."""
    secs = secs if secs is not None else sections(race)
    if not has_ranked_entries(secs):
        return False
    post_to_race(race, standings_text(
        race, secs,
        display=lambda row: f"{row.best.total:.1f} pts (run {row.best.run_number})"))
    finish_race(race)
    return True
