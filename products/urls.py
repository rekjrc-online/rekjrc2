from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path("<slug:store_slug>/", views.product_list, name="list"),
    path("<slug:store_slug>/<slug:slug>/", views.product_detail, name="detail"),
]
