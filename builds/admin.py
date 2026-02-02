from django.contrib import admin
from .models import Build

@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner", "year", "make", "model")
    search_fields = ("display_name", "owner__username", "make", "model")
    list_filter = ("year", "make")
    ordering = ("display_name",)

    # Group all the component fields into a collapsible fieldset
    fieldsets = (
        (None, {
            "fields": ("display_name", "owner", "year", "make", "model", "avatar")
        }),
        ("Components", {
            "classes": ("collapse",),
            "fields": tuple([
                "bearings","body","bumper_front","bumper_rear","camber_links","caster_blocks",
                "chassis","control_arms","cooling","driveshafts","esc","esc_motor","fuel",
                "lights","motor","radio_system","rear_steer","rims","scale","sensor","servo",
                "shocks","shocks_front","shocks_rear","transmission","wheel_hubs","wheels",
                "wheels_front","wheels_rear"
            ]),
        }),
    )
