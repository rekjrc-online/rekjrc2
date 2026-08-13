import os

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from rekjrc.base_models import BaseModel, Ownable
from locations.models import Location

class Store(BaseModel, Ownable):
    location = models.ForeignKey (
        Location,
        on_delete=models.SET_NULL,
        related_name='stores',
        null=True,
        blank=True )
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    # ------------------------------------------------------------------
    # Online storefront (added 2026-08-07). A Store is a dealer/location
    # listing by default; is_storefront_enabled lets its owner turn it
    # into a sellable online storefront, rather than routing payments
    # through a single site-wide store/cart. See products.models.Product
    # .store, cart.models.Cart, and orders.models.Order, which are all
    # scoped to a single Store.
    #
    # Payment model (revised 2026-08-07): each store's Stripe setup is
    # handled by hand, off-platform, rather than via Stripe Connect --
    # Jason creates/confirms each store owner's own standalone Stripe
    # account and drops its keys into rekjrc/.env as
    # STRIPE_<store.pk>_SECRET_KEY / STRIPE_<store.pk>_PUBLIC_KEY /
    # STRIPE_<store.pk>_WEBHOOK_SECRET. Nothing about that account's
    # status is tracked in the database -- can_accept_payments below just
    # checks whether the secret key env var exists.
    # ------------------------------------------------------------------
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_storefront_enabled = models.BooleanField(
        default=False,
        help_text="Turn this on to let customers browse and buy this store's products online. "
                   "Requires this store's Stripe keys to already be set in .env (STRIPE_<id>_SECRET_KEY, "
                   "etc. -- ask Jason) before checkout will actually work.",
    )

    def __str__(self):
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.display_name)[:240] or "store"
            slug = base_slug
            i = 2
            while Store.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
            return reverse("stores:detail", kwargs={"uuid": self.uuid})

    @property
    def can_accept_payments(self):
        """True once this store's Stripe secret key has been added to .env (STRIPE_<pk>_SECRET_KEY)."""
        if not self.pk:
            return False
        return bool(os.environ.get(f"STRIPE_{self.pk}_SECRET_KEY"))

    @property
    def storefront_live(self):
        """True when the owner has enabled the storefront AND Stripe onboarding is complete."""
        return self.is_storefront_enabled and self.can_accept_payments

    def get_storefront_url(self):
        return reverse("products:list", kwargs={"store_slug": self.slug})
