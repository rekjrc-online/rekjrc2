from django.urls import path
from . import views

app_name = 'swiss'

urlpatterns = [
    path('<uuid:race_uuid>/start/',   views.Start_.as_view(),   name='start'),
    path('<uuid:race_uuid>/swiss/', views.Swiss_.as_view(), name='swiss'),
    path('<uuid:race_uuid>/finish/',  views.Finish_.as_view(),  name='finish'),
]
