from django.test import TestCase

from .results import assign_positions
from .testing_factories import make_entry, make_race, make_user


class AssignPositionsTests(TestCase):
    def test_ties_share_a_position_and_skip_the_next(self):
        ranked = assign_positions([10, 20, 20, 30], key=lambda v: v)
        self.assertEqual([p for p, _ in ranked], [1, 2, 2, 4])

    def test_empty(self):
        self.assertEqual(assign_positions([], key=lambda v: v), [])


class SectionsTests(TestCase):
    """Class grouping, exercised through Top Speed (simplest metric)."""

    def setUp(self):
        self.owner = make_user()

    def test_no_classes_gives_one_untitled_section(self):
        from topspeed import services
        race = make_race(self.owner, "Top Speed")
        make_entry(race, "A")
        secs = services.sections(race)
        self.assertEqual(len(secs), 1)
        self.assertIsNone(secs[0].race_class)

    def test_entries_ranked_within_their_own_class(self):
        from topspeed import services
        race = make_race(self.owner, "Top Speed", classes=["Pro", "Stock"])
        pro = make_entry(race, "ProDriver", "Pro")
        stock_fast = make_entry(race, "StockFast", "Stock")
        stock_slow = make_entry(race, "StockSlow", "Stock")
        services.record_topspeed(race, pro, "30.00")
        services.record_topspeed(race, stock_fast, "50.00")
        services.record_topspeed(race, stock_slow, "40.00")

        secs = services.sections(race)
        self.assertEqual([s.title for s in secs], ["Pro", "Stock"])  # RaceClass ordering
        pro_sec, stock_sec = secs
        self.assertEqual([(r.position, r.racedriver) for r in pro_sec.rows], [(1, pro)])
        self.assertEqual([(r.position, r.racedriver) for r in stock_sec.rows],
                         [(1, stock_fast), (2, stock_slow)])

    def test_entry_without_class_in_classed_race_gets_no_class_section(self):
        from topspeed import services
        race = make_race(self.owner, "Top Speed", classes=["Stock"])
        make_entry(race, "Classed", "Stock")
        make_entry(race, "Orphan")   # e.g. its class was deleted (SET_NULL)
        secs = services.sections(race)
        self.assertEqual([s.title for s in secs], ["Stock", ""])

    def test_finish_post_has_a_winner_block_per_class(self):
        from posts.models import Post
        from topspeed import services
        race = make_race(self.owner, "Top Speed", classes=["Pro", "Stock"])
        services.record_topspeed(race, make_entry(race, "P1", "Pro"), "30")
        services.record_topspeed(race, make_entry(race, "S1", "Stock"), "50")
        self.assertTrue(services.finish(race))
        text = Post.objects.filter(author_object_id=race.id).latest('id').content
        self.assertIn("== Pro ==", text)
        self.assertIn("== Stock ==", text)
        self.assertEqual(text.count("🏁 Winner 🏁"), 2)
        race.refresh_from_db()
        self.assertTrue(race.race_finished)
