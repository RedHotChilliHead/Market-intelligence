import os
from django.conf import settings

from celery import Celery

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Market_intelligence.settings')

app = Celery('Market_intelligence', broker=settings.CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автообнаружение задач в приложениях Django
app.autodiscover_tasks()

# Планировщик задач
app.conf.beat_schedule = {
    'delete-expired-secrets-every-hour': {
        'task': 'secretapp.tasks.delete_expired_secrets',
        'schedule': settings.CELERY_SCHEDULE,
    },
}