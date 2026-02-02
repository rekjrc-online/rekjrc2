from django.urls import path
from . import views

app_name = 'dragrace'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/dragrace/", views.DragRace_.as_view(), name="dragrace"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
]