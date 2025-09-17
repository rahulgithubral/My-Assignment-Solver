"""
Pydantic models for the Assignment Assistant Agent API.
Defines request/response schemas and data validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssignmentStatus(str, Enum):
    """Assignment processing status enumeration."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PLANNED = "planned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanStatus(str, Enum):
    """Plan status enumeration."""
    CREATED = "created"
    VALIDATED = "validated"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


# Base models
class BaseResponse(BaseModel):
    """Base response model with common fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# Assignment models
class AssignmentBase(BaseModel):
    """Base assignment model."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Assignment creation request model."""
    pass


class AssignmentUpdate(BaseModel):
    """Assignment update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[AssignmentStatus] = None


class Assignment(AssignmentBase, BaseResponse):
    """Assignment response model."""
    user_id: UUID
    file_path: Optional[str] = None
    status: AssignmentStatus = AssignmentStatus.UPLOADED
    file_size: Optional[int] = None
    file_type: Optional[str] = None


# Task models
class TaskDependency(BaseModel):
    """Task dependency model."""
    task_id: UUID
    dependency_type: str = "blocking"  # blocking, optional, parallel


class Task(BaseModel):
    """Task model for plan execution."""
    id: UUID = Field(default_factory=uuid4)
    task_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    dependencies: List[TaskDependency] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # in minutes
    tool_requirements: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    """Task creation request model."""
    task_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    dependencies: List[TaskDependency] = Field(default_factory=list)
    estimated_duration: Optional[int] = None
    tool_requirements: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


# Plan models
class PlanBase(BaseModel):
    """Base plan model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PlanCreate(PlanBase):
    """Plan creation request model."""
    assignment_id: UUID
    tasks: List[TaskCreate] = Field(default_factory=list)


class PlanUpdate(BaseModel):
    """Plan update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[PlanStatus] = None


class Plan(PlanBase, BaseResponse):
    """Plan response model."""
    assignment_id: UUID
    tasks: List[Task] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.CREATED
    total_estimated_duration: Optional[int] = None
    execution_started_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None


# Execution models
class ExecutionResult(BaseModel):
    """Execution result model."""
    task_id: UUID
    status: TaskStatus
    output: Optional[Dict[str, Any]] = None
    logs: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # in seconds


class ExecutionRequest(BaseModel):
    """Execution request model."""
    plan_id: UUID
    dry_run: bool = False
    parallel_execution: bool = True
    max_parallel_tasks: int = 3


class ExecutionResponse(BaseModel):
    """Execution response model."""
    execution_id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    status: str
    results: List[ExecutionResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_execution_time: Optional[float] = None


# File upload models
class FileUploadResponse(BaseModel):
    """File upload response model."""
    file_id: UUID = Field(default_factory=uuid4)
    filename: str
    file_size: int
    file_type: str
    upload_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


# Chat/Interaction models
class ChatMessage(BaseModel):
    """Chat message model."""
    id: UUID = Field(default_factory=uuid4)
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=2000)
    assignment_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: ChatMessage
    suggestions: List[str] = Field(default_factory=list)
    related_assignments: List[UUID] = Field(default_factory=list)


# Error models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Health check models
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = Field(default_factory=dict)
