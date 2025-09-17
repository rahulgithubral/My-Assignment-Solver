"""
Unit tests for the Assignment Planner agent.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from agent.planner.planner import AssignmentPlanner, create_plan


class TestAssignmentPlanner:
    """Test cases for the AssignmentPlanner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = AssignmentPlanner()
    
    def test_create_plan_basic(self):
        """Test basic plan creation."""
        assignment_title = "Build a REST API"
        assignment_description = "Create a REST API using Python and FastAPI"
        
        plan = self.planner.create_plan(
            assignment_title=assignment_title,
            assignment_description=assignment_description
        )
        
        assert plan is not None
        assert plan["name"] == f"Execution Plan for {assignment_title}"
        assert plan["assignment_id"] is None
        assert "tasks" in plan
        assert len(plan["tasks"]) > 0
        assert plan["status"] == "created"
    
    def test_create_plan_with_assignment_id(self):
        """Test plan creation with assignment ID."""
        assignment_id = uuid4()
        plan = self.planner.create_plan(
            assignment_title="Test Assignment",
            assignment_id=assignment_id
        )
        
        assert plan["assignment_id"] == str(assignment_id)
    
    def test_analyze_requirements_python(self):
        """Test requirements analysis for Python assignment."""
        text = "Create a Python web application using Django framework"
        
        requirements = self.planner._analyze_requirements(text, "", [])
        
        assert requirements["programming_language"] == "python"
        assert requirements["framework"] == "django"
        assert "source_code" in requirements["deliverables"]
    
    def test_analyze_requirements_javascript(self):
        """Test requirements analysis for JavaScript assignment."""
        text = "Build a React application with Node.js backend"
        
        requirements = self.planner._analyze_requirements(text, "", [])
        
        assert requirements["programming_language"] == "javascript"
        assert requirements["framework"] == "react"
    
    def test_analyze_requirements_testing(self):
        """Test requirements analysis with testing requirements."""
        text = "Implement a solution with comprehensive unit tests and documentation"
        
        requirements = self.planner._analyze_requirements(text, "", [])
        
        assert requirements["testing_required"] is True
        assert requirements["documentation_required"] is True
        assert "tests" in requirements["deliverables"]
        assert "documentation" in requirements["deliverables"]
    
    def test_detect_programming_language(self):
        """Test programming language detection."""
        assert self.planner._detect_programming_language("Python project") == "python"
        assert self.planner._detect_programming_language("JavaScript app") == "javascript"
        assert self.planner._detect_programming_language("Java application") == "java"
        assert self.planner._detect_programming_language("C++ program") == "cpp"
        assert self.planner._detect_programming_language("Unknown language") == "python"  # default
    
    def test_detect_framework(self):
        """Test framework detection."""
        assert self.planner._detect_framework("Django web app") == "django"
        assert self.planner._detect_framework("Flask API") == "flask"
        assert self.planner._detect_framework("FastAPI service") == "fastapi"
        assert self.planner._detect_framework("React frontend") == "react"
        assert self.planner._detect_framework("Vue.js app") == "vue"
        assert self.planner._detect_framework("Angular project") == "angular"
        assert self.planner._detect_framework("Spring Boot") == "spring"
        assert self.planner._detect_framework("No framework") == "none"
    
    def test_extract_deliverables(self):
        """Test deliverable extraction."""
        text = "Submit source code, tests, documentation, and a demo"
        
        deliverables = self.planner._extract_deliverables(text)
        
        assert "source_code" in deliverables
        assert "tests" in deliverables
        assert "documentation" in deliverables
        assert "demo" in deliverables
    
    def test_assess_complexity(self):
        """Test complexity assessment."""
        # High complexity
        complex_text = "Implement advanced algorithms with data structures and performance optimization"
        assert self.planner._assess_complexity(complex_text) == "high"
        
        # Medium complexity
        medium_text = "Create API with database integration and authentication"
        assert self.planner._assess_complexity(medium_text) == "medium"
        
        # Low complexity
        simple_text = "Simple calculator application"
        assert self.planner._assess_complexity(simple_text) == "low"
    
    def test_extract_deadline(self):
        """Test deadline extraction."""
        text_with_date = "Assignment due on 2024-12-31"
        deadline = self.planner._extract_deadline(text_with_date)
        assert deadline == "2024-12-31"
        
        text_without_date = "No deadline mentioned"
        deadline = self.planner._extract_deadline(text_without_date)
        assert deadline is None
    
    def test_generate_task_sequence(self):
        """Test task sequence generation."""
        requirements = {
            "programming_language": "python",
            "framework": "fastapi",
            "deliverables": ["source_code", "tests", "documentation"],
            "complexity": "medium",
            "testing_required": True,
            "documentation_required": True
        }
        
        tasks = self.planner._generate_task_sequence(requirements)
        
        assert len(tasks) >= 4  # At least project_setup, requirements_analysis, core_implementation, final_review
        assert any(task["task_type"] == "project_setup" for task in tasks)
        assert any(task["task_type"] == "requirements_analysis" for task in tasks)
        assert any(task["task_type"] == "core_implementation" for task in tasks)
        assert any(task["task_type"] == "testing" for task in tasks)
        assert any(task["task_type"] == "documentation" for task in tasks)
        assert any(task["task_type"] == "final_review" for task in tasks)
        
        # Check task dependencies
        for task in tasks:
            assert "id" in task
            assert "task_type" in task
            assert "description" in task
            assert "dependencies" in task
            assert "estimated_duration" in task
            assert "tool_requirements" in task
            assert "parameters" in task
            assert "status" in task


class TestCreatePlanFunction:
    """Test cases for the create_plan convenience function."""
    
    def test_create_plan_function(self):
        """Test the create_plan convenience function."""
        plan = create_plan(
            assignment_title="Test Assignment",
            assignment_description="Test description"
        )
        
        assert plan is not None
        assert plan["name"] == "Execution Plan for Test Assignment"
        assert "tasks" in plan
        assert len(plan["tasks"]) > 0


@pytest.mark.parametrize("language,expected_tools", [
    ("python", ["git", "package_manager"]),
    ("javascript", ["git", "package_manager"]),
    ("java", ["git", "package_manager"]),
])
def test_task_tool_requirements(language, expected_tools):
    """Test that tasks have appropriate tool requirements."""
    planner = AssignmentPlanner()
    requirements = {
        "programming_language": language,
        "framework": "none",
        "deliverables": ["source_code"],
        "complexity": "low",
        "testing_required": False,
        "documentation_required": False
    }
    
    tasks = planner._generate_task_sequence(requirements)
    project_setup_task = next(task for task in tasks if task["task_type"] == "project_setup")
    
    assert all(tool in project_setup_task["tool_requirements"] for tool in expected_tools)


def test_plan_estimated_duration():
    """Test that plan has reasonable estimated duration."""
    planner = AssignmentPlanner()
    plan = planner.create_plan("Test Assignment")
    
    assert "estimated_duration" in plan
    assert plan["estimated_duration"] > 0
    assert plan["estimated_duration"] < 1000  # Reasonable upper bound
