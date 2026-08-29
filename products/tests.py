from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from stores.models import Store

from .models import Product, ProductVariant

User = get_user_model()


class ProductVariantPriceTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email="owner@example.com", password="testpass123")
        self.store = Store.objects.create(owner=owner, display_name="RekjRC Device Store")

    def test_variant_uses_base_price_when_no_override(self):
        product = Product.objects.create(store=self.store, name="Universal Keypad Kit", base_price="49.99")
        # Product.save() already auto-creates a "Default" variant -- reuse it
        # instead of creating a second one, which would collide on the
        # (product, name) unique constraint.
        variant = product.variants.get()
        variant.sku = "UK-001"
        variant.save()
        self.assertEqual(variant.price, product.base_price)

    def test_variant_price_override(self):
        product = Product.objects.create(store=self.store, name="Crawler Comp ESU", base_price="29.99")
        variant = ProductVariant.objects.create(
            product=product, name="Black", sku="CC-001-BLK", price_override="34.99")
        self.assertEqual(variant.price, Decimal("34.99"))

    def test_inactive_product_has_no_display_price_variants(self):
        product = Product.objects.create(store=self.store, name="Discontinued Kit", base_price="10.00")
        # Product.save() already auto-creates a "Default" variant -- mark
        # that one inactive instead of creating a second "Default" variant,
        # which would collide on the (product, name) unique constraint.
        variant = product.variants.get()
        variant.sku = "DK-001"
        variant.is_active = False
        variant.save()
        self.assertFalse(product.in_stock)

    def test_product_slug_unique_per_store_not_globally(self):
        other_owner = User.objects.create_user(email="other@example.com", password="testpass123")
        other_store = Store.objects.create(owner=other_owner, display_name="Other Store")
        p1 = Product.objects.create(store=self.store, name="Widget", base_price="10.00")
        p2 = Product.objects.create(store=other_store, name="Widget", base_price="10.00")
        self.assertEqual(p1.slug, p2.slug)  # both "widget" -- fine, different stores
        self.assertNotEqual(p1.store_id, p2.store_id)

    def test_slug_auto_increments_within_same_store(self):
        p1 = Product.objects.create(store=self.store, name="Gadget", base_price="10.00")
        p2 = Product.objects.create(store=self.store, name="Gadget", base_price="10.00")
        self.assertEqual(p1.slug, "gadget")
        self.assertEqual(p2.slug, "gadget-2")

    def test_display_price_returns_lowest_active_variant_price(self):
        product = Product.objects.create(store=self.store, name="Multi Variant Kit", base_price="40.00")
        default_variant = product.variants.get()
        default_variant.sku = "MVK-DEFAULT"
        default_variant.save()
        ProductVariant.objects.create(
            product=product, name="Budget", sku="MVK-BUDGET", price_override="19.99")
        self.assertEqual(product.display_price, Decimal("19.99"))

    def test_display_price_falls_back_to_base_price_when_no_active_variants(self):
        product = Product.objects.create(store=self.store, name="No Active Variant Kit", base_price="15.00")
        variant = product.variants.get()
        variant.sku = "NAV-001"
        variant.is_active = False
        variant.save()
        self.assertEqual(product.display_price, product.base_price)

    def test_product_save_auto_creates_default_variant(self):
        product = Product.objects.create(store=self.store, name="Auto Variant Kit", base_price="12.00")
        self.assertEqual(product.variants.count(), 1)
        variant = product.variants.get()
        self.assertEqual(variant.name, "Default")
        self.assertEqual(variant.sku, f"product-{product.pk}")
        self.assertTrue(variant.is_active)

    def test_variant_name_unique_per_product(self):
        # Product.save() already auto-creates a "Default" variant, so a
        # second explicit "Default" variant on the same product should
        # collide on the (product, name) unique constraint -- this is the
        # exact collision that broke cart/orders/products tests earlier.
        product = Product.objects.create(store=self.store, name="Duplicate Name Kit", base_price="20.00")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductVariant.objects.create(product=product, name="Default", sku="DUP-001")

    def test_variant_sku_unique_globally(self):
        product1 = Product.objects.create(store=self.store, name="SKU Kit One", base_price="20.00")
        product2 = Product.objects.create(store=self.store, name="SKU Kit Two", base_price="25.00")
        variant1 = product1.variants.get()
        variant1.sku = "SHARED-SKU"
        variant1.save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductVariant.objects.create(product=product2, name="Black", sku="SHARED-SKU")

    def test_in_stock_false_when_product_itself_inactive(self):
        product = Product.objects.create(store=self.store, name="Toggled Off Kit", base_price="30.00")
        # Auto-created "Default" variant is active, but the product itself
        # being unlisted should still make it out of stock.
        product.is_active = False
        product.save()
        self.assertFalse(product.in_stock)
