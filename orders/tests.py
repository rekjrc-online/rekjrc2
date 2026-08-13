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
        variant = ProductVariant.objects.create(product=product, name="Default", sku="UK-100")
        order = Order.objects.create(store=store, email="jason@example.com", shipping_cost=Decimal("5.00"))
        OrderItem.objects.create(
            order=order, variant=variant, product_name=product.name,
            unit_price=variant.price, quantity=2,
        )
        order.recalculate_totals()
        self.assertEqual(order.subtotal, Decimal("198.00"))
        self.assertEqual(order.total, Decimal("203.00"))
