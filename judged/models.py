from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver
from django.conf import settings


class JudgedScore(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name="judged_scores")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'racedriver', 'judge'],
                name='unique_score_per_judge_driver'
            )
        ]

    def __str__(self):
        return f"{self.racedriver} - {self.judge} - {self.score:.1f}"