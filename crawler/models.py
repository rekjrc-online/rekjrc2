from django.db import models
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver

class CrawlerRun(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='crawler_runs')
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE, related_name='crawler_runs')
    elapsed_time = models.FloatField(null=True, blank=True)
    penalty_points = models.IntegerField(default=0)

    def total_log_points(self):
        return self.log_entries.aggregate(models.Sum('delta'))['delta__sum'] or 0

    def __str__(self):
        if self.elapsed_time is not None:
            return f"{self.racedriver} - {self.penalty_points} points - {self.elapsed_time:.2f}s"
        return f"{self.racedriver} - No time recorded"

class CrawlerRunLog(BaseModel):
    run = models.ForeignKey(CrawlerRun, on_delete=models.CASCADE, related_name='log_entries')
    milliseconds = models.PositiveIntegerField()
    label = models.CharField(max_length=255)
    delta = models.IntegerField(default=0)

    class Meta:
        ordering = ['milliseconds']

    def __str__(self):
        return f"{self.milliseconds}ms - {self.label} ({self.delta:+})"
