from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
    path("<uuid:uuid>/advanced/", views.Advanced_.as_view(), name="advanced"),
    path("<uuid:uuid>/track/add/", views.LocationTrackAdd_.as_view(), name="track-add"),
    path("<uuid:uuid>/track/<int:pk>/remove/", views.LocationTrackRemove_.as_view(), name="track-remove"),
]