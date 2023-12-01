from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'images_api.settings')

# Create a Celery instance
app = Celery('images_api')

# Using a string here means the worker doesn't have to serialize the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Example: Define additional Celery configuration settings
# app.conf.update(
#     task_serializer='json',
#     result_serializer='json',
#     accept_content=['json'],
#     timezone='UTC',
# )

# Optional: Configure periodic tasks (beat schedule)
# app.conf.beat_schedule = {
#     'my_periodic_task': {
#         'task': 'myapp.tasks.my_periodic_task',
#         'schedule': 300,  # Every 5 minutes
#     },
# }

# Optional: Define the queue or routing configurations
# app.conf.task_queues = (
#     Queue('default', routing_key='task.default'),
#     Queue('priority', routing_key='task.priority'),
# )

if __name__ == '__main__':
    app.start()