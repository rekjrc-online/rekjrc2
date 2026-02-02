from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("<str:model_type>/<uuid:object_uuid>/",views.ChatRoomView.as_view(),name="room",),
    path("<str:model_type>/<uuid:object_uuid>/messages/",views.ChatMessagesView.as_view(),name="messages",),
    path("<str:model_type>/<uuid:object_uuid>/send/",views.ChatSendView.as_view(),name="send",),
]
