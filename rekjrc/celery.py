import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rekjrc.settings')

app = Celery('rekjrc')
app.config_from_object('django.conf:settings', namespace='CELERY')

# autodiscover_tasks() with no args only scans INSTALLED_APPS for a
# tasks.py in each -- but rekjrc/tasks.py (resize_avatar,
# resize_product_thumbnail) lives in the project package itself, which
# isn't in INSTALLED_APPS, so it was never being found (confirmed
# 2026-08-07: worker startup only listed accounts.tasks.generate_user_qr,
# and resize_avatar calls were silently discarded as "unregistered").
# Add 'rekjrc' explicitly alongside the normal per-app task modules.
from django.conf import settings
app.autodiscover_tasks(lambda: list(settings.INSTALLED_APPS) + ['rekjrc'])