from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Sponsor, SponsorClick


# csrf_exempt: this only appends a click-log row, and anonymous visitors may
# not have a csrftoken cookie yet, which would otherwise 403 every logo click.
@method_decorator(csrf_exempt, name="dispatch")
class SponsorClickView(View):
    http_method_names = ["post"]

    def post(self, request, sponsor_id):
        sponsor = get_object_or_404(Sponsor, pk=sponsor_id)
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
        SponsorClick.objects.create(
            sponsor=sponsor,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip or None,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return JsonResponse({"ok": True, "redirect_url": sponsor.website})
