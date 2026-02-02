from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class StopwatchRun(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='stopwatch_runs')
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name='stopwatch_runs')
    elapsed_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        if self.elapsed_time is not None:
            return f"{self.racedriver} - {self.elapsed_time:.2f}s"
        return f"{self.racedriver} - No time recorded"
