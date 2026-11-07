from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver
from django.conf import settings


class JudgedScore(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name="judged_scores")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.FloatField()
    # Re-runs: a "run" is one set of scores, one per judge. Assigned
    # automatically by judged.services.next_run_number() -- a judge's score
    # goes into the lowest run of this entry they haven't scored yet, or
    # starts the next run. Existing scores (pre re-runs) are all run 1.
    run_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'racedriver', 'judge', 'run_number'],
                name='unique_score_per_judge_driver_run'
            )
        ]

    def __str__(self):
        return f"{self.racedriver} - Run {self.run_number} - {self.judge} - {self.score:.1f}"