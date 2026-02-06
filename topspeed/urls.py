from django.urls import path
from . import views

app_name = 'topspeed'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/race/<uuid:racedriver_uuid>", views.Race_.as_view(), name="race"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
]