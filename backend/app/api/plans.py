"""
Plan API endpoints for managing assignment execution plans.
Handles plan creation, execution, and monitoring.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.database import get_db
from app.models import Plan, PlanCreate, PlanUpdate, ExecutionRequest, ExecutionResponse
from app.models.database_models import Plan as PlanDB, Assignment as AssignmentDB, Task as TaskDB
from app.tasks import execute_plan

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Plan)
async def create_plan(
    plan_create: PlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new execution plan for an assignment."""
    try:
        # Verify assignment exists
        result = await db.execute(
            select(AssignmentDB).where(AssignmentDB.id == plan_create.assignment_id)
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Create plan
        plan = PlanDB(
            assignment_id=plan_create.assignment_id,
            name=plan_create.name,
            description=plan_create.description,
            tasks=[],  # Will be populated by the planner
            status="created"
        )
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        logger.info(f"Plan created: {plan.id}")
        
        return Plan(
            id=plan.id,
            assignment_id=plan.assignment_id,
            name=plan.name,
            description=plan.description,
            tasks=[],
            status=plan.status,
            total_estimated_duration=plan.total_estimated_duration,
            execution_started_at=plan.execution_started_at,
            execution_completed_at=plan.execution_completed_at,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create plan")


@router.get("/", response_model=List[Plan])
async def list_plans(
    assignment_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List plans with optional assignment filtering."""
    try:
        query = select(PlanDB)
        
        if assignment_id:
            query = query.where(PlanDB.assignment_id == assignment_id)
        
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(PlanDB.created_at.desc())
        )
        plans = result.scalars().all()
        
        return [
            Plan(
                id=plan.id,
                assignment_id=plan.assignment_id,
                name=plan.name,
                description=plan.description,
                tasks=[],  # Simplified for list view
                status=plan.status,
                total_estimated_duration=plan.total_estimated_duration,
                execution_started_at=plan.execution_started_at,
                execution_completed_at=plan.execution_completed_at,
                created_at=plan.created_at,
                updated_at=plan.updated_at
            )
            for plan in plans
        ]
        
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to list plans")


@router.get("/{plan_id}", response_model=Plan)
async def get_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific plan by ID with full task details."""
    try:
        result = await db.execute(
            select(PlanDB).where(PlanDB.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get tasks for this plan
        tasks_result = await db.execute(
            select(TaskDB).where(TaskDB.plan_id == plan_id).order_by(TaskDB.created_at)
        )
        tasks = tasks_result.scalars().all()
        
        # Convert tasks to Pydantic models
        task_models = []
        for task in tasks:
            task_models.append({
                "id": task.id,
                "task_type": task.task_type,
                "description": task.description,
                "dependencies": task.dependencies or [],
                "estimated_duration": task.estimated_duration,
                "tool_requirements": task.tool_requirements or [],
                "parameters": task.parameters or {},
                "status": task.status,
                "result": task.result,
                "error_message": task.error_message,
                "started_at": task.started_at,
                "completed_at": task.completed_at
            })
        
        return Plan(
            id=plan.id,
            assignment_id=plan.assignment_id,
            name=plan.name,
            description=plan.description,
            tasks=task_models,
            status=plan.status,
            total_estimated_duration=plan.total_estimated_duration,
            execution_started_at=plan.execution_started_at,
            execution_completed_at=plan.execution_completed_at,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get plan")


@router.put("/{plan_id}", response_model=Plan)
async def update_plan(
    plan_id: UUID,
    plan_update: PlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a plan."""
    try:
        result = await db.execute(
            select(PlanDB).where(PlanDB.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Update fields
        if plan_update.name is not None:
            plan.name = plan_update.name
        if plan_update.description is not None:
            plan.description = plan_update.description
        if plan_update.status is not None:
            plan.status = plan_update.status
        
        await db.commit()
        await db.refresh(plan)
        
        return Plan(
            id=plan.id,
            assignment_id=plan.assignment_id,
            name=plan.name,
            description=plan.description,
            tasks=[],  # Simplified for update response
            status=plan.status,
            total_estimated_duration=plan.total_estimated_duration,
            execution_started_at=plan.execution_started_at,
            execution_completed_at=plan.execution_completed_at,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update plan")


@router.post("/{plan_id}/execute", response_model=ExecutionResponse)
async def execute_plan_endpoint(
    plan_id: UUID,
    execution_request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Execute a plan with the given parameters."""
    try:
        # Verify plan exists
        result = await db.execute(
            select(PlanDB).where(PlanDB.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        if plan.status not in ["created", "validated"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot execute plan with status: {plan.status}"
            )
        
        # Update plan status
        plan.status = "executing"
        await db.commit()
        
        # Queue background task for plan execution
        background_tasks.add_task(
            execute_plan,
            plan_id,
            execution_request.dry_run,
            execution_request.parallel_execution,
            execution_request.max_parallel_tasks
        )
        
        logger.info(f"Plan execution queued: {plan_id}")
        
        return ExecutionResponse(
            execution_id=UUID(),
            plan_id=plan_id,
            status="queued",
            started_at=plan.execution_started_at or plan.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute plan")


@router.get("/{plan_id}/status")
async def get_plan_status(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a plan and its tasks."""
    try:
        result = await db.execute(
            select(PlanDB).where(PlanDB.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get task statuses
        tasks_result = await db.execute(
            select(TaskDB).where(TaskDB.plan_id == plan_id)
        )
        tasks = tasks_result.scalars().all()
        
        task_statuses = {}
        for task in tasks:
            task_statuses[str(task.id)] = {
                "status": task.status,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message
            }
        
        return {
            "plan_id": plan_id,
            "plan_status": plan.status,
            "execution_started_at": plan.execution_started_at,
            "execution_completed_at": plan.execution_completed_at,
            "task_statuses": task_statuses,
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.status == "success"]),
            "failed_tasks": len([t for t in tasks if t.status == "failed"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan status {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get plan status")


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a plan and all its tasks."""
    try:
        result = await db.execute(
            select(PlanDB).where(PlanDB.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Delete plan (cascade will handle tasks)
        await db.delete(plan)
        await db.commit()
        
        logger.info(f"Plan deleted: {plan_id}")
        
        return {"message": "Plan deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete plan")
