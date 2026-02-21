from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import UserProfile, Follow

User = get_user_model()

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "sms_opt_in", "is_verified",)
    search_fields = ("user__email", "phone_number")

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "object", "created_at")
    search_fields = ("follower__email",)