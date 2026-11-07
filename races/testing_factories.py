"""Small fixtures shared by the run-based race types' test_services.py files."""
from itertools import count

from django.contrib.auth import get_user_model

from builds.models import Build
from drivers.models import Driver
from .models import Race, RaceClass, RaceDriver

_seq = count(1)


def make_user():
    return get_user_model().objects.create_user(email=f"user{next(_seq)}@test.com", password="pass")


def make_race(owner, race_type, classes=(), **kwargs):
    race = Race.objects.create(display_name=f"{race_type} race", owner=owner, race_type=race_type, **kwargs)
    for name in classes:
        RaceClass.objects.create(race=race, name=name)
    return race


def make_entry(race, name, race_class=None):
    user = make_user()
    return RaceDriver.objects.create(
        race=race, user=user,
        driver=Driver.objects.create(display_name=name, owner=user),
        build=Build.objects.create(display_name=f"{name} car", owner=user),
        race_class=race.race_classes.get(name=race_class) if race_class else None)
