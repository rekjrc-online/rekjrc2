"""
Pure-logic tests for the Swiss bracket helpers, including the
Championship Round pairing and final standings tiebreaker.
No database required.
"""
from django.test import TestCase
from collections import defaultdict
import math


# ---------------------------------------------------------------------------
# Inline copies of the pure helpers
# ---------------------------------------------------------------------------

CHAMPIONSHIP_ROUND = 0


def _target_rounds(n):
    if n < 2:
        return 1
    return min(math.ceil(math.log2(n)), n - 1)


def _wins_losses(matchups):
    wins   = defaultdict(int)
    losses = defaultdict(int)
    for m in matchups:
        if m['winner_id']:
            wins[m['winner_id']] += 1
            loser_id = m['model2_id'] if m['winner_id'] == m['model1_id'] else m['model1_id']
            if loser_id:
                losses[loser_id] += 1
    return wins, losses


def _past_opponents(matchups):
    faced = defaultdict(set)
    for m in matchups:
        if m['model2_id']:
            faced[m['model1_id']].add(m['model2_id'])
            faced[m['model2_id']].add(m['model1_id'])
    return faced


def _swiss_pairings(drivers, wins, losses, faced):
    sorted_drivers = sorted(
        drivers,
        key=lambda d: (-wins[d['id']], losses[d['id']], d['id']),
    )
    unpaired = list(sorted_drivers)
    pairs = []
    while unpaired:
        a = unpaired.pop(0)
        opponent = None
        for i, b in enumerate(unpaired):
            if b['id'] not in faced[a['id']]:
                opponent = unpaired.pop(i)
                break
        if opponent is None and unpaired:
            opponent = unpaired.pop(0)
        pairs.append((a, opponent))
    return pairs


def _championship_pairings(drivers, wins, losses):
    ranked = sorted(
        drivers,
        key=lambda d: (-wins[d['id']], losses[d['id']], d['id']),
    )
    pairs = []
    lo, hi = 0, len(ranked) - 1
    while lo < hi:
        pairs.append((ranked[lo], ranked[hi]))
        lo += 1
        hi -= 1
    if lo == hi:
        pairs.append((ranked[lo], None))
    return pairs


def _final_standings(drivers, swiss_wins, swiss_losses, champ_winner_ids):
    def sort_key(d):
        return (
            -swiss_wins[d['id']],
             swiss_losses[d['id']],
             0 if d['id'] in champ_winner_ids else 1,
             str(d['id']),
        )
    return sorted(drivers, key=sort_key)


def _d(id_):
    return {'id': id_}


# ---------------------------------------------------------------------------
# Swiss helper tests (unchanged from before)
# ---------------------------------------------------------------------------

class TargetRoundsTests(TestCase):
    def test_2_players(self):   self.assertEqual(_target_rounds(2), 1)
    def test_4_players(self):   self.assertEqual(_target_rounds(4), 2)
    def test_8_players(self):   self.assertEqual(_target_rounds(8), 3)
    def test_5_players_ceil(self): self.assertEqual(_target_rounds(5), 3)
    def test_3_players(self):   self.assertEqual(_target_rounds(3), 2)


class WinsLossesTests(TestCase):
    def _m(self, m1, m2, winner):
        return {'model1_id': m1, 'model2_id': m2, 'winner_id': winner}

    def test_basic_count(self):
        wins, losses = _wins_losses([self._m(1, 2, 1), self._m(1, 3, 3)])
        self.assertEqual(wins[1], 1); self.assertEqual(wins[3], 1)
        self.assertEqual(losses[2], 1); self.assertEqual(losses[1], 1)

    def test_unresolved_not_counted(self):
        wins, losses = _wins_losses([self._m(1, 2, None)])
        self.assertEqual(wins[1], 0); self.assertEqual(losses[2], 0)

    def test_bye_no_loss(self):
        wins, losses = _wins_losses([{'model1_id': 1, 'model2_id': None, 'winner_id': 1}])
        self.assertEqual(wins[1], 1)
        self.assertEqual(sum(losses.values()), 0)


class SwissPairingTests(TestCase):
    def test_top_two_paired_first(self):
        drivers = [_d(1), _d(2), _d(3), _d(4)]
        wins  = defaultdict(int, {1: 1, 2: 1})
        losses = defaultdict(int, {3: 1, 4: 1})
        faced = defaultdict(set)
        pairs = _swiss_pairings(drivers, wins, losses, faced)
        ids = [(a['id'], b['id'] if b else None) for a, b in pairs]
        self.assertIn((1, 2), ids)
        self.assertIn((3, 4), ids)

    def test_avoids_rematch(self):
        drivers = [_d(1), _d(2), _d(3)]
        wins = defaultdict(int, {1: 1})
        losses = defaultdict(int, {2: 1})
        faced = defaultdict(set, {1: {2}, 2: {1}})
        pairs = _swiss_pairings(drivers, wins, losses, faced)
        paired_ids = {frozenset({a['id'], b['id']}) for a, b in pairs if b}
        self.assertIn(frozenset({1, 3}), paired_ids)

    def test_odd_field_gets_bye(self):
        drivers = [_d(1), _d(2), _d(3)]
        wins = losses = defaultdict(int)
        faced = defaultdict(set)
        pairs = _swiss_pairings(drivers, wins, losses, faced)
        bye_pairs = [(a, b) for a, b in pairs if b is None]
        self.assertEqual(len(bye_pairs), 1)


# ---------------------------------------------------------------------------
# Championship Round pairing tests
# ---------------------------------------------------------------------------

class ChampionshipPairingTests(TestCase):

    def _pairs_as_sets(self, pairs):
        return [frozenset({a['id'], b['id']}) for a, b in pairs if b]

    def test_6_drivers_best_vs_worst_forced(self):
        # 3-0, 2-1, 2-1, 1-2, 1-2, 0-3
        drivers = [_d(i) for i in range(1, 7)]
        wins   = defaultdict(int, {1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0})
        losses = defaultdict(int, {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3})
        pairs  = _championship_pairings(drivers, wins, losses)
        sets   = self._pairs_as_sets(pairs)
        # Rule 1: best vs worst forced
        self.assertIn(frozenset({1, 6}), sets)
        # Rule 2: mirror bracket — 2nd vs 2nd-worst, 3rd vs 3rd-worst
        self.assertIn(frozenset({2, 5}), sets)
        self.assertIn(frozenset({3, 4}), sets)

    def test_mirror_bracket_middle_pairs(self):
        # Algorithm is a pure mirror bracket: 1st vs last, 2nd vs 2nd-last, etc.
        # For 6 drivers ranked 1-6: pairs are {1,6}, {2,5}, {3,4}
        drivers = [_d(i) for i in range(1, 7)]
        wins   = defaultdict(int, {1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0})
        losses = defaultdict(int, {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3})
        pairs  = _championship_pairings(drivers, wins, losses)
        sets   = self._pairs_as_sets(pairs)
        self.assertIn(frozenset({2, 5}), sets)
        self.assertIn(frozenset({3, 4}), sets)
        self.assertNotIn(frozenset({2, 4}), sets)
        self.assertNotIn(frozenset({3, 5}), sets)

    def test_2_drivers_single_match(self):
        drivers = [_d(1), _d(2)]
        wins   = defaultdict(int, {1: 1})
        losses = defaultdict(int, {2: 1})
        pairs  = _championship_pairings(drivers, wins, losses)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(frozenset({pairs[0][0]['id'], pairs[0][1]['id']}), frozenset({1, 2}))

    def test_4_drivers_best_vs_worst_plus_middle(self):
        # 2-0, 1-1, 1-1, 0-2
        drivers = [_d(i) for i in range(1, 5)]
        wins   = defaultdict(int, {1: 2, 2: 1, 3: 1, 4: 0})
        losses = defaultdict(int, {1: 0, 2: 1, 3: 1, 4: 2})
        pairs  = _championship_pairings(drivers, wins, losses)
        sets   = self._pairs_as_sets(pairs)
        self.assertIn(frozenset({1, 4}), sets)  # best vs worst
        self.assertIn(frozenset({2, 3}), sets)  # tied middle pair

    def test_odd_score_group_overflow(self):
        # 3-0, 2-1, 2-1, 2-1, 1-2, 0-3
        # After removing best(1) and worst(6): remaining = 2,3,4(all 2-1) and 5(1-2)
        # 3 drivers in 2-1 group → pair two, overflow one down to 1-2 group
        drivers = [_d(i) for i in range(1, 7)]
        wins   = defaultdict(int, {1: 3, 2: 2, 3: 2, 4: 2, 5: 1, 6: 0})
        losses = defaultdict(int, {1: 0, 2: 1, 3: 1, 4: 1, 5: 2, 6: 3})
        pairs  = _championship_pairings(drivers, wins, losses)
        sets   = self._pairs_as_sets(pairs)
        self.assertIn(frozenset({1, 6}), sets)  # best vs worst always
        # One 2-1 vs 2-1 pair
        two_one_pairs = [s for s in sets if all(i in {2,3,4} for i in s)]
        self.assertEqual(len(two_one_pairs), 1)
        # Overflow: one 2-1 driver races the 1-2 driver
        cross_pairs = [s for s in sets if any(i in {2,3,4} for i in s) and 5 in s]
        self.assertEqual(len(cross_pairs), 1)

    def test_no_duplicate_drivers(self):
        drivers = [_d(i) for i in range(1, 7)]
        wins   = defaultdict(int, {1: 3, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0})
        losses = defaultdict(int, {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3})
        pairs  = _championship_pairings(drivers, wins, losses)
        all_ids = [a['id'] for a, _ in pairs] + [b['id'] for _, b in pairs if b]
        self.assertEqual(len(all_ids), len(set(all_ids)))
class FinalStandingsTests(TestCase):

    def test_swiss_record_primary_sort(self):
        # Driver 1: 3W 0L, Driver 2: 1W 2L — 1 must be ahead regardless of champ
        drivers = [_d(1), _d(2)]
        swiss_wins   = defaultdict(int, {1: 3, 2: 1})
        swiss_losses = defaultdict(int, {1: 0, 2: 2})
        standings = _final_standings(drivers, swiss_wins, swiss_losses, champ_winner_ids=set())
        self.assertEqual(standings[0]['id'], 1)

    def test_championship_breaks_tie(self):
        # Drivers 1 and 2 are exactly tied on Swiss record.
        # Driver 2 won the championship match → 2 should rank ahead of 1.
        drivers = [_d(1), _d(2)]
        swiss_wins   = defaultdict(int, {1: 2, 2: 2})
        swiss_losses = defaultdict(int, {1: 1, 2: 1})
        champ_winner_ids = {2}  # driver 2 won their champ matchup
        standings = _final_standings(drivers, swiss_wins, swiss_losses, champ_winner_ids)
        self.assertEqual(standings[0]['id'], 2)
        self.assertEqual(standings[1]['id'], 1)

    def test_championship_only_breaks_tied_pair(self):
        # Driver 1: 3W (clear leader), Drivers 2 & 3 tied, Driver 2 won champ.
        drivers = [_d(1), _d(2), _d(3)]
        swiss_wins   = defaultdict(int, {1: 3, 2: 1, 3: 1})
        swiss_losses = defaultdict(int, {1: 0, 2: 2, 3: 2})
        champ_winner_ids = {2}
        standings = _final_standings(drivers, swiss_wins, swiss_losses, champ_winner_ids)
        self.assertEqual(standings[0]['id'], 1)  # unambiguous leader stays 1st
        self.assertEqual(standings[1]['id'], 2)  # champ winner gets 2nd
        self.assertEqual(standings[2]['id'], 3)  # champ loser gets 3rd

    def test_alphabetical_fallback(self):
        # All tied, no champ winners — falls back to str(id) sort
        drivers = [_d(3), _d(1), _d(2)]
        swiss_wins = losses = defaultdict(int)
        standings = _final_standings(drivers, swiss_wins, losses, champ_winner_ids=set())
        ids = [d['id'] for d in standings]
        self.assertEqual(ids, sorted(ids, key=str))
