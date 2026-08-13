from django.contrib.auth import get_user_model
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
        variant = ProductVariant.objects.create(product=product, name="Default", sku="UK-001")
        self.assertEqual(variant.price, product.base_price)

    def test_variant_price_override(self):
        product = Product.objects.create(store=self.store, name="Crawler Comp ESU", base_price="29.99")
        variant = ProductVariant.objects.create(
            product=product, name="Black", sku="CC-001-BLK", price_override="34.99")
        self.assertEqual(variant.price, 34.99)

    def test_inactive_product_has_no_display_price_variants(self):
        product = Product.objects.create(store=self.store, name="Discontinued Kit", base_price="10.00")
        ProductVariant.objects.create(product=product, name="Default", sku="DK-001", is_active=False)
        self.assertFalse(product.in_stock)

    def test_product_slug_unique_per_store_not_globally(self):
        other_owner = User.objects.create_user(email="other@example.com", password="testpass123")
        other_store = Store.objects.create(owner=other_owner, display_name="Other Store")
        p1 = Product.objects.create(store=self.store, name="Widget", base_price="10.00")
        p2 = Product.objects.create(store=other_store, name="Widget", base_price="10.00")
        self.assertEqual(p1.slug, p2.slug)  # both "widget" -- fine, different stores
        self.assertNotEqual(p1.store_id, p2.store_id)
