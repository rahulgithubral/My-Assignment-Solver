# Demo Steps for Assignment Assistant Agent

This document provides step-by-step instructions for demonstrating the Assignment Assistant Agent system.

## Prerequisites

1. **Environment Setup**
   - Docker and Docker Compose installed
   - OpenAI API key (for LLM functionality)
   - Git installed

2. **Repository Setup**
   ```bash
   git clone <repository-url>
   cd assignment-agent
   cp env.example .env
   # Edit .env file with your OpenAI API key
   ```

## Demo Scenarios

### Scenario 1: Basic Assignment Upload and Processing

**Objective**: Demonstrate the core workflow of uploading an assignment and generating an execution plan.

#### Steps:

1. **Start the System**
   ```bash
   cd infra
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access the Application**
   - Open browser to `http://localhost:3000`
   - Verify the application loads correctly

3. **Upload Assignment**
   - Click on the "Upload" tab
   - Drag and drop or select a PDF assignment file
   - Add optional title and description
   - Click "Upload Assignment"
   - Verify file upload success

4. **Generate Plan**
   - Switch to "Chat" tab
   - Click "Generate Plan" button
   - Wait for plan generation to complete
   - Verify plan appears in the "Plans" tab

5. **Review Generated Plan**
   - Switch to "Plans" tab
   - Click on the generated plan
   - Review the task breakdown
   - Show task dependencies and estimated durations

#### Expected Results:
- Assignment file successfully uploaded
- Plan generated with multiple tasks
- Tasks include: project setup, requirements analysis, core implementation, testing, documentation, final review
- Each task has appropriate dependencies and time estimates

### Scenario 2: Plan Execution and Monitoring

**Objective**: Demonstrate plan execution and real-time monitoring.

#### Steps:

1. **Execute Plan**
   - In the Plans tab, select a plan
   - Click "Execute Plan" button
   - Choose between dry run and actual execution

2. **Monitor Execution**
   - Watch real-time status updates
   - Show task status changes (pending → running → success/failed)
   - Display execution logs and results

3. **Review Results**
   - Show completed task results
   - Display generated files and outputs
   - Review execution summary

#### Expected Results:
- Plan execution starts successfully
- Tasks execute in proper dependency order
- Real-time status updates visible
- Generated code and documentation files
- Execution summary with timing information

### Scenario 3: Chat Interaction

**Objective**: Demonstrate the AI chat assistant capabilities.

#### Steps:

1. **Start Chat Session**
   - Select an uploaded assignment
   - Switch to "Chat" tab
   - Send a message asking about the assignment

2. **Interactive Q&A**
   - Ask questions about the assignment requirements
   - Request clarification on specific tasks
   - Ask for code examples or implementation suggestions

3. **Context-Aware Responses**
   - Show how the assistant references the uploaded document
   - Demonstrate RAG capabilities with document context

#### Expected Results:
- Chat interface responds to messages
- AI provides relevant, context-aware responses
- References to uploaded assignment content
- Helpful suggestions for implementation

### Scenario 4: Multi-Assignment Management

**Objective**: Demonstrate managing multiple assignments simultaneously.

#### Steps:

1. **Upload Multiple Assignments**
   - Upload 2-3 different assignment files
   - Show assignment list in sidebar
   - Demonstrate assignment switching

2. **Generate Multiple Plans**
   - Generate plans for different assignments
   - Show plan comparison
   - Demonstrate different task structures for different assignment types

3. **Parallel Processing**
   - Show multiple assignments being processed
   - Demonstrate background task processing
   - Show system scalability

#### Expected Results:
- Multiple assignments visible in sidebar
- Each assignment has its own plan and chat context
- System handles multiple concurrent operations
- Clean separation between different assignment workflows

## Technical Demonstrations

### Backend API Testing

1. **API Documentation**
   - Navigate to `http://localhost:8000/docs`
   - Show FastAPI automatic documentation
   - Demonstrate API endpoints

2. **Health Monitoring**
   - Check `http://localhost:8000/health`
   - Show system status and dependencies

3. **Celery Monitoring**
   - Access Flower at `http://localhost:5555`
   - Show task queue status
   - Monitor background job execution

### Database and Storage

1. **Database Inspection**
   ```bash
   docker exec -it assignment-agent-db-dev psql -U postgres -d assignment_agent
   \dt  # List tables
   SELECT * FROM assignments;  # View assignments
   ```

2. **Vector Store**
   - Show document embeddings
   - Demonstrate similarity search
   - Display RAG context retrieval

### Logging and Debugging

1. **Application Logs**
   ```bash
   docker logs assignment-agent-backend-dev
   docker logs assignment-agent-worker-dev
   ```

2. **Error Handling**
   - Upload invalid file types
   - Show graceful error handling
   - Demonstrate user-friendly error messages

## Performance Demonstrations

### Load Testing

1. **Concurrent Uploads**
   - Upload multiple files simultaneously
   - Show system handling concurrent requests

2. **Large File Processing**
   - Upload large PDF files
   - Demonstrate efficient processing

3. **Background Task Processing**
   - Show Celery worker processing
   - Demonstrate task queuing and execution

## Troubleshooting Demo

### Common Issues and Solutions

1. **File Upload Issues**
   - Show file type validation
   - Demonstrate file size limits
   - Show error messages for invalid files

2. **API Errors**
   - Show proper error responses
   - Demonstrate error logging
   - Show user-friendly error messages

3. **Database Connection Issues**
   - Show connection retry logic
   - Demonstrate graceful degradation

## Demo Script for Presentation

### Introduction (2 minutes)
- Overview of the Assignment Assistant Agent
- Key features and capabilities
- Target use case: University assignment automation

### Core Workflow (5 minutes)
- Upload assignment file
- Generate execution plan
- Execute plan with monitoring
- Review results and deliverables

### Advanced Features (3 minutes)
- Chat interaction with AI assistant
- Multi-assignment management
- Real-time monitoring and status updates

### Technical Architecture (2 minutes)
- Backend API and database
- Frontend React application
- Background task processing
- Vector search and RAG

### Q&A and Discussion (3 minutes)
- Answer questions about implementation
- Discuss potential improvements
- Address technical concerns

## Demo Data

### Sample Assignment Files

1. **Simple Python Project**
   - Title: "Build a Calculator"
   - Description: "Create a command-line calculator with basic operations"
   - Expected tasks: Project setup, implementation, testing, documentation

2. **Web Application**
   - Title: "Student Management System"
   - Description: "Build a web application for managing student records"
   - Expected tasks: Database design, API development, frontend, testing

3. **Data Analysis Project**
   - Title: "Sales Data Analysis"
   - Description: "Analyze sales data and create visualizations"
   - Expected tasks: Data processing, analysis, visualization, report generation

## Success Metrics

### Demo Success Criteria

1. **Functional Requirements**
   - ✅ File upload works correctly
   - ✅ Plan generation produces valid tasks
   - ✅ Plan execution completes successfully
   - ✅ Chat interface responds appropriately

2. **Performance Requirements**
   - ✅ File upload completes within 10 seconds
   - ✅ Plan generation completes within 30 seconds
   - ✅ UI remains responsive during processing
   - ✅ Background tasks process efficiently

3. **User Experience**
   - ✅ Intuitive interface navigation
   - ✅ Clear status indicators
   - ✅ Helpful error messages
   - ✅ Responsive design

## Post-Demo Actions

1. **Collect Feedback**
   - Ask for specific feature requests
   - Identify potential improvements
   - Note any issues or concerns

2. **Technical Questions**
   - Architecture decisions
   - Scalability considerations
   - Security implementations
   - Deployment strategies

3. **Next Steps**
   - Discuss potential enhancements
   - Plan for production deployment
   - Consider integration opportunities
