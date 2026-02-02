from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class TopSpeedRun(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='topspeed_runs')
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name='topspeed_runs')
    topspeed = models.IntegerField(null=True, blank=True)

    def __str__(self):
        if self.topspeed is not None:
            return f"{self.racedriver} - {self.topspeed}mph"
        return f"{self.racedriver} - No top speed recorded"
