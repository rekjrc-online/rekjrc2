from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path("<slug:store_slug>/checkout/", views.checkout, name="checkout"),
    path("<slug:store_slug>/<uuid:uuid>/", views.confirmation, name="confirmation"),
]
