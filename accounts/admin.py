from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Follow

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff", "is_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("uuid", "phone_number", "is_verified", "sms_opt_in")}),
    )
    readonly_fields = ("uuid",)

admin.site.register(User, UserAdmin)

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "object", "created_at")
    search_fields = ("follower__email",)