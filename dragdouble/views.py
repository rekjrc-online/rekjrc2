from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from .models import DragDouble
import random

def build_loss_cache(race):
    cache = {}
    matches = DragDouble.objects.filter(race=race, winner__isnull=False)
    for m in matches:
        if not (m.model1 and m.model2):
            continue
        for driver in [m.model1, m.model2]:
            if driver.id not in cache:
                cache[driver.id] = 0
        loser = m.model2 if m.winner == m.model1 else m.model1
        cache[loser.id] += 1
    return cache

def build_win_cache(race):
    cache = {}
    matches = DragDouble.objects.filter(race=race, winner__isnull=False)
    for m in matches:
        if m.winner_id not in cache:
            cache[m.winner_id] = 0
        cache[m.winner_id] += 1
    return cache

def pair_and_create(race, drivers, round_number, bracket):
    loss_cache = build_loss_cache(race)
    win_cache = build_win_cache(race)
    for i in range(0, len(drivers), 2):
        model1 = drivers[i]
        model2 = drivers[i + 1] if i + 1 < len(drivers) else None
        model1_record = f"{win_cache.get(model1.id,0)}-{loss_cache.get(model1.id,0)}"
        model2_record = f"{win_cache.get(model2.id,0)}-{loss_cache.get(model2.id,0)}" if model2 else None
        DragDouble.objects.create(
            race=race,
            model1=model1,
            model1_record=model1_record,
            model2=model2,
            model2_record=model2_record,
            round_number=round_number,
            bracket=bracket)

def fetch_matches(race):
    w = list(DragDouble.objects.filter(race=race, bracket="W").order_by("round_number", "id"))
    l = list(DragDouble.objects.filter(race=race, bracket="L").order_by("round_number", "id"))
    f = list(DragDouble.objects.filter(race=race, bracket="F").order_by("round_number", "id"))
    return w, l, f

class Start_(LoginRequiredMixin, View):
    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)

        if race.race_finished:
            return redirect("races:detail", uuid=race.uuid)

        if DragDouble.objects.filter(race=race).exists():
            return redirect("dragdouble:dragdouble", race_uuid=race.uuid)

        race.entry_locked = True
        race.save(update_fields=["entry_locked"])

        drivers = list(RaceDriver.objects.filter(race=race))
        random.shuffle(drivers)

        if len(drivers) < 2:
            return redirect("dragdouble:dragdouble", race_uuid=race.uuid)

        pair_and_create(race, drivers, 1, "W")
        return redirect("dragdouble:dragdouble", race_uuid=race.uuid)

class Finish_(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)

        final_match = DragDouble.objects.filter(race=race, bracket="F").last()

        if not final_match or not final_match.winner:
            return redirect("dragdouble:dragdouble", race_uuid=race.uuid)

        winner = final_match.winner
        runner_up = final_match.model2 if winner == final_match.model1 else final_match.model1

        winner.finish_position = 1
        winner.save(update_fields=["finish_position"])

        if runner_up:
            runner_up.finish_position = 2
            runner_up.save(update_fields=["finish_position"])

        already_placed = {winner.id}
        if runner_up:
            already_placed.add(runner_up.id)

        position = 3
        seen = set()
        for match in DragDouble.objects.filter(race=race, winner__isnull=False).order_by("-round_number", "-id"):
            if not (match.model1 and match.model2):
                continue
            loser = match.model2 if match.winner == match.model1 else match.model1
            if loser.id not in already_placed and loser.id not in seen:
                seen.add(loser.id)
                loser.finish_position = position
                loser.save(update_fields=["finish_position"])
                position += 1

        race.race_finished = True
        race.save(update_fields=["race_finished"])

        return redirect("races:detail", uuid=race.uuid)

class DragDouble_(LoginRequiredMixin, View):
    template_name = "races/dragdouble.html"

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        drivers = list(RaceDriver.objects.filter(race=race))

        winners_matches, losers_matches, finals_matches = fetch_matches(race)
        loss_cache = build_loss_cache(race)
        win_cache = build_win_cache(race)

        record_map = {
            rd.id: f"{win_cache.get(rd.id, 0)}-{loss_cache.get(rd.id, 0)}"
            for rd in drivers
        }

        # Check if final winner exists
        final_winner = None
        if finals_matches:
            last_final = finals_matches[-1]
            if last_final.winner:
                if loss_cache.get(last_final.winner.id, 0) == 0:
                    final_winner = last_final.winner

        return render(request, self.template_name, {
            "race": race,
            "winners_matches": winners_matches,
            "losers_matches": losers_matches,
            "finals_matches": finals_matches,
            "record_map": record_map,
            "final_winner": final_winner,
        })

    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)

        # 1️⃣ Assign winners from POST
        updated_matches = []
        for match in DragDouble.objects.filter(race=race, winner__isnull=True):
            winner_id = request.POST.get(f"winner_{match.id}")
            if winner_id:
                try:
                    match.winner = RaceDriver.objects.get(id=winner_id, race=race)
                    match.save(update_fields=["winner"])
                    updated_matches.append(match)
                except RaceDriver.DoesNotExist:
                    continue

        # 2️⃣ Generate next winner round if possible
        winners_matches, losers_matches, finals_matches = fetch_matches(race)
        max_w = max((m.round_number for m in winners_matches), default=0)
        max_l = max((m.round_number for m in losers_matches), default=1)  # loser round 1 starts at 2

        current_w = [m for m in winners_matches if m.round_number == max_w]
        current_l = [m for m in losers_matches if m.round_number == max_l]

        loss_cache = build_loss_cache(race)

        # Collect winners and losers from current winner round
        round_winners = [m.winner for m in current_w if m.winner]
        fresh_losers = [m.model2 if m.winner == m.model1 else m.model1 for m in current_w if m.winner]

        # 2a. Create next winner round if >=2 winners
        next_w_exists = any(m.round_number == max_w + 1 for m in winners_matches)
        if len(round_winners) > 1 and not next_w_exists:
            pair_and_create(race, round_winners, max_w + 1, "W")

        # 2b. Create/update loser bracket
        # If no loser matches yet, first round is round 2
        next_l_round = max_l + 1 if losers_matches else 2
        # Collect losers from current loser round (if completed) and fresh losers
        losers_winners = [m.winner for m in current_l if m.winner] if current_l else []
        next_losers_pool = losers_winners + fresh_losers

        next_l_exists = any(m.round_number == next_l_round for m in losers_matches)
        if len(next_losers_pool) > 1 and not next_l_exists:
            pair_and_create(race, next_losers_pool, next_l_round, "L")

        # 3️⃣ Generate finals if applicable
        undefeated = [d for d in RaceDriver.objects.filter(race=race) if loss_cache.get(d.id, 0) == 0]
        one_loss = [d for d in RaceDriver.objects.filter(race=race) if loss_cache.get(d.id, 0) == 1]

        if len(undefeated) == 1 and len(one_loss) == 1 and not finals_matches:
            DragDouble.objects.create(
                race=race,
                model1=undefeated[0],
                model2=one_loss[0],
                bracket="F",
                round_number=1
            )

        return redirect("dragdouble:dragdouble", race_uuid=race.uuid)