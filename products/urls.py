from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    # Owner-only management routes. Kept under manage/ and listed first so
    # they take priority over the public store_slug/slug routes below --
    # note this means a store slugged literally "manage" isn't supported.
    path("manage/<slug:store_slug>/create/", views.ManageCreate.as_view(), name="manage_create"),
    path("manage/<slug:store_slug>/<slug:slug>/edit/", views.ManageUpdate.as_view(), name="manage_edit"),
    path("manage/<slug:store_slug>/<slug:slug>/delete/", views.ManageDelete.as_view(), name="manage_delete"),

    path("manage/<slug:store_slug>/<slug:slug>/variants/", views.ManageVariantList.as_view(), name="manage_variants"),
    path("manage/<slug:store_slug>/<slug:slug>/variants/create/", views.ManageVariantCreate.as_view(), name="manage_variant_create"),
    path("manage/<slug:store_slug>/<slug:slug>/variants/<uuid:variant_uuid>/edit/", views.ManageVariantUpdate.as_view(), name="manage_variant_edit"),
    path("manage/<slug:store_slug>/<slug:slug>/variants/<uuid:variant_uuid>/delete/", views.ManageVariantDelete.as_view(), name="manage_variant_delete"),

    path("manage/<slug:store_slug>/<slug:slug>/images/", views.ManageImageList.as_view(), name="manage_images"),
    path("manage/<slug:store_slug>/<slug:slug>/images/create/", views.ManageImageCreate.as_view(), name="manage_image_create"),
    path("manage/<slug:store_slug>/<slug:slug>/images/<uuid:image_uuid>/edit/", views.ManageImageUpdate.as_view(), name="manage_image_edit"),
    path("manage/<slug:store_slug>/<slug:slug>/images/<uuid:image_uuid>/delete/", views.ManageImageDelete.as_view(), name="manage_image_delete"),

    path("manage/<slug:store_slug>/", views.ManageList.as_view(), name="manage_list"),

    path("<slug:store_slug>/", views.product_list, name="list"),
    path("<slug:store_slug>/<slug:slug>/", views.product_detail, name="detail"),
]
