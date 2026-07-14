from celery import shared_task

@shared_task
def generate_user_qr(user_id):
    from .models import User
    user = User.objects.get(pk=user_id)
    user._generate_qr()