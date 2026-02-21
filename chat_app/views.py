from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import TemplateView

from chat_app.models import ChatMessage

from builds.models import Build
from clubs.models import Club
from drivers.models import Driver
from events.models import Event
from locations.models import Location
from races.models import Race
from stores.models import Store
from teams.models import Team
from tracks.models import Track
from django.utils import timezone
from datetime import timedelta

CHAT_MODELS = {
    "build": Build,
    "club": Club,
    "driver": Driver,
    "event": Event,
    "location": Location,
    "race": Race,
    "store": Store,
    "team": Team,
    "track": Track,
}


def resolve_channel(model_type, object_uuid):
    model = CHAT_MODELS.get(model_type)
    if not model:
        raise Http404("Invalid channel")

    obj = get_object_or_404(
        model,
        uuid=object_uuid,
        is_active=True,
        enable_chat=True,
    )

    return obj, ContentType.objects.get_for_model(model)


class ChatRoomView(LoginRequiredMixin, TemplateView):
    template_name = "chat/room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj, ct = resolve_channel(
            self.kwargs["model_type"],
            self.kwargs["object_uuid"],
        )

        messages = (
            ChatMessage.objects
            .filter(
                channel_content_type=ct,
                channel_object_id=obj.pk,
                created_at__gte=timezone.now() - timedelta(hours=1),
            ).order_by("created_at")[:50]
        )

        context.update({
            "channel": obj,
            "channel_type": self.kwargs["model_type"],
            "messages": messages,
        })

        return context


class ChatMessagesView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        obj, ct = resolve_channel(
            kwargs["model_type"],
            kwargs["object_uuid"],
        )

        qs = (
            ChatMessage.objects
            .filter(
                channel_content_type=ct,
                channel_object_id=obj.pk,
                created_at__gte=timezone.now() - timedelta(hours=1),
            ).order_by("created_at")
        )

        after = request.GET.get("after")
        if after:
            dt = parse_datetime(after)
            if dt:
                qs = qs.filter(created_at__gt=dt)

        return JsonResponse(
            [
                {
                    "username": m.user.get_full_name() or m.user.username,
                    "message": m.content,
                    "created_at": m.created_at.isoformat(),
                    "is_you": m.user_id == request.user.id,
                }
                for m in qs
            ],
            safe=False,
        )


class ChatSendView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        obj, ct = resolve_channel(
            kwargs["model_type"],
            kwargs["object_uuid"],
        )

        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Empty message"}, status=400)

        msg = ChatMessage.objects.create(
            user=request.user,
            channel_object_id=obj.pk,
            channel_content_type=ct,
            content=content,
        )

        return JsonResponse({
            "username": msg.user.get_full_name() or msg.user.username,
            "message": msg.content,
            "created_at": msg.created_at.isoformat(),
        })
