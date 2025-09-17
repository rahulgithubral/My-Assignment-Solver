# System Design Document: Assignment Assistant Agent

## Problem Statement

University students face significant challenges in managing complex programming assignments that require multiple steps: understanding requirements, planning implementation, scaffolding code, writing tests, and generating deliverables. The Assignment Assistant Agent automates this workflow by providing an AI-powered system that can ingest assignment documents, create structured plans, and execute tasks to produce complete solutions.

## Functional Requirements

### Core Features (Mandatory)
1. **Document Ingestion**: Accept PDF assignment files and extract text content
2. **AI Planning**: Generate structured task plans from assignment descriptions
3. **Task Execution**: Execute planned tasks with appropriate tools
4. **User Interface**: Provide web-based interface for interaction
5. **Deliverable Generation**: Produce complete assignment solutions

### Advanced Features (Bonus)
1. **Multi-Agent Architecture**: Separate Planner and Executor agents
2. **RAG Integration**: Use retrieved context for better planning
3. **External Tool Integration**: Support for Git, testing frameworks, linters
4. **Monitoring UI**: Real-time task status and manual overrides
5. **Scheduling**: Background task processing and retry mechanisms

## Non-Functional Requirements

### Security
- Secure file upload with validation and sanitization
- Environment-based secret management
- Rate limiting on API endpoints
- Sandboxed code execution with timeouts

### Performance
- Sub-second response times for UI interactions
- Background processing for long-running tasks
- Efficient vector search with FAISS/ChromaDB
- Horizontal scaling capability

### Testability
- Unit tests for all core components
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Mock external dependencies

### Maintainability
- Modular architecture with clear separation of concerns
- Type safety with TypeScript and Pydantic
- Comprehensive logging and monitoring
- Documentation and code comments

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Agent Core     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (Planner +     │
│                 │    │                 │    │   Executor)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Upload   │    │   PostgreSQL    │    │   Vector Store  │
│   & Chat UI     │    │   Database      │    │   (FAISS)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Task Queue     │
                       │  (Celery+Redis) │
                       └─────────────────┘
```

### Component Responsibilities

1. **Frontend (Next.js + TypeScript)**
   - User interface for file upload and chat interaction
   - Plan visualization and editing
   - Real-time status updates
   - Responsive design with Tailwind CSS

2. **Backend API (FastAPI)**
   - RESTful API endpoints for all operations
   - Authentication and authorization
   - File upload handling and validation
   - Database operations and caching

3. **Agent Orchestrator**
   - **Planner**: Analyzes assignments and creates task graphs
   - **Executor**: Runs tasks with appropriate tools and monitoring
   - Tool integration and sandboxing

4. **Vector Database (FAISS/ChromaDB)**
   - Document embedding storage and retrieval
   - Similarity search for RAG context
   - Efficient indexing and querying

5. **PostgreSQL Database**
   - User and assignment metadata
   - Task execution logs and results
   - System configuration and state

6. **Task Queue (Celery + Redis)**
   - Background job processing
   - Retry mechanisms and error handling
   - Scalable worker distribution

## Data Model

### Core Entities

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assignments table
CREATE TABLE assignments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_path VARCHAR(1000),
    status VARCHAR(50) DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Plans table
CREATE TABLE plans (
    id UUID PRIMARY KEY,
    assignment_id UUID REFERENCES assignments(id),
    tasks JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES plans(id),
    task_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    dependencies JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Execution logs table
CREATE TABLE execution_logs (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## Technology Choices

### Backend: FastAPI
- **Reason**: High performance, automatic API documentation, type safety with Pydantic
- **Benefits**: Async support, built-in validation, easy testing

### Frontend: Next.js + TypeScript
- **Reason**: Server-side rendering, excellent TypeScript support, React ecosystem
- **Benefits**: SEO-friendly, fast development, production-ready

### Database: PostgreSQL
- **Reason**: ACID compliance, JSON support, excellent performance
- **Benefits**: Reliable, scalable, rich feature set

### Vector Store: FAISS
- **Reason**: Fast similarity search, memory efficient, easy integration
- **Benefits**: GPU acceleration support, large-scale indexing

### Task Queue: Celery + Redis
- **Reason**: Mature Python solution, reliable message passing
- **Benefits**: Distributed processing, monitoring, retry mechanisms

## Deployment Architecture

### Development Environment
```
┌─────────────────┐
│  Docker Compose │
│  - Backend      │
│  - Frontend     │
│  - PostgreSQL   │
│  - Redis        │
│  - Worker       │
└─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   App Servers   │    │   Database      │
│   (Nginx)       │◄──►│   (Multiple)    │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Worker Cluster │
                       │  (Celery)       │
                       └─────────────────┘
```

## CI/CD Pipeline

1. **Code Push**: Trigger GitHub Actions workflow
2. **Testing**: Run unit tests, integration tests, linting
3. **Build**: Create Docker images for all services
4. **Deploy**: Deploy to staging environment
5. **E2E Tests**: Run end-to-end tests
6. **Production**: Deploy to production with zero downtime

## Interaction Logs & LLM Usage

### Logging Strategy
- All LLM interactions logged with timestamps and model versions
- Prompt templates stored in version control
- Response validation and error tracking
- User consent for data collection

### LLM Integration
- OpenAI GPT-4 for planning and reasoning
- Embedding models for document processing
- Fallback mechanisms for API failures
- Cost monitoring and optimization

### Data Privacy
- No PII stored in logs without consent
- Secure API key management
- Data retention policies
- GDPR compliance considerations
