from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class DragDouble(BaseModel):
    BRACKET_CHOICES = (
        ("W", "Win"),
        ("L", "Loss"),
        ("F", "Final"),
    )
    bracket = models.CharField(max_length=1, choices=BRACKET_CHOICES, default="W")
    round_number = models.PositiveSmallIntegerField(default=1)
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='drag_double_rounds'
    )
    model1 = models.ForeignKey(
        RaceDriver,
        on_delete=models.CASCADE,
        related_name='drag_double_lane1_races'
    )
    model1_record = models.CharField(max_length=20, null=True, blank=True)
    model2 = models.ForeignKey(
        RaceDriver,
        on_delete=models.CASCADE,
        related_name='drag_double_lane2_races',
        null=True,
        blank=True
    )
    model2_record = models.CharField(max_length=20, null=True, blank=True)
    winner = models.ForeignKey(
        RaceDriver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drag_double_won_rounds'
    )

    def __str__(self):
        return f"Round {self.round_number}: {self.model1} vs {self.model2 or 'BYE'}"
