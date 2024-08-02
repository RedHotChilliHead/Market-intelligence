from celery import shared_task
from .models import Secret
from django.utils import timezone


# задача по удалению секретов, у которых кончился срок жизни
@shared_task()
def delete_expired_secrets():
    Secret.objects.filter(expires_at__lt=timezone.now()).delete()
