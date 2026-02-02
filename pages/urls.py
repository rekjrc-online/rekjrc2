from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('privacy', views.PrivacyView.as_view(), name='privacy'),
    path('terms-of-service', views.TermsView.as_view(), name='terms'),
    path('crawler_comp', views.PrivacyViewCrawlercomp.as_view(), name='crawler_comp'),
    path('support', views.SupportView.as_view(), name='support'),
]
