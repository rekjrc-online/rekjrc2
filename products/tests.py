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

    def test_variant_price(self):
        product = Product.objects.create(store=self.store, name="Universal Keypad Kit")
        variant = ProductVariant.objects.create(product=product, sku="UK-001", price="49.99")
        self.assertEqual(variant.price, Decimal("49.99"))

    def test_variant_price_coerces_string_in_memory(self):
        # ProductVariant.save() explicitly coerces price to Decimal so an
        # in-memory instance created with a string price behaves correctly
        # before it's ever reloaded from the DB (see the comment in
        # ProductVariant.save()).
        product = Product.objects.create(store=self.store, name="Crawler Comp ESU")
        variant = ProductVariant.objects.create(
            product=product, name="Black", sku="CC-001-BLK", price="34.99")
        self.assertEqual(variant.price, Decimal("34.99"))

    def test_inactive_product_has_no_display_price_variants(self):
        product = Product.objects.create(store=self.store, name="Discontinued Kit")
        ProductVariant.objects.create(product=product, sku="DK-001", price="10.00", is_active=False)
        self.assertFalse(product.in_stock)

    def test_product_slug_unique_per_store_not_globally(self):
        other_owner = User.objects.create_user(email="other@example.com", password="testpass123")
        other_store = Store.objects.create(owner=other_owner, display_name="Other Store")
        p1 = Product.objects.create(store=self.store, name="Widget")
        p2 = Product.objects.create(store=other_store, name="Widget")
        self.assertEqual(p1.slug, p2.slug)  # both "widget" -- fine, different stores
        self.assertNotEqual(p1.store_id, p2.store_id)

    def test_slug_auto_increments_within_same_store(self):
        p1 = Product.objects.create(store=self.store, name="Gadget")
        p2 = Product.objects.create(store=self.store, name="Gadget")
        self.assertEqual(p1.slug, "gadget")
        self.assertEqual(p2.slug, "gadget-2")

    def test_display_price_returns_lowest_active_variant_price(self):
        product = Product.objects.create(store=self.store, name="Multi Variant Kit")
        ProductVariant.objects.create(product=product, name="Default", sku="MVK-DEFAULT", price="40.00")
        ProductVariant.objects.create(product=product, name="Budget", sku="MVK-BUDGET", price="19.99")
        self.assertEqual(product.display_price, Decimal("19.99"))

    def test_display_price_is_none_when_no_active_variants(self):
        # base_price is gone -- a product with no active variants (including
        # a brand new one with no variants at all) has no price to show.
        product = Product.objects.create(store=self.store, name="No Active Variant Kit")
        self.assertIsNone(product.display_price)

    def test_product_has_no_variants_until_one_is_added(self):
        # Product no longer auto-creates a "Default" variant on save() --
        # a freshly created Product has zero variants and isn't purchasable
        # until an owner explicitly adds a priced one.
        product = Product.objects.create(store=self.store, name="Auto Variant Kit")
        self.assertEqual(product.variants.count(), 0)
        self.assertFalse(product.in_stock)

    def test_variant_name_unique_per_product(self):
        product = Product.objects.create(store=self.store, name="Duplicate Name Kit")
        ProductVariant.objects.create(product=product, name="Default", sku="DUP-000", price="20.00")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductVariant.objects.create(product=product, name="Default", sku="DUP-001", price="20.00")

    def test_variant_sku_unique_globally(self):
        product1 = Product.objects.create(store=self.store, name="SKU Kit One")
        product2 = Product.objects.create(store=self.store, name="SKU Kit Two")
        ProductVariant.objects.create(product=product1, sku="SHARED-SKU", price="20.00")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductVariant.objects.create(product=product2, name="Black", sku="SHARED-SKU", price="25.00")

    def test_in_stock_false_when_product_itself_inactive(self):
        product = Product.objects.create(store=self.store, name="Toggled Off Kit")
        ProductVariant.objects.create(product=product, sku="TOK-001", price="30.00")
        product.is_active = False
        product.save()
        self.assertFalse(product.in_stock)
