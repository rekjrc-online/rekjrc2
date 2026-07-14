from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from rekjrc.base_models import BaseModel

class Device(BaseModel):
    mac         = models.CharField(max_length=17, unique=True)  # "AA:BB:CC:DD:EE:FF"
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    # GFK "owner" — the entity that owns this device for assignment / racing.
    # Allowable target models: User, Team, Club, Location.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='owned_devices')
    object_id    = models.PositiveIntegerField(null=True, blank=True)
    owner        = GenericForeignKey('content_type', 'object_id')

    # The human who claimed this device. Distinct from `owner` because a device
    # may be owned by a Club/Team/Location, but a single user performed the claim
    # (used for audit + permission to re-assign).
    claimed_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='claimed_devices')

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.mac})"

    def get_absolute_url(self):
        return reverse("devices:detail", kwargs={"uuid": self.uuid})

    @property
    def is_unlinked(self):
        """True if this device has no GFK owner set yet."""
        return self.content_type_id is None

    @property
    def owner_type(self):
        """Lowercase model name of the owner (e.g. 'club'), or None if unlinked."""
        if self.content_type_id is None:
            return None
        return self.content_type.model

    @property
    def owner_display(self):
        """Human-readable label for the owner, or '' if unlinked / dangling."""
        owner = self.owner
        if owner is None:
            return ''
        # Ownable subclasses expose display_name; User has get_full_name / email.
        return getattr(owner, 'display_name', None) \
            or getattr(owner, 'get_full_name', lambda: '')() \
            or getattr(owner, 'email', '') \
            or str(owner)

class DeviceWhitelist(models.Model):
    """
    MAC addresses pre-approved to self-publish an unclaimed Device row via
    the Go gateway's self-publish endpoint (gateway.rekjrc.com/device/publish/),
    triggered from the ESP32 Universal Keypad's Settings -> Show Owner ->
    Publish flow. Deliberately populated by hand (admin) only — this is the
    gate that stops an arbitrary/spoofed MAC from creating device rows.
    Presence on this list does not claim or own a device; it only allows the
    bare unclaimed row to be created so a logged-in Django user can claim it
    via the existing Scan flow (devices:scan).
    """
    mac        = models.CharField(max_length=17, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Device whitelist entry"
        verbose_name_plural = "Device whitelist"
        ordering = ["mac"]

    def __str__(self):
        return self.mac

    def save(self, *args, **kwargs):
        self.mac = self.mac.upper().strip()
        super().save(*args, **kwargs)


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
