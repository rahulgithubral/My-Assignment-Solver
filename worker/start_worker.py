"""
Celery worker startup script for the Assignment Assistant Agent.
Handles background task processing for document processing, plan generation, and execution.
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
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
)

# Import tasks to register them
from app.tasks import (
    process_assignment_document,
    generate_assignment_plan,
    execute_plan,
    cleanup_old_files,
    health_check
)

# Task routing
app.conf.task_routes = {
    'app.tasks.process_assignment_document': {'queue': 'document_processing'},
    'app.tasks.generate_assignment_plan': {'queue': 'planning'},
    'app.tasks.execute_plan': {'queue': 'execution'},
    'app.tasks.cleanup_old_files': {'queue': 'maintenance'},
    'app.tasks.health_check': {'queue': 'monitoring'},
}

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

# Worker configuration
app.conf.worker_hijack_root_logger = False
app.conf.worker_log_color = False

if __name__ == '__main__':
    # Start the worker
    logger.info("Starting Assignment Assistant Agent Celery Worker...")
    logger.info(f"Broker URL: {settings.celery_broker_url}")
    logger.info(f"Result Backend: {settings.celery_result_backend}")
    
    app.start()
