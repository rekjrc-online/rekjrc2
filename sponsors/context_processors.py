from .models import Sponsor


def sponsors_context(request):
    """Expose all sponsors as `sponsors_list` for templates/panel_right.html,
    which is included from base.html on every page."""
    return {"sponsors_list": Sponsor.objects.order_by("name")}
