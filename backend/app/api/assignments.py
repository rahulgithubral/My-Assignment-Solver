"""
Assignment API endpoints for file upload, management, and processing.
Handles assignment lifecycle from upload to completion.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import aiofiles
import os
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models import Assignment, AssignmentCreate, AssignmentUpdate, FileUploadResponse
from app.models.database_models import Assignment as AssignmentDB, User
from app.tasks import process_assignment_document, generate_assignment_plan

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_assignment_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload an assignment file and create assignment record."""
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_extension}' not allowed. Allowed types: {settings.allowed_file_types}"
            )
        
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_id = UUID()
        filename = f"{file_id}_{file.filename}"
        file_path = upload_dir / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Create assignment record (for demo, use a default user)
        # In production, this would come from authentication
        user_result = await db.execute(select(User).limit(1))
        user = user_result.scalar_one_or_none()
        
        if not user:
            # Create default user for demo
            user = User(email="demo@example.com", name="Demo User")
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        assignment = AssignmentDB(
            user_id=user.id,
            title=Path(file.filename).stem,
            file_path=str(file_path),
            file_size=len(file_content),
            file_type=file_extension,
            status="uploaded"
        )
        
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        
        # Queue background task for document processing
        background_tasks.add_task(process_assignment_document, assignment.id)
        
        logger.info(f"Assignment file uploaded: {assignment.id}")
        
        return FileUploadResponse(
            file_id=assignment.id,
            filename=file.filename,
            file_size=len(file_content),
            file_type=file_extension,
            upload_path=str(file_path)
        )
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.get("/", response_model=List[Assignment])
async def list_assignments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all assignments with pagination."""
    try:
        result = await db.execute(
            select(AssignmentDB)
            .offset(skip)
            .limit(limit)
            .order_by(AssignmentDB.created_at.desc())
        )
        assignments = result.scalars().all()
        
        return [
            Assignment(
                id=assignment.id,
                user_id=assignment.user_id,
                title=assignment.title,
                description=assignment.description,
                file_path=assignment.file_path,
                status=assignment.status,
                file_size=assignment.file_size,
                file_type=assignment.file_type,
                created_at=assignment.created_at,
                updated_at=assignment.updated_at
            )
            for assignment in assignments
        ]
        
    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list assignments")


@router.get("/{assignment_id}", response_model=Assignment)
async def get_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assignment by ID."""
    try:
        result = await db.execute(
            select(AssignmentDB).where(AssignmentDB.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return Assignment(
            id=assignment.id,
            user_id=assignment.user_id,
            title=assignment.title,
            description=assignment.description,
            file_path=assignment.file_path,
            status=assignment.status,
            file_size=assignment.file_size,
            file_type=assignment.file_type,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get assignment")


@router.post("/{assignment_id}/plan", response_model=dict)
async def generate_plan(
    assignment_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate a plan for the assignment."""
    try:
        # Verify assignment exists
        result = await db.execute(
            select(AssignmentDB).where(AssignmentDB.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        if assignment.status not in ["uploaded", "processing"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot generate plan for assignment with status: {assignment.status}"
            )
        
        # Update assignment status
        assignment.status = "processing"
        await db.commit()
        
        # Queue background task for plan generation
        background_tasks.add_task(generate_assignment_plan, assignment_id)
        
        logger.info(f"Plan generation queued for assignment: {assignment_id}")
        
        return {
            "message": "Plan generation started",
            "assignment_id": assignment_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating plan for assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plan")


@router.put("/{assignment_id}", response_model=Assignment)
async def update_assignment(
    assignment_id: UUID,
    assignment_update: AssignmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an assignment."""
    try:
        result = await db.execute(
            select(AssignmentDB).where(AssignmentDB.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Update fields
        if assignment_update.title is not None:
            assignment.title = assignment_update.title
        if assignment_update.description is not None:
            assignment.description = assignment_update.description
        if assignment_update.status is not None:
            assignment.status = assignment_update.status
        
        await db.commit()
        await db.refresh(assignment)
        
        return Assignment(
            id=assignment.id,
            user_id=assignment.user_id,
            title=assignment.title,
            description=assignment.description,
            file_path=assignment.file_path,
            status=assignment.status,
            file_size=assignment.file_size,
            file_type=assignment.file_type,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assignment")


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an assignment and its associated files."""
    try:
        result = await db.execute(
            select(AssignmentDB).where(AssignmentDB.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Delete associated file if it exists
        if assignment.file_path and os.path.exists(assignment.file_path):
            os.remove(assignment.file_path)
        
        # Delete from database (cascade will handle related records)
        await db.delete(assignment)
        await db.commit()
        
        logger.info(f"Assignment deleted: {assignment_id}")
        
        return {"message": "Assignment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete assignment")
