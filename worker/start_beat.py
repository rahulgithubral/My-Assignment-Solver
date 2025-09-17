"""
Celery Beat scheduler startup script for the Assignment Assistant Agent.
Handles periodic task scheduling.
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from celery import Celery
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery('assignment_agent')

# Configure Celery
app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Import tasks to register them
from app.tasks import (
    cleanup_old_files,
    health_check
)

# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'app.tasks.cleanup_old_files',
        'schedule': 3600.0,  # Run every hour
    },
    'health-check': {
        'task': 'app.tasks.health_check',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

# Beat configuration
app.conf.beat_scheduler = 'celery.beat:PersistentScheduler'
app.conf.beat_schedule_filename = '/tmp/celerybeat-schedule'

if __name__ == '__main__':
    # Start the beat scheduler
    logger.info("Starting Assignment Assistant Agent Celery Beat Scheduler...")
    logger.info(f"Broker URL: {settings.celery_broker_url}")
    
    app.start()
