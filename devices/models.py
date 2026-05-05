from django.conf import settings
from django.db import models
from django.utils import timezone

class Device(models.Model):
    mac         = models.CharField(max_length=17, unique=True)  # "AA:BB:CC:DD:EE:FF"
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner_user  = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.SET_NULL,
                      null=True, blank=True,
                      related_name='devices')
    owner_team  = models.ForeignKey(
                      'teams.Team',
                      on_delete=models.SET_NULL,
                      null=True, blank=True,
                      related_name='devices')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.mac})"

class DevicePayload(models.Model):
    device          = models.ForeignKey(
                          Device,
                          related_name='payloads',
                          on_delete=models.CASCADE)
    created_at      = models.DateTimeField(auto_now_add=True)
    racedriver_id   = models.PositiveIntegerField(null=True, blank=True)
    value           = models.CharField(max_length=32)
    name            = models.CharField(max_length=40, blank=True)
    processed       = models.BooleanField(default=False, db_index=True)
    processed_at    = models.DateTimeField(null=True, blank=True)
    error           = models.TextField(blank=True)
    retry_count     = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.device.name} @ {self.created_at:%Y-%m-%d %H:%M:%S} — {self.value}"

    def mark_processed(self):
        self.processed    = True
        self.processed_at = timezone.now()
        self.save(update_fields=['processed', 'processed_at'])

    def mark_error(self, message):
        self.error       = message
        self.retry_count += 1
        self.save(update_fields=['error', 'retry_count'])
