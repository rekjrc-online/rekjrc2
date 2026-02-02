from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class LongJumpRun(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='longjump_runs')
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name='longjump_runs')
    feet = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(999)])
    inches = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(11)])

    @property
    def total_inches(self):
        return (self.feet or 0) * 12 + (self.inches or 0)

    def __str__(self):
        if self.feet is not None and self.inches is not None:
            return f"{self.racedriver} - {self.feet}ft {self.inches}in"
        return f"{self.racedriver} - No distance recorded"
