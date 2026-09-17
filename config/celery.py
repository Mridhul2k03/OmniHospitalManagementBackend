"""
Celery configuration for Hospitality Management Operating System (HMOS).
"""
import os
from celery import Celery

# Set default Django settings module for celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('omni_hospitality')

# Load configuration from Django settings, namespace='CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks across all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
