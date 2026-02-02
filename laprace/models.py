from django.db import models
from django.conf import settings
from rekjrc.base_models import BaseModel
from races.models import Race

class LapMonitorResult(BaseModel):
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='lapmonitor_results',
        db_index=True,
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lapmonitor_uploads',
    )
    # from CSV
    session_id = models.UUIDField()
    session_name = models.CharField(max_length=100)
    session_date = models.DateTimeField()
    session_kind = models.CharField(max_length=50)
    session_duration = models.DecimalField(max_digits=10, decimal_places=3)
    driver_id = models.UUIDField()
    driver_name = models.CharField(max_length=100)
    driver_transponder_id = models.CharField(max_length=50)
    driver_rank = models.IntegerField()
    lap_index = models.IntegerField()
    lap_end_time = models.DecimalField(max_digits=10, decimal_places=3)
    lap_duration = models.DecimalField(max_digits=10, decimal_places=3)
    lap_kind = models.CharField(max_length=50)
    # from CSV end

    class Meta:
        verbose_name = "LapMonitor Result"
        verbose_name_plural = "LapMonitor Results"
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["driver_id"]),
            models.Index(fields=["race", "session_id", "driver_id", "lap_index"])
        ]

    def __str__(self):
        return f"{self.session_name} - {self.driver_name} (Lap {self.lap_index})"
