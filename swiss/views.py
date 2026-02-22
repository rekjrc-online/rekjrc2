from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from posts.models import Post
from .models import SwissRace
import random
import math
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# round_number=0 is the sentinel for the Championship Round.
# Swiss rounds are numbered 1, 2, 3 … so 0 is safely distinct.
CHAMPIONSHIP_ROUND = 0


# ---------------------------------------------------------------------------
# Pairing helpers
# ---------------------------------------------------------------------------

def _wins_losses(matchups):
    """
    Return (wins, losses) dicts keyed by RaceDriver.id.
    Only completed matchups (winner set) are counted.
    """
    wins   = defaultdict(int)
    losses = defaultdict(int)
    for m in matchups:
        if m.winner_id:
            wins[m.winner_id] += 1
            loser_id = m.model2_id if m.winner_id == m.model1_id else m.model1_id
            if loser_id:
                losses[loser_id] += 1
    return wins, losses


def _past_opponents(matchups):
    """
    Return dict: driver_id -> set of opponent driver_ids already faced.
    BYE slots (model2 is None) are ignored.
    """
    faced = defaultdict(set)
    for m in matchups:
        if m.model2_id:
            faced[m.model1_id].add(m.model2_id)
            faced[m.model2_id].add(m.model1_id)
    return faced


def _swiss_pairings(drivers, wins, losses, faced):
    """
    Swiss pairing for one round.

    1. Sort drivers by score desc (wins desc, losses asc, then id).
    2. Greedily pair each unpaired driver with the next available
       driver they haven't yet faced.
    3. Odd field: lowest-ranked unpaired driver gets a BYE
       (model2=None, auto-resolved by caller).

    Returns list of (driver_a, driver_b_or_None).
    """
    sorted_drivers = sorted(
        drivers,
        key=lambda d: (-wins[d.id], losses[d.id], d.id),
    )
    unpaired = list(sorted_drivers)
    pairs = []
    while unpaired:
        a = unpaired.pop(0)
        opponent = None
        for i, b in enumerate(unpaired):
            if b.id not in faced[a.id]:
                opponent = unpaired.pop(i)
                break
        if opponent is None and unpaired:
            opponent = unpaired.pop(0)  # forced rematch
        pairs.append((a, opponent))
    return pairs


def _championship_pairings(drivers, wins, losses):
    """
    Championship Round pairing:

    Rule 1 — Always force best record vs worst record as a special match.
    Rule 2 — All remaining drivers pair within their own score group
             (same wins/losses race each other).
    Rule 3 — If a score group has an odd number of drivers, the lowest-ranked
             driver in that group drops down to pair with the top of the next
             group. If no next group exists, they get a BYE.

    Returns list of (driver_a, driver_b_or_None), best-vs-worst first.
    """
    from collections import OrderedDict as _OD
    ranked = sorted(
        drivers,
        key=lambda d: (-wins[d.id], losses[d.id], d.id),
    )

    if len(ranked) < 2:
        return [(ranked[0], None)] if ranked else []

    # Rule 1: force best vs worst
    best  = ranked[0]
    worst = ranked[-1]
    remaining = ranked[1:-1]

    pairs = [(best, worst)]

    if not remaining:
        return pairs

    # Rule 2: group remaining by score (wins, losses)
    groups = _OD()
    for d in remaining:
        key = (wins[d.id], losses[d.id])
        groups.setdefault(key, []).append(d)

    # Rule 3: pair within groups; odd leftover drops to next group
    overflow = None
    for key, group in groups.items():
        if overflow is not None:
            group = [overflow] + group
            overflow = None

        unpaired = list(group)
        while len(unpaired) >= 2:
            pairs.append((unpaired.pop(0), unpaired.pop(0)))

        if unpaired:
            overflow = unpaired[0]

    if overflow is not None:
        pairs.append((overflow, None))

    return pairs


def _final_standings(drivers, swiss_wins, swiss_losses, champ_winner_ids):
    """
    Final finish order:
      Primary    — Swiss wins desc, Swiss losses asc
      Tiebreaker — within a championship-round matched pair,
                   the winner of that match ranks higher
      Fallback   — alphabetical string representation
    """
    def sort_key(d):
        return (
            -swiss_wins[d.id],
             swiss_losses[d.id],
             0 if d.id in champ_winner_ids else 1,
             str(d),
        )
    return sorted(drivers, key=sort_key)


# ---------------------------------------------------------------------------
# How many Swiss rounds?
# ---------------------------------------------------------------------------

def _target_rounds(n):
    """ceil(log2(N)), min 1, capped at N-1."""
    if n < 2:
        return 1
    return min(math.ceil(math.log2(n)), n - 1)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class Start_(LoginRequiredMixin, View):
    """Seed round 1 randomly, lock entries, redirect to board."""

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)

        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)

        if SwissRace.objects.filter(race=race).exists():
            return redirect('swiss:swiss', race_uuid=race.uuid)

        drivers = list(RaceDriver.objects.filter(race=race))
        if len(drivers) < 2:
            return redirect('swiss:swiss', race_uuid=race.uuid)

        race.entry_locked = True
        race.save(update_fields=['entry_locked'])

        random.shuffle(drivers)

        for i in range(0, len(drivers), 2):
            model1 = drivers[i]
            model2 = drivers[i + 1] if i + 1 < len(drivers) else None
            m = SwissRace.objects.create(
                race=race, model1=model1, model2=model2, round_number=1,
            )
            if model2 is None:
                m.winner = model1
                m.save(update_fields=['winner'])

        return redirect('swiss:swiss', race_uuid=race.uuid)


class Swiss_(LoginRequiredMixin, View):
    """
    Main board view.

    GET advancement logic:
      • While Swiss rounds < _target_rounds(N): when current round fully
        resolved, generate next Swiss round and redirect (mirrors DragRace).
      • When last Swiss round resolves: generate Championship Round
        (round_number=0) using mirror-image standings pairings, redirect.
      • When Championship Round fully resolves: set ready_to_finish=True
        and render (no more redirects).

    POST: save winner selections, redirect to GET.
    """

    template_name = 'races/swiss.html'

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        all_matchups = list(
            SwissRace.objects.filter(race=race)
            .select_related('model1', 'model1__driver',
                            'model2', 'model2__driver',
                            'winner', 'winner__driver')
        )

        ready_to_finish = False

        if all_matchups:
            swiss_matchups = [m for m in all_matchups if m.round_number != CHAMPIONSHIP_ROUND]
            champ_matchups = [m for m in all_matchups if m.round_number == CHAMPIONSHIP_ROUND]

            max_swiss     = max((m.round_number for m in swiss_matchups), default=0)
            current_swiss = [m for m in swiss_matchups if m.round_number == max_swiss]
            swiss_done    = all(m.winner_id for m in current_swiss)

            drivers = list(RaceDriver.objects.filter(race=race))
            target  = _target_rounds(len(drivers))

            if swiss_done and not champ_matchups:
                swiss_wins, swiss_losses = _wins_losses(swiss_matchups)
                faced = _past_opponents(swiss_matchups)

                if max_swiss < target:
                    # Advance to next Swiss round
                    pairs = _swiss_pairings(drivers, swiss_wins, swiss_losses, faced)
                    for model1, model2 in pairs:
                        m = SwissRace.objects.create(
                            race=race, model1=model1, model2=model2,
                            round_number=max_swiss + 1,
                        )
                        if model2 is None:
                            m.winner = model1
                            m.save(update_fields=['winner'])
                    return redirect('swiss:swiss', race_uuid=race.uuid)

                else:
                    # All Swiss rounds done — generate Championship Round
                    pairs = _championship_pairings(drivers, swiss_wins, swiss_losses)
                    for model1, model2 in pairs:
                        m = SwissRace.objects.create(
                            race=race, model1=model1, model2=model2,
                            round_number=CHAMPIONSHIP_ROUND,
                        )
                        if model2 is None:
                            m.winner = model1
                            m.save(update_fields=['winner'])
                    return redirect('swiss:swiss', race_uuid=race.uuid)

            elif champ_matchups and all(m.winner_id for m in champ_matchups):
                ready_to_finish = True

        # ---- standings for display ----
        swiss_only = [m for m in all_matchups if m.round_number != CHAMPIONSHIP_ROUND]
        champ_only = [m for m in all_matchups if m.round_number == CHAMPIONSHIP_ROUND]
        swiss_wins, swiss_losses = _wins_losses(swiss_only) if swiss_only else ({}, {})
        champ_winner_ids = {m.winner_id for m in champ_only if m.winner_id}

        drivers_qs = RaceDriver.objects.filter(race=race).select_related('driver')
        ordered    = _final_standings(list(drivers_qs), swiss_wins, swiss_losses, champ_winner_ids)
        standings_rows = [
            {'driver': d, 'wins': swiss_wins[d.id], 'losses': swiss_losses[d.id]}
            for d in ordered
        ]

        max_swiss_display = max((m.round_number for m in swiss_only), default=0)

        return render(request, self.template_name, {
            'race':               race,
            'rounds':             all_matchups,
            'max_round':          max_swiss_display,
            'target_rounds':      _target_rounds(drivers_qs.count()),
            'standings':          standings_rows,
            'ready_to_finish':    ready_to_finish,
            'CHAMPIONSHIP_ROUND': CHAMPIONSHIP_ROUND,
        })

    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)

        for match in SwissRace.objects.filter(race=race):
            winner_id = request.POST.get(f'winner_{match.id}')
            if not winner_id:
                continue
            winner = RaceDriver.objects.filter(id=winner_id).first()
            if winner:
                match.winner = winner
                match.save(update_fields=['winner'])

        return redirect('swiss:swiss', race_uuid=race.uuid)


class Finish_(LoginRequiredMixin, View):
    """
    Lock the race.  Assign finish_position using Swiss record as primary
    sort and championship round result as tiebreaker.  Post summary.
    """

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)

        all_matchups = list(
            SwissRace.objects.filter(race=race)
            .select_related('model1', 'model1__driver', 'model1__build',
                            'model2', 'model2__driver', 'model2__build',
                            'winner', 'winner__driver', 'winner__build'))

        if not all_matchups or not all(m.winner_id for m in all_matchups):
            return redirect('swiss:swiss', race_uuid=race.uuid)

        swiss_only = [m for m in all_matchups if m.round_number != CHAMPIONSHIP_ROUND]
        champ_only = [m for m in all_matchups if m.round_number == CHAMPIONSHIP_ROUND]

        swiss_wins, swiss_losses = _wins_losses(swiss_only)
        champ_winner_ids = {m.winner_id for m in champ_only if m.winner_id}

        drivers_qs = RaceDriver.objects.filter(race=race).select_related('driver')
        standings  = _final_standings(list(drivers_qs), swiss_wins, swiss_losses, champ_winner_ids)

        for position, rd in enumerate(standings, start=1):
            rd.finish_position = position
            rd.save(update_fields=['finish_position'])

        # ---- summary post ----
        winner_rd = standings[0]
        lines = [
            '🏁 Swiss Bracket Results 🏁',
            f'Winner: {winner_rd.driver}  ({swiss_wins[winner_rd.id]}W–{swiss_losses[winner_rd.id]}L)',
            '',
            '= Final Standings =',
        ]
        for pos, rd in enumerate(standings, start=1):
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, f'#{pos}')
            lines.append(f"{medal} {rd.driver}  ({swiss_wins[rd.id]}W–{swiss_losses[rd.id]}L)")

        current_round = None
        for match in sorted(swiss_only, key=lambda m: (m.round_number, m.id)):
            if match.round_number != current_round:
                current_round = match.round_number
                lines += ['', f'= Round {current_round} =']
            if match.model2 is None:
                lines.append(f'🏁 {match.model1.driver} ({match.model1.build})  (BYE)')
            elif match.winner == match.model1:
                lines.append(f'🏁 {match.model1.driver} ({match.model1.build}) vs {match.model2.driver} ({match.model2.build})')
            else:
                lines.append(f'{match.model1.driver} ({match.model1.build}) vs 🏁 {match.model2.driver} ({match.model2.build})')

        if champ_only:
            lines += ['', '= Championship Round =']
            for match in sorted(champ_only, key=lambda m: m.id):
                if match.model2 is None:
                    lines.append(f'🏁 {match.model1.driver} ({match.model1.build})  (BYE)')
                elif match.winner == match.model1:
                    lines.append(f'🏁 {match.model1.driver} ({match.model1.build}) vs {match.model2.driver} ({match.model2.build})')
                else:
                    lines.append(f'{match.model1.driver} ({match.model1.build}) vs 🏁 {match.model2.driver} ({match.model2.build})')

        content = '\r\n'.join(lines)
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content,
        )

        race.race_finished = True
        race.save(update_fields=['race_finished'])
        return redirect('races:detail', uuid=race.uuid)
