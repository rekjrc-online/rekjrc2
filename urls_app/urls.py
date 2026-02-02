# urls_app/urls.py

from django.urls import path
from .views import short_url_redirect

app_name = "urls_app"

urlpatterns = [
    path('<str:code>/', short_url_redirect, name='short_redirect'),
]
