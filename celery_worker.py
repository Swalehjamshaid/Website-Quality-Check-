# celery_worker.py - Defines the schedule for Daily Audits and Reports

# CRITICAL: This file must be in your repository root, 
# and it is used by the 'report-beat' service defined in render.yaml

from app import celery_app
from celery.schedules import crontab

# Define when Celery Beat should run the tasks
celery_app.conf.beat_schedule = {
    # Task 1: Daily Monitoring (Triggers the function that queues all individual audits)
    # This task calls app.daily_audit_all, which then uses app.audit_website.delay()
    'run-daily-system-audits': {
        'task': 'app.daily_audit_all',
        'schedule': crontab(hour=2, minute=0), # Daily at 02:00 AM UTC
    },
    # Task 2: Scheduled Report Sending (Checks user schedules every 5 minutes)
    # This task calls app.send_scheduled_reports, which contains the scheduling logic.
    'check-user-report-schedules': {
        'task': 'app.send_scheduled_reports',
        'schedule': crontab(minute='*/5'), 
    },
}
