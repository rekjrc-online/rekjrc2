from django.urls import path
from . import views

app_name = 'dragdouble'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/dragdouble/", views.DragDouble_.as_view(), name="dragdouble"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
]