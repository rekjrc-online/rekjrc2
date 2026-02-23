from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from races.models import Race, RaceDriver
from posts.models import Post
from .models import RoundRobinRace
from itertools import combinations
from collections import defaultdict
import random

class Start_(LoginRequiredMixin, View):
    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)
        if RoundRobinRace.objects.filter(race=race).exists():
            return redirect('roundrobin:roundrobin', race_uuid=race.uuid)
        drivers = list(RaceDriver.objects.filter(race=race))
        if len(drivers) < 2:
            return redirect('roundrobin:roundrobin', race_uuid=race.uuid)
        race.entry_locked = True
        race.save(update_fields=['entry_locked'])
        random.shuffle(drivers)
        lines = [f"🏁 {race.display_name} — Race Starting! 🏁", ""]
        for rd in drivers:
            lines.append(f"  • {rd.driver} ({rd.build})")
        content = '\r\n'.join(lines)
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content)
        matchups = [
            RoundRobinRace(race=race, model1=a, model2=b)
            for a, b in combinations(drivers, 2) ]
        RoundRobinRace.objects.bulk_create(matchups)
        return redirect('roundrobin:roundrobin', race_uuid=race.uuid)

class RoundRobin_(LoginRequiredMixin, View):
    template_name = 'races/roundrobin.html'

    def get(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        matchups = RoundRobinRace.objects.filter(race=race).select_related(
            'model1', 'model1__driver',
            'model2', 'model2__driver',
            'winner', 'winner__driver', )
        all_complete = matchups.exists() and all(m.winner_id for m in matchups)
        standings = _build_standings(matchups) if matchups.exists() else []
        return render(request, self.template_name, {
            'race':         race,
            'matchups':     matchups,
            'standings':    standings,
            'all_complete': all_complete, })

    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)
        for matchup in RoundRobinRace.objects.filter(race=race):
            winner_id = request.POST.get(f'winner_{matchup.id}')
            if not winner_id:
                continue
            winner = RaceDriver.objects.filter(id=winner_id).first()
            if winner and winner in (matchup.model1, matchup.model2):
                matchup.winner = winner
                matchup.save(update_fields=['winner'])
        return redirect('roundrobin:roundrobin', race_uuid=race.uuid)

class Finish_(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request, race_uuid):
        race = get_object_or_404(Race.for_user(request.user), uuid=race_uuid)
        if race.race_finished:
            return redirect('races:detail', uuid=race.uuid)
        matchups = list(
            RoundRobinRace.objects.filter(race=race).select_related(
                'model1', 'model1__driver',
                'model2', 'model2__driver',
                'winner', 'winner__driver',))
        if not matchups:
            return redirect('roundrobin:roundrobin', race_uuid=race.uuid)
        if not all(m.winner_id for m in matchups):
            return redirect('roundrobin:roundrobin', race_uuid=race.uuid)
        standings = _build_standings(matchups)
        for position, entry in enumerate(standings, start=1):
            rd = entry['driver']
            rd.finish_position = position
            rd.save(update_fields=['finish_position'])
        lines = ['🏆 Round Robin Results 🏆', '']
        lines.append('= Final Standings =')
        for entry in standings:
            rd    = entry['driver']
            medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rd.finish_position, f"#{rd.finish_position}")
            lines.append(f"{medal} {entry['wins']}W – {entry['losses']}L – {rd.driver} ({rd.build})")
        content = '\r\n'.join(lines)
        Post.objects.create(
            author_content_type=ContentType.objects.get_for_model(Race),
            author_object_id=race.id,
            content=content,
            display_content=content,)
        race.race_finished = True
        race.save(update_fields=['race_finished'])
        return redirect('races:detail', uuid=race.uuid)

def _build_standings(matchups):
    wins   = defaultdict(int)
    losses = defaultdict(int)
    played = defaultdict(int)
    participants = {}
    for m in matchups:
        participants[m.model1_id] = m.model1
        participants[m.model2_id] = m.model2
        if m.winner_id:
            played[m.model1_id] += 1
            played[m.model2_id] += 1
            wins[m.winner_id] += 1
            loser_id = m.model2_id if m.winner_id == m.model1_id else m.model1_id
            losses[loser_id] += 1
    standings = []
    for rd_id, rd in participants.items():
        standings.append({
            'driver':  rd,
            'wins':    wins[rd_id],
            'losses':  losses[rd_id],
            'played':  played[rd_id], })
    standings.sort(key=lambda x: (-x['wins'], x['losses'], str(x['driver'])))
    return standings