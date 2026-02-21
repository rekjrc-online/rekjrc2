from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rekjrc.base_models import BaseModel
from PIL import Image, ImageDraw, ImageFont
import uuid as uuid_lib
import qrcode
import json
import os


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    sms_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        qr_payload = {
            "uuid": str(self.uuid),
            "type": "user"}
        qr_data = json.dumps(qr_payload)
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=3)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        header_lines = [f"{self.user.id}: {self.user.first_name} {self.user.last_name}", " "]

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

        qr_folder = os.path.join(settings.MEDIA_ROOT, "qrcodes/users")
        os.makedirs(qr_folder, exist_ok=True)
        qr_path = os.path.join(qr_folder, f"{self.uuid}.png")
        final_img.save(qr_path)


class Follow(BaseModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="followers")
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey("content_type", "object_id")

    @property
    def followed_type(self):
        return self.content_type.model

    class Meta:
        unique_together = ("follower", "content_type", "object_id")

    def __str__(self):
        return f"{self.follower} follows {self.object}"