from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse

from rekjrc.base_models import BaseModel
from products.models import ProductVariant


class Order(BaseModel):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FULFILLED = "fulfilled"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_FULFILLED, "Fulfilled / shipped"),
        (STATUS_CANCELED, "Canceled"),
    ]

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)

    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    # TODO(shipping): no shipping-rate calculation is wired up yet (flagged
    # during scoping 2026-08-07, deliberately deferred). Set manually per
    # order -- via admin -- until real rates are built.
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.uuid} - {self.email} - {self.status}"

    def get_absolute_url(self):
        store_slug = self.store.slug if self.store else "store"
        return reverse("orders:confirmation", kwargs={"store_slug": store_slug, "uuid": self.uuid})

    def recalculate_totals(self):
        self.subtotal = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.total = self.subtotal + self.shipping_cost


class OrderItem(BaseModel):
    """
    Snapshots product/variant name and price at time of purchase so the
    order stays accurate even if the Product/ProductVariant is later
    edited or deleted (variant is SET_NULL, not CASCADE, for that reason).
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=255)
    variant_name = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=64, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.order.uuid})"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity
