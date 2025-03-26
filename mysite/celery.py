# # beat_schedule.py

# from celery.schedules import crontab
# from celery_app import app
# from celery import Celery

# app = Celery('tasks')

# app.conf.beat_schedule = {
#     'run-processing-task-every-night': {
#         'task': 'tasks.run_processing_task',
#         'schedule': crontab(minute=0, hour=0),  # Run at midnight
#     },
# }

# app.conf.timezone = 'UTC'

# mysite/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Define the task schedule
# app.conf.beat_schedule = {
#     'scrape-and-process-schemes-every-5-minutes': {
#         'task': 'myapp.tasks.scrape_and_process_schemes',
#         'schedule': crontab(minute='*/5'),  # Run every 5 minutes
#     },
# }

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'check-urls-every-24-hours': {
        'task': 'communityEmpowerment.tasks.check_urls_task',
        'schedule': crontab(minute=0, hour='0'),  #Runs every midnight
    },
}


app.conf.beat_schedule = {
    "send-weekly-email": {
        "task": "your_app.tasks.send_weekly_email",
        "schedule": crontab(day_of_week=0, hour=9, minute=0),  # Every Monday at 9 AM
    },
}
