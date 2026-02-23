from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from posts.models import Post
from .models import DragRace
import random

class Start_(LoginRequiredMixin, View):
    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)
        if DragRace.objects.filter(race=race).exists():
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        race.entry_locked = True
        race.save(update_fields=["entry_locked"])

        drivers = list(RaceDriver.objects.filter(race=race))
        random.shuffle(drivers)

        if len(drivers) < 2:
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        lines = [f"🏁 {race.display_name} 🏁", "🏁 Race Starting 🏁", ""]
        for rd in drivers:
            lines.append(f"  • {rd.driver} ({rd.build})")
        content = "\r\n".join(lines)
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content)

        # Calculate bracket size
        total_slots = 1
        while total_slots < len(drivers):
            total_slots *= 2

        num_byes = total_slots - len(drivers)

        # Build round 1
        queue = drivers + [None] * num_byes
        for i in range(0, total_slots, 2):
            DragRace.objects.create(
                race=race,
                model1=queue[i],
                model2=queue[i + 1],
                round_number=1)

        return redirect("dragrace:dragrace", race_uuid=race.uuid)

class DragRace_(LoginRequiredMixin, View):
    template_name = "races/dragrace.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        rounds = (DragRace.objects.filter(race=race).order_by("round_number", "id"))
        final_winner = None
        if rounds.exists():
            max_round = rounds.aggregate(max_round=Max("round_number"))["max_round"]
            current_round = rounds.filter(round_number=max_round)
            if current_round.exists() and all(r.winner for r in current_round):
                winners = [r.winner for r in current_round]
                if len(winners) > 1:
                    # Post the completed round before advancing
                    lines = [f"= Round {max_round} Results ="]
                    for match in current_round.order_by("id"):
                        if match.winner == match.model1:
                            lines.append(f"🏁 {match.model1.driver} ({match.model1.build}) vs {match.model2.driver} ({match.model2.build})")
                        else:
                            lines.append(f"{match.model1.driver} ({match.model1.build}) vs 🏁 {match.model2.driver} ({match.model2.build})")

                    # Leaderboard: still in vs eliminated
                    eliminated = []
                    for r in rounds.order_by("round_number", "id"):
                        if r.winner and r.model2:
                            loser = r.model2 if r.winner == r.model1 else r.model1
                            eliminated.append(loser)
                    eliminated_ids = {e.id for e in eliminated}
                    still_in = [w for w in winners]  # winners of the just-completed round
                    lines += ["", "= Leaderboard ="]
                    lines.append("Still in:")
                    for rd in still_in:
                        lines.append(f"  ✅ {rd.driver} ({rd.build})")
                    lines.append("Eliminated:")
                    # collect all eliminated across all rounds so far
                    all_eliminated = []
                    seen_ids = set()
                    for r in rounds.order_by("round_number", "id"):
                        if r.winner and r.model2:
                            loser = r.model2 if r.winner == r.model1 else r.model1
                            if loser.id not in seen_ids:
                                all_eliminated.append(loser)
                                seen_ids.add(loser.id)
                    for rd in all_eliminated:
                        lines.append(f"  ❌ {rd.driver} ({rd.build})")

                    content = "\r\n".join(lines)
                    Post.objects.create(
                        author_content_type=ContentType.objects.get_for_model(Race),
                        author_object_id=race.id,
                        content=content,
                        display_content=content)

                    for i in range(0, len(winners), 2):
                        DragRace.objects.create(
                            race=race,
                            model1=winners[i],
                            model2=winners[i + 1] if i + 1 < len(winners) else None,
                            round_number=max_round + 1)
                    return redirect("dragrace:dragrace", race_uuid=race.uuid)
                if len(winners) == 1 and not race.race_finished:
                    final_winner = winners[0]

        return render(request, self.template_name, {
            "race": race,
            "rounds": rounds,
            "final_winner": final_winner,
        })

    # --------------------------------------------------
    # POST — save match winners only
    # --------------------------------------------------
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)

        for match in DragRace.objects.filter(race=race):
            winner_id = request.POST.get(f"winner_{match.id}")
            if not winner_id:
                continue
            winner = RaceDriver.objects.filter(id=winner_id).first()
            if winner:
                match.winner = winner
                match.save(update_fields=["winner"])

        return redirect("dragrace:dragrace", race_uuid=race.uuid)


class Finish_(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)

        rounds = DragRace.objects.filter(race=race)

        max_round = rounds.aggregate(
            max_round=Max("round_number")
        )["max_round"]

        final_round = rounds.filter(round_number=max_round)

        if final_round.count() != 1:
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        final_match = final_round.first()
        if not final_match.winner:
            return redirect("dragrace:dragrace", race_uuid=race.uuid)

        racedriver1=final_match.model1
        racedriver2=final_match.model2
        if final_match.winner == final_match.model1:
            racedriver1.finish_position = 1
            racedriver2.finish_position = 2
        else:
            racedriver1.finish_position = 2
            racedriver2.finish_position = 1
        racedriver1.save(update_fields=["finish_position"])
        racedriver2.save(update_fields=["finish_position"])

        final_winner = final_match.winner
        runner_up = final_match.model2 if final_match.winner == final_match.model1 else final_match.model1

        lines = [
            "🏁 Drag Race Results 🏁",
            f"1st: {final_winner.driver} ({final_winner.build})",
            f"2nd: {runner_up.driver} ({runner_up.build})",
        ]

        content = "\r\n".join(lines)

        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content)

        race.race_finished = True
        race.save(update_fields=["race_finished"])

        return redirect("races:detail", uuid=race.uuid)