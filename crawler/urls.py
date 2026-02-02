from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path("<uuid:race_uuid>/start/", views.Start_.as_view(), name="start"),
    path("<uuid:race_uuid>/crawl/<uuid:racedriver_uuid>", views.Crawl_.as_view(), name="crawl"),
    path("<uuid:race_uuid>/finish/", views.Finish_.as_view(), name="finish"),
]