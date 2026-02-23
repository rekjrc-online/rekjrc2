from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

# python manage.py reset_race --race_id=42

class Command(BaseCommand):
    help = "Reset a race: clears all results, unlocks entries, and marks it active/unfinished."

    def add_arguments(self, parser):
        parser.add_argument(
            "--race_id",
            type=int,
            required=True,
            metavar="RACE_ID",
            help="Primary key (integer id) of the Race to reset.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip the confirmation prompt.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from races.models import Race, RaceDriver
        from posts.models import Post

        race_id = options["race_id"]

        try:
            race = Race.objects.get(pk=race_id)
        except Race.DoesNotExist:
            raise CommandError(f"No Race found with id={race_id}")

        self.stdout.write(f"\nRace:")
        self.stdout.write(f"  id         : {race.id}")
        self.stdout.write(f"  name       : {race.display_name}")
        self.stdout.write(f"  type       : {race.race_type}")
        self.stdout.write(f"  finished   : {race.race_finished}")
        self.stdout.write(f"  locked     : {race.entry_locked}")
        self.stdout.write(f"  is_active  : {race.is_active}")
        self.stdout.write(f"  drivers    : {RaceDriver.objects.filter(race=race).count()}")

        if not options["yes"]:
            confirm = input("\nThis will DELETE all results and posts for this race. Continue? [y/N] ").strip().lower()
            if confirm != "y":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        deleted_counts = {}

        # --- race-type-specific result tables ---

        try:
            from dragrace.models import DragRace
            n, _ = DragRace.objects.filter(race=race).delete()
            if n:
                deleted_counts["DragRace rounds"] = n
        except Exception:
            pass

        try:
            from swiss.models import SwissRace
            n, _ = SwissRace.objects.filter(race=race).delete()
            if n:
                deleted_counts["SwissRace matchups"] = n
        except Exception:
            pass

        try:
            from roundrobin.models import RoundRobinRace
            n, _ = RoundRobinRace.objects.filter(race=race).delete()
            if n:
                deleted_counts["RoundRobinRace matchups"] = n
        except Exception:
            pass

        try:
            from stopwatch.models import StopwatchRun
            n, _ = StopwatchRun.objects.filter(race=race).delete()
            if n:
                deleted_counts["StopwatchRun records"] = n
        except Exception:
            pass

        try:
            from topspeed.models import TopSpeedRun
            n, _ = TopSpeedRun.objects.filter(race=race).delete()
            if n:
                deleted_counts["TopSpeedRun records"] = n
        except Exception:
            pass

        try:
            from longjump.models import LongJumpRun
            n, _ = LongJumpRun.objects.filter(race=race).delete()
            if n:
                deleted_counts["LongJumpRun records"] = n
        except Exception:
            pass

        try:
            from judged.models import JudgedScore
            n, _ = JudgedScore.objects.filter(race=race).delete()
            if n:
                deleted_counts["JudgedScore records"] = n
        except Exception:
            pass

        try:
            from crawler.models import CrawlerRun
            # CrawlerRunLog deletes cascade from CrawlerRun
            n, _ = CrawlerRun.objects.filter(race=race).delete()
            if n:
                deleted_counts["CrawlerRun records (+ logs)"] = n
        except Exception:
            pass

        try:
            from laprace.models import LapMonitorResult
            n, _ = LapMonitorResult.objects.filter(race=race).delete()
            if n:
                deleted_counts["LapMonitorResult records"] = n
        except Exception:
            pass

        # --- clear finish_position on racedrivers (keep the entries themselves) ---
        updated = RaceDriver.objects.filter(race=race).exclude(finish_position=None).update(finish_position=None)
        if updated:
            deleted_counts["RaceDriver finish_position cleared"] = updated

        # --- delete posts authored by this race ---
        race_ct = ContentType.objects.get_for_model(Race)
        n, _ = Post.objects.filter(author_content_type=race_ct, author_object_id=race.id).delete()
        if n:
            deleted_counts["Posts deleted"] = n

        # --- reset race flags ---
        race.entry_locked = False
        race.race_finished = False
        race.is_active = True
        race.save(update_fields=["entry_locked", "race_finished", "is_active"])

        # --- report ---
        self.stdout.write("")
        if deleted_counts:
            for label, count in deleted_counts.items():
                self.stdout.write(f"  deleted  {count:>4}  {label}")
        else:
            self.stdout.write("  (no results found to delete)")

        self.stdout.write(self.style.SUCCESS(f"\nRace [{race.id}] \"{race.display_name}\" has been reset."))