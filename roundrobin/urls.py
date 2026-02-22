from django.urls import path
from . import views

app_name = 'roundrobin'

urlpatterns = [
    path('<uuid:race_uuid>/start/',      views.Start_.as_view(),      name='start'),
    path('<uuid:race_uuid>/roundrobin/', views.RoundRobin_.as_view(), name='roundrobin'),
    path('<uuid:race_uuid>/finish/',     views.Finish_.as_view(),     name='finish'),
]
