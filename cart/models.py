from decimal import Decimal

from django.conf import settings
from django.db import models

from rekjrc.base_models import BaseModel
from products.models import ProductVariant


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
