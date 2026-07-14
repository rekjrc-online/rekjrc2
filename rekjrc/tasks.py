from celery import shared_task
from PIL import Image

@shared_task
def resize_avatar(app_label, model_name, pk):
    from django.apps import apps
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=pk)
    if instance.avatar and hasattr(instance.avatar, 'path'):
        try:
            img = Image.open(instance.avatar.path)
            img.thumbnail((300, 300))
            img.save(instance.avatar.path, optimize=True, quality=85)
        except Exception as e:
            print("Avatar resize failed:", e)