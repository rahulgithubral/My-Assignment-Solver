"""
SQLAlchemy database models for the Assignment Assistant Agent.
Defines the database schema and relationships.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and assignment ownership."""
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # For future auth
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignments = relationship("Assignment", back_populates="user", cascade="all, delete-orphan")


class Assignment(Base):
    """Assignment model for storing assignment metadata and files."""
    __tablename__ = "assignments"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    status = Column(Enum("uploaded", "processing", "planned", "executing", "completed", "failed", name="assignment_status"), default="uploaded")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assignments")
    plans = relationship("Plan", back_populates="assignment", cascade="all, delete-orphan")


class Plan(Base):
    """Plan model for storing task execution plans."""
    __tablename__ = "plans"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id = Column(PostgresUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tasks = Column(JSON, nullable=False, default=list)  # List of task objects
    status = Column(Enum("created", "validated", "executing", "completed", "failed", name="plan_status"), default="created")
    total_estimated_duration = Column(Integer, nullable=True)  # in minutes
    execution_started_at = Column(DateTime(timezone=True), nullable=True)
    execution_completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignment = relationship("Assignment", back_populates="plans")
    tasks_relation = relationship("Task", back_populates="plan", cascade="all, delete-orphan")


class Task(Base):
    """Task model for individual plan tasks."""
    __tablename__ = "tasks"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(PostgresUUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    task_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    dependencies = Column(JSON, nullable=True, default=list)  # List of dependency objects
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    tool_requirements = Column(JSON, nullable=True, default=list)  # List of required tools
    parameters = Column(JSON, nullable=True, default=dict)  # Task parameters
    status = Column(Enum("pending", "running", "success", "failed", "cancelled", name="task_status"), default="pending")
    result = Column(JSON, nullable=True)  # Task execution result
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    plan = relationship("Plan", back_populates="tasks_relation")
    execution_logs = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")


class ExecutionLog(Base):
    """Execution log model for task execution tracking."""
    __tablename__ = "execution_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(PostgresUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    log_level = Column(Enum("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", name="log_level"), nullable=False)
    message = Column(Text, nullable=False)
    log_metadata = Column(JSON, nullable=True)  # Additional log metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="execution_logs")


class Document(Base):
    """Document model for storing processed documents and embeddings."""
    __tablename__ = "documents"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    assignment_id = Column(PostgresUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)  # Extracted text content
    chunks = Column(JSON, nullable=True)  # Text chunks for vector search
    embeddings = Column(JSON, nullable=True)  # Vector embeddings
    doc_metadata = Column(JSON, nullable=True)  # Document metadata
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assignment = relationship("Assignment")


class ChatSession(Base):
    """Chat session model for storing user interactions."""
    __tablename__ = "chat_sessions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignment_id = Column(PostgresUUID(as_uuid=True), ForeignKey("assignments.id"), nullable=True)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    assignment = relationship("Assignment")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model for storing conversation history."""
    __tablename__ = "chat_messages"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PostgresUUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Enum("user", "assistant", "system", name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Message metadata (model used, tokens, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
