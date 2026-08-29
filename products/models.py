from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from rekjrc.base_models import BaseModel


class Product(BaseModel):
    """
    A sellable item belonging to exactly one Store (e.g. a Universal Keypad
    kit listed under "RekjRC Device Store"). Not Ownable itself -- a
    product's "owner" is its Store, reached via store.owner.

    Inventory is a simple on/off toggle (is_active) rather than a stock
    count -- unlist a product/variant by unchecking is_active instead of
    tracking quantity on hand.
    """
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Price in USD. Used for any variant that doesn't set its own price_override.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to unlist this product from the store without deleting it.",
    )
    sort_order = models.PositiveIntegerField(default=0)
    # Auto-generated (not hand-uploaded -- see admin.py) resized copy of
    # whichever ProductImage currently sorts first. Kept in sync by
    # rekjrc.tasks.resize_product_thumbnail, triggered from
    # ProductImage.save()/delete() below.
    thumbnail = models.ImageField(upload_to="products/thumbnails/", blank=True, null=True)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = ("store", "slug")

    def __str__(self):
        return f"{self.name} ({self.store.display_name})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if self.base_price is not None:
            # Coerce explicitly: Django doesn't cast DecimalField values on
            # plain assignment/save() (only on the way to SQL, or via a
            # ModelForm's full_clean()), so a Product created directly with
            # a string base_price (Product.objects.create(base_price="59.99"))
            # would otherwise keep that raw string in memory -- e.g.
            # "59.99" * 2 == "59.9959.99" instead of Decimal("119.98") --
            # until the instance is reloaded from the DB. Admin/API save
            # paths already coerce via their form/serializer layer; this
            # closes the gap for direct .create()/.save() calls.
            self.base_price = Decimal(str(self.base_price))
        if not self.slug:
            base_slug = slugify(self.name)[:240]
            slug = base_slug
            i = 2
            while Product.objects.filter(store=self.store, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)
        if is_new and not self.variants.exists():
            # A product needs at least one active variant to be purchasable
            # (see in_stock below) -- give it one automatically so a product
            # created without ever touching the admin's variant inline is
            # still sellable. SKU is derived from the pk (guaranteed unique)
            # rather than the slug, since ProductVariant.sku is unique
            # across all stores/products, not just within this one.
            self.variants.create(name="Default", sku=f"product-{self.pk}")

    def get_absolute_url(self):
        return reverse("products:detail", kwargs={"store_slug": self.store.slug, "slug": self.slug})

    @property
    def active_variants(self):
        return self.variants.filter(is_active=True)

    @property
    def in_stock(self):
        return self.is_active and self.active_variants.exists()

    @property
    def display_price(self):
        """Lowest active variant price, or base_price if there are no variants."""
        prices = [v.price for v in self.active_variants]
        return min(prices) if prices else self.base_price

    @property
    def primary_image(self):
        return self.images.first()


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.product.name} image ({self.sort_order})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._queue_thumbnail_refresh()

    def delete(self, *args, **kwargs):
        product_id = self.product_id
        super().delete(*args, **kwargs)
        self._queue_thumbnail_refresh(product_id)

    def _queue_thumbnail_refresh(self, product_id=None):
        # Recomputed fresh from the DB every time (not just "was I first
        # before this save") -- cheap at this scale, and correctly handles
        # re-sorting an *existing* image to sort_order 0, not just
        # uploading a new one.
        from rekjrc.tasks import resize_product_thumbnail
        resize_product_thumbnail.delay(product_id or self.product_id)


class ProductVariant(BaseModel):
    """
    A buyable option of a Product (e.g. "Black", "Rev B", or just "Default"
    for a product with no real options). Every Product needs at least one
    active variant to be purchasable -- the cart adds ProductVariants, not
    Products directly.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(
        max_length=255,
        default="Default",
        help_text='e.g. "Black", "Rev B" -- or leave as "Default" if this product has no options.',
    )
    sku = models.CharField(max_length=64, unique=True)
    price_override = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Leave blank to use the product's base price.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to mark this variant sold out / unavailable without deleting it.",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = ("product", "name")

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def price(self) -> Decimal:
        if self.price_override is not None:
            # Coerce explicitly: Django doesn't cast DecimalField values on
            # plain assignment/save() (only on the way to SQL, or via
            # full_clean()), so a variant created in-memory with a string
            # override (e.g. price_override="34.99") would otherwise return
            # that raw string here until the instance is reloaded from the DB.
            return Decimal(self.price_override)
        return self.product.base_price
