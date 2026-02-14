from django.db import models
from django.core.exceptions import ValidationError
from rekjrc.base_models import BaseModel
from races.models import Race, RaceDriver
from django.conf import settings

class JudgedEventRun(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE)
    racedriver = models.ForeignKey(RaceDriver, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['race', 'racedriver'], name='unique_race_racedriver')]

    def __str__(self):
        if self.scores.exists():
            avg_score = self.scores.aggregate(models.Avg('score'))['score__avg']
            return f"{self.racedriver} - {avg_score:.1f}"
        return f"{self.racedriver} - No score recorded"

class JudgedEventRunScore(BaseModel):
    run = models.ForeignKey(JudgedEventRun, on_delete=models.CASCADE, related_name='scores')
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.FloatField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['run', 'judge'], name='unique_judge_per_run_score')]

    def __str__(self):
        return f"{self.run.racedriver} - {self.judge} - {self.score:.1f}"

class Judge(BaseModel):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='race_judges')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['race', 'user'], name='unique_judge_per_race')]

    def clean(self):
        if self.race_id:
            count = Judge.objects.filter(race=self.race).exclude(pk=self.pk).count()
            if count >= 3:
                raise ValidationError("A race can have at most 3 judges.")

    def __str__(self):
        return str(self.user)
