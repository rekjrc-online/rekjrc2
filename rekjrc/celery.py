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
#
# Build the package list from the Django app registry (AppConfig.name)
# instead of raw INSTALLED_APPS strings. INSTALLED_APPS entries can be
# either a plain app label ("devices") or a dotted AppConfig path
# ("accounts.apps.AccountsConfig") -- passing the dotted form straight to
# autodiscover_tasks() breaks it, since it then tries to import
# "accounts.apps.AccountsConfig.tasks" instead of "accounts.tasks" and
# silently finds nothing. This is exactly what quietly broke
# accounts.tasks.generate_user_qr on 2026-08-29 when INSTALLED_APPS'
# "accounts" entry got changed to the dotted form. AppConfig.name is
# always the plain package path no matter how INSTALLED_APPS spelled it,
# so building the list this way is safe against that happening again for
# any app. Still add 'rekjrc' explicitly alongside it, since that's the
# project package itself, not a registered Django app.
from django.apps import apps as django_apps
app.autodiscover_tasks(lambda: [c.name for c in django_apps.get_app_configs()] + ['rekjrc'])