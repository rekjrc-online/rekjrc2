from django.shortcuts import render, get_object_or_404

from stores.models import Store

from .models import Product


def product_list(request, store_slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    products = Product.objects.filter(store=store, is_active=True).prefetch_related("images", "variants")
    return render(request, "products/list.html", {"store": store, "products": products})


def product_detail(request, store_slug, slug):
    store = get_object_or_404(Store, slug=store_slug, is_storefront_enabled=True)
    product = get_object_or_404(
        Product.objects.prefetch_related("images", "variants"),
        store=store,
        slug=slug,
        is_active=True,
    )
    return render(request, "products/detail.html", {"store": store, "product": product})
