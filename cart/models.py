from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from rekjrc.base_models import BaseModel
from products.models import ProductVariant


class PromoCode(BaseModel):
    """
    A flat percent-off-the-subtotal discount a shopper can apply to a Cart.
    Codes are matched case-insensitively ("prototype" == "PROTOTYPE"). A
    blank store means the code works at every store; otherwise it only
    applies to carts at that one store. times_used counts paid orders only
    (bumped in stripe_app.services.mark_order_paid), so abandoned checkouts
    don't burn through max_uses.
    """
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100.00"))],
        help_text="Percent off the cart subtotal, e.g. 25 for 25% off.",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="promo_codes",
        help_text="Leave blank to allow this code at every store.",
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave blank for unlimited uses.")
    times_used = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(Lower("code"), name="cart_promocode_code_ci_unique"),
        ]

    def __str__(self):
        return f"{self.code} ({self.discount_percent.normalize():f}% off)"

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip()
        super().save(*args, **kwargs)

    @classmethod
    def lookup(cls, code):
        code = (code or "").strip()
        if not code:
            return None
        return cls.objects.filter(code__iexact=code).first()

    def invalid_reason(self, store):
        """Returns a shopper-facing reason this code can't be used at `store`, or None if it can."""
        if not self.is_active:
            return "That promo code is no longer active."
        if self.expires_at and self.expires_at <= timezone.now():
            return "That promo code has expired."
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return "That promo code has reached its usage limit."
        if self.store_id and self.store_id != store.pk:
            return "That promo code isn't valid at this store."
        return None

    def discount_for(self, amount: Decimal) -> Decimal:
        discount = (amount * self.discount_percent / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
        return min(discount, amount)


class Cart(BaseModel):
    """
    Scoped to exactly one Store (a shopper checks out with one store at a
    time -- see the 2026-08-07 design discussion -- so buying from two
    stores means two separate Cart rows, not a mixed one). Session-based
    for anonymous shoppers (matched on session_key), or tied to a logged-in
    user. checked_out flips to True once a Stripe Checkout Session has been
    created from it, so a fresh Cart is used for anything added afterward.
    """
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="carts",
    )
    session_key = models.CharField(max_length=40, db_index=True, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    )
    checked_out = models.BooleanField(default=False)
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    )

    def __str__(self):
        who = self.user or self.session_key or self.uuid
        return f"Cart({who} @ {self.store}){' [checked out]' if self.checked_out else ''}"

    @property
    def subtotal(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.select_related("variant__product"):
            total += item.line_total
        return total

    @property
    def discount_amount(self) -> Decimal:
        if not self.promo_code:
            return Decimal("0.00")
        return self.promo_code.discount_for(self.subtotal)

    @property
    def total(self) -> Decimal:
        """Subtotal minus any promo discount (shipping is handled on the Order)."""
        return self.subtotal - self.discount_amount

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "variant")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.variant}"

    @property
    def line_total(self) -> Decimal:
        return self.variant.price * self.quantity
