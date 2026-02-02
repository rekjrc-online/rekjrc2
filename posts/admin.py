from django.contrib import admin
from .models import Post, PostLike

class PostLikeInline(admin.TabularInline):
    model = PostLike
    extra = 0
    readonly_fields = ("user",)
    can_delete = False

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("short_content", "created_at", "parent_display")
    search_fields = ("content",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    inlines = [PostLikeInline]

    def short_content(self, obj):
        return obj.content[:50] if obj.content else "-"
    short_content.short_description = "Content"

    def parent_display(self, obj):
        return str(obj.parent) if obj.parent else "-"
    parent_display.short_description = "Parent Post"

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("post_display", "user")
    search_fields = ("post__content", "user__username")
    list_filter = ("post", "user")
    ordering = ("-post__created_at",)

    def post_display(self, obj):
        return str(obj.post)
    post_display.short_description = "Post"
