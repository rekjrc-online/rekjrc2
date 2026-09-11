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
        extra_fields.pop("username", None)
        email = self.normalize_email(email).lower()
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password=password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    sms_opt_in = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            from accounts.tasks import generate_user_qr
            generate_user_qr.delay(self.pk)

    def _generate_qr(self):
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

        header_lines = [f"{self.id}: {self.first_name} {self.last_name}", " "]

        font_path = os.path.join(settings.BASE_DIR, "assets", "fonts", "DejaVuSans.ttf")
        try:
            font = ImageFont.truetype(font_path, 36)
        except IOError:
            font = ImageFont.load_default()

        line_sizes = [font.getbbox(line) for line in header_lines]
        line_widths = [bbox[2] - bbox[0] for bbox in line_sizes]
        line_heights = [bbox[3] - bbox[1] for bbox in line_sizes]

        text_width = max(line_widths)

        padding = 10
        total_width = max(qr_img.width, text_width + 2 * padding)
        total_height = qr_img.height + sum(line_heights) + (len(header_lines) - 1) * 5 + 2 * padding + 5

        final_img = Image.new("RGB", (total_width, total_height), "white")
        draw_final = ImageDraw.Draw(final_img)

        current_y = padding
        for i, line in enumerate(header_lines):
            text_x = (total_width - line_widths[i]) // 2
            draw_final.text((text_x, current_y), line, fill="black", font=font)
            current_y += line_heights[i] + 5

        final_img.paste(qr_img, ((total_width - qr_img.width) // 2, current_y))

        qr_folder = os.path.join(settings.MEDIA_ROOT, "qrcodes/users")
        os.makedirs(qr_folder, exist_ok=True)
        final_img.save(os.path.join(qr_folder, f"{self.uuid}.png"))

class VerificationLog(models.Model):
    """
    Permanent record of one "Verify a Friend" QR verification (see
    accounts.views.VerifyConfirmView) -- an already-verified user scanning
    another account's QR code and setting that account's is_verified to
    True. Insert-only: save()/delete() below refuse any update or removal
    of an existing row, and accounts.admin.VerificationLogAdmin blocks
    add/change/delete from the admin UI too (rows are created only by
    VerifyConfirmView).

    verifier/verified_user are nullable FKs (on_delete=SET_NULL) so deleting
    either User doesn't cascade the log row away -- but the *_uuid/_email/
    _name fields alongside them are snapshotted at creation time and never
    touched again, so the row stays meaningful (who verified whom, and
    when) even after one or both accounts are gone and the FK has gone
    null. Don't add a way to backfill/repair those snapshot fields from the
    live User record -- the whole point is that they're frozen at the
    moment of verification.
    """
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="verifications_performed")
    verifier_uuid = models.UUIDField(editable=False)
    verifier_email = models.EmailField(editable=False)
    verifier_name = models.CharField(max_length=255, editable=False, blank=True)

    verified_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="verifications_received")
    verified_uuid = models.UUIDField(editable=False)
    verified_email = models.EmailField(editable=False)
    verified_name = models.CharField(max_length=255, editable=False, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.verifier_email} verified {self.verified_email} on {self.created_at:%Y-%m-%d}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("VerificationLog rows are permanent and cannot be modified after creation.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("VerificationLog rows are permanent and cannot be deleted.")

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