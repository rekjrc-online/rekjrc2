from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path("<slug:store_slug>/", views.cart_detail, name="detail"),
    path("<slug:store_slug>/add/", views.add_to_cart, name="add"),
    path("<slug:store_slug>/<uuid:uuid>/update/", views.update_cart_item, name="update"),
    path("<slug:store_slug>/<uuid:uuid>/remove/", views.remove_cart_item, name="remove"),
]
