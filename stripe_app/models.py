from django.db import models
from django.conf import settings
from rekjrc.base_models import BaseModel

class StripePaymentLog(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stripe_payments'
    )
    product_slug = models.CharField(max_length=100)
    stripe_session_id = models.CharField(max_length=255)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    amount_total = models.PositiveIntegerField(blank=True, null=True)  # amount in cents
    currency = models.CharField(max_length=10, default="usd")
    status = models.CharField(max_length=50, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)  # optional timestamp for completed payment

    def __str__(self):
        user_str = str(self.user) if self.user else "Anonymous"
        return f"{user_str} - {self.product_slug} - {self.status or 'Pending'}"
