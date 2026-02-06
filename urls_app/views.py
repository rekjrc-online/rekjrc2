from django.shortcuts import redirect
from .models import ShortURL
from django.shortcuts import get_object_or_404

def short_url_redirect(request, code):
    lookup=get_object_or_404(ShortURL, code=code, is_active=True)
    lookup.click_count += 1
    lookup.save()
    return redirect(lookup.destination_url, permanent=False)