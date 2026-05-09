from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("scan/", views.Scan_.as_view(), name="scan"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
]
