from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class RoundRobinRace(BaseModel):
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='round_robin_matchups'
    )
    model1 = models.ForeignKey(
        RaceDriver,
        on_delete=models.CASCADE,
        related_name='rr_lane1_races'
    )
    model2 = models.ForeignKey(
        RaceDriver,
        on_delete=models.CASCADE,
        related_name='rr_lane2_races'
    )
    winner = models.ForeignKey(
        RaceDriver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rr_won_matchups'
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.model1} vs {self.model2}"
