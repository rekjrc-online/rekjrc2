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
        self.product = Product.objects.create(store=self.store, name="Crawler Comp Kit")
        self.variant = ProductVariant.objects.create(product=self.product, sku="CCK-001", price="59.99")

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

    def test_cart_subtotal_sums_multiple_items(self):
        second_variant = ProductVariant.objects.create(
            product=self.product, name="Black", sku="CCK-002", price="49.99")
        cart = Cart.objects.create(store=self.store)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        CartItem.objects.create(cart=cart, variant=second_variant, quantity=3)
        expected = (self.variant.price * 2) + (second_variant.price * 3)
        self.assertEqual(cart.subtotal, expected)

    def test_cart_item_count_sums_across_items(self):
        second_variant = ProductVariant.objects.create(
            product=self.product, name="Black", sku="CCK-003", price="49.99")
        cart = Cart.objects.create(store=self.store)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        CartItem.objects.create(cart=cart, variant=second_variant, quantity=5)
        self.assertEqual(cart.item_count, 7)

    def test_add_to_cart_twice_accumulates_quantity_not_duplicate_row(self):
        # CartItem has unique_together = ("cart", "variant") -- adding the
        # same variant twice should accumulate quantity on one row (per
        # cart/views.add_to_cart's get_or_create + increment), not raise or
        # create a second row.
        self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 2},
            follow=True,
        )
        self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 3},
            follow=True,
        )
        cart = Cart.objects.get(store=self.store, checked_out=False)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.get(variant=self.variant).quantity, 5)

    def test_add_to_cart_inactive_variant_returns_404(self):
        self.variant.is_active = False
        self.variant.save()
        response = self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 1},
        )
        self.assertEqual(response.status_code, 404)

    def test_cart_str_shows_checked_out_suffix(self):
        checked_out_cart = Cart.objects.create(store=self.store, checked_out=True)
        self.assertIn("[checked out]", str(checked_out_cart))
        open_cart = Cart.objects.create(store=self.store, session_key="abc123")
        self.assertNotIn("[checked out]", str(open_cart))

    def test_update_cart_item_changes_quantity(self):
        self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 1},
        )
        cart = Cart.objects.get(store=self.store, checked_out=False)
        item = cart.items.get(variant=self.variant)
        self.client.post(f"/cart/{self.store.slug}/{item.uuid}/update/", {"quantity": 5})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_update_cart_item_deletes_when_quantity_zero_or_less(self):
        self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 2},
        )
        cart = Cart.objects.get(store=self.store, checked_out=False)
        item = cart.items.get(variant=self.variant)
        self.client.post(f"/cart/{self.store.slug}/{item.uuid}/update/", {"quantity": 0})
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_remove_cart_item_deletes_item(self):
        self.client.post(
            f"/cart/{self.store.slug}/add/",
            {"variant_uuid": str(self.variant.uuid), "quantity": 2},
        )
        cart = Cart.objects.get(store=self.store, checked_out=False)
        item = cart.items.get(variant=self.variant)
        self.client.post(f"/cart/{self.store.slug}/{item.uuid}/remove/")
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())


class GetOrCreateCartUtilTests(TestCase):
    """
    cart.utils.get_or_create_cart is exercised indirectly here via
    cart_detail, rather than called directly, since it needs a real
    request (user/session) to branch on.
    """
    def setUp(self):
        owner = User.objects.create_user(email="utilstoreowner@example.com", password="testpass123")
        self.store = Store.objects.create(
            owner=owner, display_name="Utility Test Store", is_storefront_enabled=True)

    def test_authenticated_user_reuses_same_open_cart(self):
        customer = User.objects.create_user(email="customer@example.com", password="testpass123")
        self.client.force_login(customer)
        self.client.get(f"/cart/{self.store.slug}/")
        self.client.get(f"/cart/{self.store.slug}/")
        self.assertEqual(
            Cart.objects.filter(store=self.store, user=customer, checked_out=False).count(), 1)

    def test_anonymous_visitor_reuses_same_session_cart(self):
        self.client.get(f"/cart/{self.store.slug}/")
        self.client.get(f"/cart/{self.store.slug}/")
        self.assertEqual(
            Cart.objects.filter(store=self.store, user__isnull=True, checked_out=False).count(), 1)

    def test_different_stores_get_separate_carts_for_same_user(self):
        other_owner = User.objects.create_user(email="otherstoreowner@example.com", password="testpass123")
        other_store = Store.objects.create(
            owner=other_owner, display_name="Second Store", is_storefront_enabled=True)
        customer = User.objects.create_user(email="customer2@example.com", password="testpass123")
        self.client.force_login(customer)
        self.client.get(f"/cart/{self.store.slug}/")
        self.client.get(f"/cart/{other_store.slug}/")
        self.assertEqual(Cart.objects.filter(user=customer, checked_out=False).count(), 2)
