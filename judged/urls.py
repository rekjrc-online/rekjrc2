from django.urls import path
from . import views

app_name = 'judged'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/judge/<int:racedriver_id>", views.Judge_.as_view(), name="judge"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
]