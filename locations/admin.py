from django.contrib import admin
from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [
        field.name for field in Location._meta.fields
            if field.name not in ("uuid", "avatar", "updated_at", "allow_followers", "created_at", "address2", "zip", "latitude", "longitude")
    ]
    readonly_fields = [
        field.name for field in Location._meta.fields
            if field.name in ("uuid", "created_at", "updated_at")
    ]
    list_filter = [
        field.name for field in Location._meta.fields
            if field.get_internal_type() in ("ForeignKey", "BooleanField", "CharField")
            and field.name not in ("address1", "address2", "city", "state", "zip")
    ]
    search_fields = [
        field.name for field in Location._meta.fields
            if field.get_internal_type() in ("CharField", "TextField")
    ]
    ordering = [
        f.name for f in Location._meta.fields
            if f.name != "id"
    ][:1]
