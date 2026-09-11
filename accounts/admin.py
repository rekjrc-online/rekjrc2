from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Follow, VerificationLog

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

@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    # Read-only everywhere: rows are only ever created by
    # accounts.views.VerifyConfirmView, and VerificationLog.save()/delete()
    # already refuse edits/deletes at the model layer -- these admin
    # permission overrides just keep the admin UI from offering (and
    # erroring on) actions that would never succeed anyway.
    list_display = ("created_at", "verifier_email", "verified_email", "verifier", "verified_user")
    search_fields = ("verifier_email", "verified_email", "verifier_uuid", "verified_uuid")
    readonly_fields = [f.name for f in VerificationLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False