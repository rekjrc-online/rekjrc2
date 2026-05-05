from django.urls import path
from . import views

app_name = 'races'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
    path("<uuid:uuid>/join/", views.Join_.as_view(), name="join"),
    path("<uuid:uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:uuid>/lock/", views.Lock_.as_view(), name="lock"),
    path("<uuid:uuid>/judge-devices/", views.JudgeDeviceAdd_.as_view(), name="judge-device-add"),
    path("<uuid:uuid>/judge-devices/<int:assignment_id>/remove/", views.JudgeDeviceRemove_.as_view(), name="judge-device-remove"),
]