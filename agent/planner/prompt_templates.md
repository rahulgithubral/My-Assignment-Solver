# Planner Prompt Templates

This document contains the prompt templates used by the Assignment Planner agent for creating execution plans.

## Main Planning Prompt

```
You are an expert software engineering assistant that creates detailed execution plans for programming assignments.

Assignment Details:
- Title: {assignment_title}
- Description: {assignment_description}
- Context Documents: {context_documents}

Please analyze this assignment and create a structured execution plan with the following components:

1. **Requirements Analysis**: Extract key requirements, programming language, frameworks, deliverables
2. **Task Breakdown**: Create a sequence of tasks with dependencies
3. **Time Estimation**: Provide realistic time estimates for each task
4. **Tool Requirements**: Specify tools and technologies needed
5. **Risk Assessment**: Identify potential challenges and mitigation strategies

Output Format (JSON):
{
  "requirements": {
    "programming_language": "string",
    "framework": "string", 
    "deliverables": ["list"],
    "complexity": "low|medium|high",
    "deadline": "string|null",
    "testing_required": boolean,
    "documentation_required": boolean,
    "git_required": boolean
  },
  "tasks": [
    {
      "id": "uuid",
      "task_type": "string",
      "description": "string",
      "dependencies": ["task_ids"],
      "estimated_duration": number,
      "tool_requirements": ["list"],
      "parameters": {},
      "status": "pending"
    }
  ],
  "estimated_total_duration": number,
  "risk_factors": ["list"],
  "success_criteria": ["list"]
}
```

## Task Type Definitions

### project_setup
- **Purpose**: Initialize project structure, dependencies, and basic configuration
- **Tools**: Git, package managers (npm, pip, etc.), IDE setup
- **Duration**: 10-20 minutes
- **Dependencies**: None

### requirements_analysis
- **Purpose**: Deep dive into requirements, create specifications
- **Tools**: Text editor, documentation tools
- **Duration**: 20-40 minutes
- **Dependencies**: project_setup

### core_implementation
- **Purpose**: Implement main functionality and features
- **Tools**: Code editor, linter, debugger
- **Duration**: 60-180 minutes (varies by complexity)
- **Dependencies**: requirements_analysis

### testing
- **Purpose**: Write and execute tests
- **Tools**: Test frameworks (pytest, jest, etc.), test runners
- **Duration**: 30-60 minutes
- **Dependencies**: core_implementation

### documentation
- **Purpose**: Create documentation, README, API docs
- **Tools**: Markdown editor, documentation generators
- **Duration**: 20-40 minutes
- **Dependencies**: core_implementation, testing (if applicable)

### final_review
- **Purpose**: Code review, packaging, final checks
- **Tools**: Linter, formatter, package tools
- **Duration**: 15-30 minutes
- **Dependencies**: All previous tasks

## Complexity Assessment Guidelines

### Low Complexity
- Simple CRUD operations
- Basic algorithms
- Single file implementations
- Estimated time: 2-4 hours

### Medium Complexity
- Multiple components/modules
- Database integration
- API development
- Authentication/authorization
- Estimated time: 4-8 hours

### High Complexity
- Complex algorithms
- Performance optimization
- Distributed systems
- Advanced data structures
- Machine learning integration
- Estimated time: 8+ hours

## Tool Requirements Mapping

### Programming Languages
- **Python**: pip, venv, pytest, black, flake8
- **JavaScript**: npm, jest, eslint, prettier
- **Java**: maven/gradle, junit, checkstyle
- **C++**: cmake, gtest, clang-format

### Frameworks
- **Django**: django-admin, django-extensions
- **Flask**: flask-cli, flask-migrate
- **React**: create-react-app, react-scripts
- **FastAPI**: uvicorn, alembic

### Development Tools
- **Version Control**: git, GitHub CLI
- **Code Quality**: linters, formatters, type checkers
- **Testing**: test runners, coverage tools
- **Documentation**: sphinx, jsdoc, mkdocs

## Risk Assessment Factors

1. **Technical Complexity**: High complexity increases risk
2. **Time Constraints**: Tight deadlines increase risk
3. **Dependency Management**: External dependencies can cause issues
4. **Environment Setup**: Complex setup requirements
5. **Integration Points**: Multiple system integrations
6. **Performance Requirements**: Non-functional requirements
7. **Security Requirements**: Authentication, authorization, data protection

## Success Criteria

1. **Functional Requirements**: All specified features implemented
2. **Code Quality**: Clean, readable, well-documented code
3. **Testing Coverage**: Adequate test coverage for critical paths
4. **Documentation**: Clear setup and usage instructions
5. **Performance**: Meets specified performance criteria
6. **Security**: Follows security best practices
7. **Maintainability**: Code is maintainable and extensible
