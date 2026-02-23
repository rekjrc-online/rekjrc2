from django.views.generic import TemplateView
from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('<uuid:post_uuid>/', views.PostDetail.as_view(), name='detail'),
    path('create/', views.PostCreateView.as_view(), name='create'),
    path('reply/<uuid:post_uuid>/', views.PostReplyView.as_view(), name='reply'),
    path('like-ajax/<uuid:post_uuid>/', views.toggle_like_ajax, name='ajax_like'),
    path('replies/ajax/<uuid:post_uuid>/', views.PostRepliesAjax.as_view(), name='ajax_replies'),
    path('for/<str:model_name>/<uuid:uuid>/', views.ObjectPostsAjax.as_view(), name='ajax_object_posts'),
]