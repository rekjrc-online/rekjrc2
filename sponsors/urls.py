from django.urls import path
from . import views

app_name = 'sponsors'

urlpatterns = [
    path('<int:sponsor_id>/click/', views.SponsorClickView.as_view(), name='sponsor_click'),
]
