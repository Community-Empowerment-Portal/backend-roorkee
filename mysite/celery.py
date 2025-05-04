from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    broker_transport_options=settings.CELERY_BROKER_TRANSPORT_OPTIONS,
    result_backend_transport_options=settings.CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS,
    broker_connection_retry_on_startup=True,
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_default_exchange=settings.CELERY_TASK_DEFAULT_EXCHANGE,
    task_default_routing_key=settings.CELERY_TASK_DEFAULT_ROUTING_KEY,
)

app.conf.beat_schedule = {
    '{mysite}check-urls': {
        'task': 'communityEmpowerment.tasks.check_urls_task',
        'schedule': crontab(minute=0, hour='0'),  # Runs every midnight
    },
    "{mysite}send-weekly-email": {
        "task": "communityEmpowerment.tasks.send_weekly_email",
        "schedule": crontab(day_of_week=0, hour=9, minute=0),  # Every Monday at 9 AM
    },
    "{mysite}send-expiry-reminders": {
        "task": "communityEmpowerment.tasks.send_expiry_email_task",
        "schedule": crontab(hour=0, minute=0),  # every day at 12:00 AM
    }
}

app.conf.timezone = 'Asia/Kolkata' 

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
