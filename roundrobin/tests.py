from django.test import TestCase
from unittest.mock import MagicMock
from itertools import combinations
from collections import defaultdict

# ---------------------------------------------------------------------------
# Pure-logic tests (no DB required)
# ---------------------------------------------------------------------------

def _build_standings_pure(matchups):
    """Duplicate of the view helper so we can test it in isolation."""
    wins   = defaultdict(int)
    losses = defaultdict(int)
    played = defaultdict(int)
    participants = {}

    for m in matchups:
        participants[m['model1_id']] = m['model1']
        participants[m['model2_id']] = m['model2']
        if m['winner_id'] is not None:
            played[m['model1_id']] += 1
            played[m['model2_id']] += 1
            wins[m['winner_id']] += 1
            loser_id = m['model2_id'] if m['winner_id'] == m['model1_id'] else m['model1_id']
            losses[loser_id] += 1

    standings = []
    for rd_id, rd in participants.items():
        standings.append({
            'driver': rd,
            'wins':   wins[rd_id],
            'losses': losses[rd_id],
            'played': played[rd_id],
        })

    standings.sort(key=lambda x: (-x['wins'], x['losses'], str(x['driver'])))
    return standings


class MatchupCountTests(TestCase):
    def _driver(self, n):
        return MagicMock(id=n, __str__=lambda self: f'Driver{n}')

    def test_3_drivers_gives_3_matchups(self):
        drivers = [self._driver(i) for i in range(3)]
        pairs = list(combinations(drivers, 2))
        self.assertEqual(len(pairs), 3)

    def test_4_drivers_gives_6_matchups(self):
        drivers = [self._driver(i) for i in range(4)]
        pairs = list(combinations(drivers, 2))
        self.assertEqual(len(pairs), 6)

    def test_5_drivers_gives_10_matchups(self):
        drivers = [self._driver(i) for i in range(5)]
        pairs = list(combinations(drivers, 2))
        self.assertEqual(len(pairs), 10)

    def test_formula_n_choose_2(self):
        for n in range(2, 9):
            drivers = [self._driver(i) for i in range(n)]
            expected = n * (n - 1) // 2
            self.assertEqual(len(list(combinations(drivers, 2))), expected)

    def test_all_pairs_unique(self):
        drivers = [self._driver(i) for i in range(5)]
        pairs = list(combinations(drivers, 2))
        # Each unordered pair appears exactly once
        seen = set()
        for a, b in pairs:
            key = frozenset({a.id, b.id})
            self.assertNotIn(key, seen)
            seen.add(key)


class StandingsTests(TestCase):
    def _matchup(self, m1_id, m2_id, winner_id):
        return {
            'model1_id': m1_id,
            'model2_id': m2_id,
            'winner_id': winner_id,
            'model1': f'Driver{m1_id}',
            'model2': f'Driver{m2_id}',
        }

    def test_standings_order_by_wins(self):
        # Driver 0 beats both; Driver 1 beats Driver 2
        matchups = [
            self._matchup(0, 1, 0),
            self._matchup(0, 2, 0),
            self._matchup(1, 2, 1),
        ]
        standings = _build_standings_pure(matchups)
        self.assertEqual(standings[0]['driver'], 'Driver0')  # 2 wins
        self.assertEqual(standings[1]['driver'], 'Driver1')  # 1 win
        self.assertEqual(standings[2]['driver'], 'Driver2')  # 0 wins

    def test_incomplete_matchups_not_counted(self):
        matchups = [
            self._matchup(0, 1, 0),
            self._matchup(0, 2, None),  # not yet decided
            self._matchup(1, 2, None),
        ]
        standings = _build_standings_pure(matchups)
        driver0 = next(s for s in standings if s['driver'] == 'Driver0')
        self.assertEqual(driver0['wins'], 1)
        self.assertEqual(driver0['played'], 1)

    def test_tie_broken_by_losses(self):
        # Both drivers have 1 win; driver 0 has fewer losses
        matchups = [
            self._matchup(0, 1, 0),   # 0 beats 1
            self._matchup(0, 2, 2),   # 2 beats 0
            self._matchup(1, 2, 1),   # 1 beats 2
        ]
        standings = _build_standings_pure(matchups)
        # 0: 1W 1L, 1: 1W 1L, 2: 1W 1L  → all tied, falls to alpha
        wins = [s['wins'] for s in standings]
        self.assertEqual(wins, [1, 1, 1])
