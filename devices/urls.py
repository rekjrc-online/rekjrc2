from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path("", views.List_.as_view(), name="list"),
    path("create/", views.Create_.as_view(), name="create"),
    path("<str:mac>/", views.Detail_.as_view(), name="detail"),
    path("<str:mac>/edit/", views.Update_.as_view(), name="edit"),
    path("<str:mac>/delete/", views.Delete_.as_view(), name="delete"),
]
