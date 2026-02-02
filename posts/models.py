from tkinter import Image
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from rekjrc.base_models import BaseModel
import re

class Post(BaseModel):
    author_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="post_authors")
    author_object_id = models.PositiveIntegerField()
    author = GenericForeignKey("author_content_type", "author_object_id")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField(max_length=200)
    display_content = models.TextField(max_length=1000, blank=True, null=True)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)

    @property
    def posted_date_delta(self):
        now = timezone.now()
        delta = now - self.created_at
        seconds = delta.total_seconds()
        minutes = seconds // 60
        hours = seconds // 3600
        days = seconds // 86400
        weeks = seconds // (86400 * 7)
        months = seconds // (86400 * 30)
        years = seconds // (86400 * 365)
        if seconds < 60:
            return "just now"
        elif minutes < 60:
            return f"{int(minutes)}m"
        elif hours < 24:
            return f"{int(hours)}h"
        elif days < 7:
            return f"{int(days)}d"
        elif weeks < 5:
            return f"{int(weeks)}w"
        elif months < 12:
            return f"{int(months)}mo"
        else:
            return f"{int(years)}y"

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def replies_count(self):
        return self.replies.count()

    class Meta:
        indexes = [models.Index(fields=['created_at'])]

    def get_absolute_url(self):
        return reverse("posts:detail", kwargs={"post_uuid": self.uuid})

    def __str__(self):
        return f"{self.content[:50]}"

    def save(self, *args, **kwargs):
        if self.content:
            self.content = strip_html(self.content)
        self.display_content = make_clickable_urls(self.content or "")
        super().save(*args, **kwargs)
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)
            max_size = (1024, 1024)
            img.thumbnail(max_size)
            img.save(img_path, optimize=True, quality=85)

class PostLike(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"],
                name="unique_post_like"
            )
        ]

HTML_TAG_REGEX = re.compile(r'<[^>]+>')
def strip_html(text):
    return HTML_TAG_REGEX.sub('', text)

URL_REGEX = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)
def make_clickable_urls(text):
    def repl(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" onclick="event.stopPropagation();" rel="noopener noreferrer">{url}</a>'
    return URL_REGEX.sub(repl, text)
