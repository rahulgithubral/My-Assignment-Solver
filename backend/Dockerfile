# Multi-stage Dockerfile for Assignment Assistant Agent Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy the entire project (to access pyproject.toml from parent)
COPY . .

# Install Python dependencies from pyproject.toml
RUN cd backend && pip install --no-cache-dir -e ..[dev]

# Development stage
FROM base as development

# Install development dependencies
RUN cd backend && pip install --no-cache-dir \
    black \
    isort \
    mypy \
    pytest \
    pytest-cov

# Production stage
FROM base as production

# Remove development files
RUN rm -rf /app/tests /app/docs /app/.git

# Expose port
EXPOSE 8000

# Set working directory to backend
WORKDIR /app/backend

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
