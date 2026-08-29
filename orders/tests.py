from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from products.models import Product, ProductVariant
from stores.models import Store

from .models import Order, OrderItem

User = get_user_model()


class OrderTotalsTests(TestCase):
    def test_recalculate_totals(self):
        owner = User.objects.create_user(email="owner@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="RekjRC Device Store")
        product = Product.objects.create(store=store, name="Universal Keypad", base_price="99.00")
        # Product.save() already auto-creates a "Default" variant -- reuse it
        # instead of creating a second one, which would collide on the
        # (product, name) unique constraint.
        variant = product.variants.get()
        variant.sku = "UK-100"
        variant.save()
        order = Order.objects.create(store=store, email="jason@example.com", shipping_cost=Decimal("5.00"))
        OrderItem.objects.create(
            order=order, variant=variant, product_name=product.name,
            unit_price=variant.price, quantity=2,
        )
        order.recalculate_totals()
        self.assertEqual(order.subtotal, Decimal("198.00"))
        self.assertEqual(order.total, Decimal("203.00"))

    def test_recalculate_totals_with_multiple_items(self):
        owner = User.objects.create_user(email="owner2@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="RekjRC Device Store 2")
        product = Product.objects.create(store=store, name="Universal Keypad", base_price="99.00")
        variant = product.variants.get()
        variant.sku = "UK-200"
        variant.save()
        second_product = Product.objects.create(store=store, name="Crawler Comp Kit", base_price="59.99")
        second_variant = second_product.variants.get()
        second_variant.sku = "CCK-200"
        second_variant.save()

        order = Order.objects.create(store=store, email="jason@example.com", shipping_cost=Decimal("10.00"))
        OrderItem.objects.create(
            order=order, variant=variant, product_name=product.name,
            unit_price=variant.price, quantity=1,
        )
        OrderItem.objects.create(
            order=order, variant=second_variant, product_name=second_product.name,
            unit_price=second_variant.price, quantity=2,
        )
        order.recalculate_totals()
        self.assertEqual(order.subtotal, Decimal("218.98"))  # 99.00 + 2 * 59.99
        self.assertEqual(order.total, Decimal("228.98"))

    def test_recalculate_totals_with_no_items_is_just_shipping(self):
        owner = User.objects.create_user(email="owner3@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="Empty Order Store")
        order = Order.objects.create(store=store, email="jason@example.com", shipping_cost=Decimal("7.50"))
        order.recalculate_totals()
        self.assertEqual(order.subtotal, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("7.50"))

    def test_order_item_line_total(self):
        owner = User.objects.create_user(email="owner4@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="Line Total Store")
        product = Product.objects.create(store=store, name="Drag Race Kit", base_price="25.00")
        variant = product.variants.get()
        variant.sku = "DR-100"
        variant.save()
        order = Order.objects.create(store=store, email="jason@example.com")
        item = OrderItem.objects.create(
            order=order, variant=variant, product_name=product.name,
            unit_price=variant.price, quantity=4,
        )
        self.assertEqual(item.line_total, Decimal("100.00"))

    def test_order_default_status_is_pending(self):
        owner = User.objects.create_user(email="owner5@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="Status Store")
        order = Order.objects.create(store=store, email="jason@example.com")
        self.assertEqual(order.status, Order.STATUS_PENDING)

    def test_order_str_includes_uuid_email_and_status(self):
        owner = User.objects.create_user(email="owner6@example.com", password="testpass123")
        store = Store.objects.create(owner=owner, display_name="Str Store")
        order = Order.objects.create(store=store, email="buyer@example.com")
        s = str(order)
        self.assertIn(str(order.uuid), s)
        self.assertIn("buyer@example.com", s)
        self.assertIn("pending", s)

    def test_get_absolute_url_falls_back_when_store_is_none(self):
        # Order.store is SET_NULL, so an order can outlive a deleted store --
        # get_absolute_url() should still produce a usable URL instead of
        # raising, using the literal "store" slug placeholder.
        order = Order.objects.create(store=None, email="jason@example.com")
        url = order.get_absolute_url()
        self.assertIn("/store/", url)
        self.assertIn(str(order.uuid), url)
