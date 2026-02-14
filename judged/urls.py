from django.urls import path
from . import views

app_name = 'judged'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/race/<uuid:racedriver_uuid>", views.Race_.as_view(), name="race"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
    path("<uuid:race_uuid>/judge/add/", views.JudgeAdd.as_view(), name="judge_add"),
    path("<uuid:race_uuid>/judge/<uuid:judge_uuid>/remove/", views.JudgeRemove.as_view(), name="judge_remove"),
]