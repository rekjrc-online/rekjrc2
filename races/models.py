from django.db import models
from django.conf import settings
from django.urls import reverse
from PIL import Image, ImageDraw, ImageFont
from rekjrc.base_models import BaseModel, Ownable
from clubs.models import Club
from devices.models import Device
from events.models import Event
from locations.models import Location
from teams.models import Team
from tracks.models import Track
from stores.models import Store
import qrcode
import os

class Race(BaseModel, Ownable):
    RACE_TYPE_CHOICES = [
        ('Lap Race',        'Lap Race'),
        ('Crawler Comp',    'Crawler Comp'),
        ('Stopwatch Race',  'Stopwatch Race'),
        ('Long Jump',       'Long Jump'),
        ('Top Speed',       'Top Speed'),
        ('Judged Event',    'Judged Event'),
        ('Drag Race',       'Drag Single Elimination'),
        ('Drag Double',     'Drag Double Elimination'),
        ('Round Robin',     'Drag Round Robin'),
        ('Swiss System',    'Drag Swiss System'), ]
    race_type = models.CharField(
        max_length=30,
        choices=RACE_TYPE_CHOICES,
        default='Lap Race')
    ENTRY_TYPE_CHOICES = [
        ('Open', 'Open'),
        ('Invitational', 'Invitational') ]
    entry_type = models.CharField(
        max_length=20,
        choices=ENTRY_TYPE_CHOICES,
        default='Open',
        blank=True,
        null=True)
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    track = models.ForeignKey(
        Track,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    judge_team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        related_name='judge_races',
        null=True,
        blank=True)
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True)
    TRANSPONDER_CHOICES = [
        ('LapMonitor','LapMonitor'),
        ('MyLaps','MyLaps') ]
    transponder = models.CharField(max_length=10, choices=TRANSPONDER_CHOICES, blank=True, null=True)
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        related_name='races',
        null=True,
        blank=True,
        help_text='Single device used for the whole race (e.g. radar gun for Top Speed)')
    entry_locked = models.BooleanField(default=False)
    race_finished = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse("races:detail", kwargs={"uuid": self.uuid})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        qr_data = f"https://www.rekjrc.com/races/{self.uuid}/join".strip()
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=3)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        header_lines = [self.display_name, " "]
        font_path = os.path.join(settings.BASE_DIR, "assets", "fonts", "DejaVuSans.ttf")
        try:
            font = ImageFont.truetype(font_path, 36)
        except IOError:
            font = ImageFont.load_default()
        ascent, descent = font.getmetrics()
        line_widths = []
        line_heights = []
        for line in header_lines:
            bbox = font.getbbox(line)
            width = bbox[2] - bbox[0]
            height = ascent + descent
            line_widths.append(width)
            line_heights.append(height)
        text_width = max(line_widths)
        text_height_total = sum(line_heights) + (len(header_lines)-1) * 5
        line_sizes = [font.getbbox(line) for line in header_lines]
        line_widths = [bbox[2] - bbox[0] for bbox in line_sizes]
        line_heights = [bbox[3] - bbox[1] for bbox in line_sizes]
        text_width = max(line_widths)
        text_height_total = sum(line_heights) + (len(header_lines) - 1) * 5
        padding = 10
        total_width = max(qr_img.width, text_width + 2*padding)
        total_height = qr_img.height + text_height_total + 2*padding + 5
        final_img = Image.new("RGB", (total_width, total_height), "white")
        draw_final = ImageDraw.Draw(final_img)
        current_y = padding
        for i, line in enumerate(header_lines):
            line_width = line_widths[i]
            line_height = line_heights[i]
            text_x = (total_width - line_width) // 2
            draw_final.text((text_x, current_y), line, fill="black", font=font)
            current_y += line_height + 5
        qr_x = (total_width - qr_img.width) // 2
        qr_y = current_y
        final_img.paste(qr_img, (qr_x, qr_y))
        qr_folder = os.path.join(settings.MEDIA_ROOT, "qrcodes/races")
        os.makedirs(qr_folder, exist_ok=True)
        qr_path = os.path.join(qr_folder, f"{self.uuid}.png")
        final_img.save(qr_path)

    @classmethod
    def for_user(cls, user):
        from django.db.models import Q
        return cls.objects.filter(
            Q(owner=user) | Q(judge_team__members__user=user)
        )

class RaceDriver(BaseModel):
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='race_drivers')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='race_drivers')
    build = models.ForeignKey(
        "builds.Build",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="race_entries")
    driver = models.ForeignKey(
        "drivers.Driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="race_entries")
    transponder = models.CharField(
        max_length=10,
        choices=[
            ('LapMonitor','LapMonitor'),
            ('MyLaps','MyLaps')],
        blank=True,
        null=True)
    finish_position = models.PositiveIntegerField(
        null=True,
        blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'driver', 'build'],
                name='unique_race_driver_build')]

    def __str__(self):
        return f"Driver: {self.driver or '-driver-'} - Build: {self.build or '-build-'}"


class RaceJudgeDevice(BaseModel):
    """
    Maps a device to a specific judge for a judged race.
    Each judge on the judge_team can have their own device.
    """
    race = models.ForeignKey(
        Race,
        on_delete=models.CASCADE,
        related_name='judge_devices')
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='judge_devices')
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='judge_assignments')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['race', 'judge'],
                name='unique_device_per_judge_per_race')
        ]

    def __str__(self):
        return f"{self.judge} → {self.device} @ {self.race}"
