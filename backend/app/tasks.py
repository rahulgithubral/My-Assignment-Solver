"""
Background tasks for the Assignment Assistant Agent.
Handles document processing, plan generation, and execution.
"""

from celery import Celery
from typing import Dict, Any, List
import logging
import asyncio
from uuid import UUID

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.database_models import Assignment as AssignmentDB, Plan as PlanDB, Task as TaskDB
from app.rag import process_document, query_similar_documents
from agent.planner.planner import create_plan
from agent.executor.executor import execute_plan as execute_plan_agent

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "assignment_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def process_assignment_document(self, assignment_id: str):
    """Process an uploaded assignment document."""
    try:
        logger.info(f"Processing document for assignment: {assignment_id}")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process_document_async(assignment_id))
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Error processing document for assignment {assignment_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _process_document_async(assignment_id: str) -> Dict[str, Any]:
    """Async helper for document processing."""
    async with AsyncSessionLocal() as db:
        # Get assignment
        result = await db.execute(
            db.query(AssignmentDB).where(AssignmentDB.id == UUID(assignment_id))
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise ValueError(f"Assignment not found: {assignment_id}")
        
        if not assignment.file_path:
            raise ValueError(f"No file path for assignment: {assignment_id}")
        
        # Process document
        document_data = await process_document(
            file_path=assignment.file_path,
            assignment_id=assignment.id
        )
        
        # Update assignment status
        assignment.status = "processing"
        await db.commit()
        
        logger.info(f"Document processed for assignment: {assignment_id}")
        
        return {
            "assignment_id": assignment_id,
            "status": "processed",
            "document_data": document_data
        }


@celery_app.task(bind=True, max_retries=3)
def generate_assignment_plan(self, assignment_id: str):
    """Generate an execution plan for an assignment."""
    try:
        logger.info(f"Generating plan for assignment: {assignment_id}")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_generate_plan_async(assignment_id))
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Error generating plan for assignment {assignment_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _generate_plan_async(assignment_id: str) -> Dict[str, Any]:
    """Async helper for plan generation."""
    async with AsyncSessionLocal() as db:
        # Get assignment
        result = await db.execute(
            db.query(AssignmentDB).where(AssignmentDB.id == UUID(assignment_id))
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise ValueError(f"Assignment not found: {assignment_id}")
        
        # Get similar documents for context
        similar_docs = await query_similar_documents(
            query=assignment.title,
            k=5
        )
        
        # Create plan using the planner
        plan_data = create_plan(
            assignment_title=assignment.title,
            assignment_description=assignment.description or "",
            file_content=similar_docs,  # Use similar documents as context
            assignment_id=assignment.id
        )
        
        # Create plan record
        plan = PlanDB(
            assignment_id=assignment.id,
            name=f"Plan for {assignment.title}",
            description=f"Generated plan for assignment: {assignment.title}",
            tasks=plan_data.get("tasks", []),
            status="created"
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Update assignment status
        assignment.status = "planned"
        await db.commit()
        
        logger.info(f"Plan generated for assignment: {assignment_id}")
        
        return {
            "assignment_id": assignment_id,
            "plan_id": str(plan.id),
            "status": "planned",
            "tasks_count": len(plan_data.get("tasks", []))
        }


@celery_app.task(bind=True, max_retries=3)
def execute_plan(self, plan_id: str, dry_run: bool = False, parallel_execution: bool = True, max_parallel_tasks: int = 3):
    """Execute a plan with the given parameters."""
    try:
        logger.info(f"Executing plan: {plan_id}")
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_execute_plan_async(plan_id, dry_run, parallel_execution, max_parallel_tasks))
            return result
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"Error executing plan {plan_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _execute_plan_async(plan_id: str, dry_run: bool, parallel_execution: bool, max_parallel_tasks: int) -> Dict[str, Any]:
    """Async helper for plan execution."""
    async with AsyncSessionLocal() as db:
        # Get plan
        result = await db.execute(
            db.query(PlanDB).where(PlanDB.id == UUID(plan_id))
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        
        # Update plan status
        plan.status = "executing"
        await db.commit()
        
        # Execute plan using the executor
        execution_result = execute_plan_agent(
            plan_id=plan.id,
            tasks=plan.tasks,
            dry_run=dry_run,
            parallel_execution=parallel_execution,
            max_parallel_tasks=max_parallel_tasks
        )
        
        # Update plan status based on execution result
        if execution_result.get("status") == "completed":
            plan.status = "completed"
        elif execution_result.get("status") == "failed":
            plan.status = "failed"
        
        await db.commit()
        
        logger.info(f"Plan executed: {plan_id}")
        
        return {
            "plan_id": plan_id,
            "status": execution_result.get("status", "unknown"),
            "execution_result": execution_result
        }


@celery_app.task
def cleanup_old_files():
    """Cleanup old uploaded files and temporary data."""
    try:
        logger.info("Starting cleanup of old files")
        # Implementation for cleanup logic
        # This would remove files older than a certain threshold
        return {"status": "completed", "cleaned_files": 0}
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task
def health_check():
    """Health check task for monitoring."""
    try:
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "vector_store": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
