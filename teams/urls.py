from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("<uuid:uuid>/", views.Detail_.as_view(), name="detail"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<uuid:uuid>/edit/", views.Update_.as_view(), name="edit"),
    path("<uuid:uuid>/delete/", views.Delete_.as_view(), name="delete"),
]