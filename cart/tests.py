from django.contrib.auth import get_user_model
from django.test import TestCase

from products.models import Product, ProductVariant
from stores.models import Store

from .models import Cart, CartItem

User = get_user_model()


class CartTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email="owner@example.com", password="testpass123")
        self.store = Store.objects.create(
            owner=owner, display_name="RekjRC Device Store", is_storefront_enabled=True)
        self.product = Product.objects.create(store=self.store, name="Crawler Comp Kit", base_price="59.99")
        self.variant = ProductVariant.objects.create(product=self.product, name="Default", sku="CCK-001")

    def test_add_to_cart_via_view(self):
        response = self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 2},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(store=self.store, checked_out=False)
        self.assertEqual(cart.item_count, 2)
        self.assertEqual(cart.subtotal, self.variant.price * 2)

    def test_cart_item_line_total(self):
        cart = Cart.objects.create(store=self.store)
        item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=3)
        self.assertEqual(item.line_total, self.variant.price * 3)
