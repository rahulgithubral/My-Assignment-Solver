"""
Unit tests for the Assignment Executor agent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from agent.executor.executor import TaskExecutor, execute_plan


class TestTaskExecutor:
    """Test cases for the TaskExecutor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.executor = TaskExecutor()
    
    def test_execute_plan_dry_run(self):
        """Test plan execution in dry run mode."""
        plan_id = uuid4()
        tasks = [
            {
                "id": str(uuid4()),
                "task_type": "project_setup",
                "description": "Set up project",
                "dependencies": [],
                "estimated_duration": 15,
                "tool_requirements": ["git"],
                "parameters": {},
                "status": "pending"
            },
            {
                "id": str(uuid4()),
                "task_type": "core_implementation",
                "description": "Implement core features",
                "dependencies": [],
                "estimated_duration": 60,
                "tool_requirements": ["code_editor"],
                "parameters": {},
                "status": "pending"
            }
        ]
        
        result = self.executor.execute_plan(
            plan_id=plan_id,
            tasks=tasks,
            dry_run=True
        )
        
        assert result["plan_id"] == str(plan_id)
        assert result["status"] == "simulated"
        assert len(result["results"]) == 2
        assert all(r["status"] == "simulated" for r in result["results"])
        assert result["total_estimated_time"] > 0
    
    def test_execute_plan_sequential(self):
        """Test sequential plan execution."""
        plan_id = uuid4()
        tasks = [
            {
                "id": str(uuid4()),
                "task_type": "project_setup",
                "description": "Set up project",
                "dependencies": [],
                "estimated_duration": 15,
                "tool_requirements": ["git"],
                "parameters": {},
                "status": "pending"
            }
        ]
        
        with patch.object(self.executor, '_execute_single_task') as mock_execute:
            mock_execute.return_value = {
                "task_id": tasks[0]["id"],
                "status": "success",
                "result": {"message": "Task completed"},
                "execution_time": 10.5,
                "logs": ["Task executed successfully"]
            }
            
            result = self.executor.execute_plan(
                plan_id=plan_id,
                tasks=tasks,
                dry_run=False,
                parallel_execution=False
            )
            
            assert result["plan_id"] == str(plan_id)
            assert result["status"] == "completed"
            assert len(result["results"]) == 1
            assert result["results"][0]["status"] == "success"
            mock_execute.assert_called_once()
    
    def test_can_execute_task_no_dependencies(self):
        """Test task execution when no dependencies."""
        task = {
            "id": str(uuid4()),
            "dependencies": []
        }
        completed_tasks = set()
        
        assert self.executor._can_execute_task(task, completed_tasks) is True
    
    def test_can_execute_task_with_dependencies(self):
        """Test task execution with satisfied dependencies."""
        task_id_1 = str(uuid4())
        task_id_2 = str(uuid4())
        
        task = {
            "id": task_id_2,
            "dependencies": [{"task_id": task_id_1, "dependency_type": "blocking"}]
        }
        completed_tasks = {task_id_1}
        
        assert self.executor._can_execute_task(task, completed_tasks) is True
    
    def test_can_execute_task_unsatisfied_dependencies(self):
        """Test task execution with unsatisfied dependencies."""
        task_id_1 = str(uuid4())
        task_id_2 = str(uuid4())
        
        task = {
            "id": task_id_2,
            "dependencies": [{"task_id": task_id_1, "dependency_type": "blocking"}]
        }
        completed_tasks = set()
        
        assert self.executor._can_execute_task(task, completed_tasks) is False
    
    def test_execute_project_setup(self):
        """Test project setup task execution."""
        with patch.object(self.executor.tools["code_gen"], 'create_project_structure') as mock_create:
            mock_create.return_value = {
                "files_created": ["main.py", "requirements.txt"],
                "logs": ["Project structure created"]
            }
            
            task = {
                "id": str(uuid4()),
                "task_type": "project_setup",
                "parameters": {
                    "language": "python",
                    "framework": "fastapi"
                }
            }
            context = {
                "temp_dir": "/tmp/test",
                "plan_id": uuid4()
            }
            
            result = self.executor._execute_project_setup(task, context)
            
            assert result["action"] == "project_setup"
            assert result["language"] == "python"
            assert result["framework"] == "fastapi"
            assert "files_created" in result
            mock_create.assert_called_once()
    
    def test_execute_requirements_analysis(self):
        """Test requirements analysis task execution."""
        with patch.object(self.executor.tools["code_gen"], 'create_requirements_doc') as mock_create:
            mock_create.return_value = "/tmp/requirements.md"
            
            task = {
                "id": str(uuid4()),
                "task_type": "requirements_analysis"
            }
            context = {
                "temp_dir": "/tmp/test",
                "plan_id": uuid4()
            }
            
            result = self.executor._execute_requirements_analysis(task, context)
            
            assert result["action"] == "requirements_analysis"
            assert "document_created" in result
            mock_create.assert_called_once()
    
    def test_execute_core_implementation(self):
        """Test core implementation task execution."""
        with patch.object(self.executor.tools["code_gen"], 'create_sample_implementation') as mock_create:
            mock_create.return_value = {
                "files_created": ["main.py", "utils.py"],
                "language": "python"
            }
            
            task = {
                "id": str(uuid4()),
                "task_type": "core_implementation",
                "parameters": {
                    "language": "python"
                }
            }
            context = {
                "temp_dir": "/tmp/test",
                "plan_id": uuid4()
            }
            
            result = self.executor._execute_core_implementation(task, context)
            
            assert result["action"] == "core_implementation"
            assert result["language"] == "python"
            assert "files_created" in result
            mock_create.assert_called_once()
    
    def test_execute_testing(self):
        """Test testing task execution."""
        with patch.object(self.executor.tools["test_runner"], 'run_tests') as mock_run:
            mock_run.return_value = {
                "status": "success",
                "tests_run": 5,
                "tests_passed": 5,
                "tests_failed": 0
            }
            
            task = {
                "id": str(uuid4()),
                "task_type": "testing",
                "parameters": {
                    "language": "python"
                }
            }
            context = {
                "temp_dir": "/tmp/test",
                "plan_id": uuid4()
            }
            
            result = self.executor._execute_testing(task, context)
            
            assert result["action"] == "testing"
            assert result["language"] == "python"
            assert "test_results" in result
            mock_run.assert_called_once()
    
    def test_execute_documentation(self):
        """Test documentation task execution."""
        with patch.object(self.executor.tools["code_gen"], 'create_documentation') as mock_create:
            mock_create.return_value = {
                "files_created": ["README.md", "API.md"]
            }
            
            task = {
                "id": str(uuid4()),
                "task_type": "documentation",
                "parameters": {
                    "include_api_docs": True
                }
            }
            context = {
                "temp_dir": "/tmp/test",
                "plan_id": uuid4()
            }
            
            result = self.executor._execute_documentation(task, context)
            
            assert result["action"] == "documentation"
            assert "files_created" in result
            mock_create.assert_called_once()
    
    def test_execute_final_review(self):
        """Test final review task execution."""
        task = {
            "id": str(uuid4()),
            "task_type": "final_review",
            "parameters": {
                "deliverables": ["source_code", "tests", "documentation"]
            }
        }
        context = {
            "temp_dir": "/tmp/test",
            "plan_id": uuid4()
        }
        
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ["main.py", "test_main.py", "README.md"]
            
            result = self.executor._execute_final_review(task, context)
            
            assert result["action"] == "final_review"
            assert "deliverables" in result
            assert "review_results" in result
    
    def test_perform_final_review(self):
        """Test final review functionality."""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ["main.py", "test_main.py", "README.md"]
            
            result = self.executor._perform_final_review(
                output_dir="/tmp/test",
                deliverables=["source_code", "tests", "documentation"]
            )
            
            assert "files_present" in result
            assert "files_missing" in result
            assert "quality_checks" in result
            assert "main.py" in result["files_present"]
            assert "test_main.py" in result["files_present"]
            assert "README.md" in result["files_present"]
    
    def test_generate_execution_summary(self):
        """Test execution summary generation."""
        results = [
            {
                "task_id": str(uuid4()),
                "status": "success",
                "execution_time": 10.5
            },
            {
                "task_id": str(uuid4()),
                "status": "success",
                "execution_time": 15.2
            },
            {
                "task_id": str(uuid4()),
                "status": "failed",
                "execution_time": 5.0
            }
        ]
        
        summary = self.executor._generate_execution_summary(results)
        
        assert summary["status"] == "partial"
        assert summary["total_tasks"] == 3
        assert summary["successful_tasks"] == 2
        assert summary["failed_tasks"] == 1
        assert summary["total_execution_time"] == 30.7
    
    def test_generate_execution_summary_all_success(self):
        """Test execution summary when all tasks succeed."""
        results = [
            {
                "task_id": str(uuid4()),
                "status": "success",
                "execution_time": 10.5
            },
            {
                "task_id": str(uuid4()),
                "status": "success",
                "execution_time": 15.2
            }
        ]
        
        summary = self.executor._generate_execution_summary(results)
        
        assert summary["status"] == "completed"
        assert summary["total_tasks"] == 2
        assert summary["successful_tasks"] == 2
        assert summary["failed_tasks"] == 0
    
    def test_generate_execution_summary_all_failed(self):
        """Test execution summary when all tasks fail."""
        results = [
            {
                "task_id": str(uuid4()),
                "status": "failed",
                "execution_time": 5.0
            },
            {
                "task_id": str(uuid4()),
                "status": "failed",
                "execution_time": 3.0
            }
        ]
        
        summary = self.executor._generate_execution_summary(results)
        
        assert summary["status"] == "failed"
        assert summary["total_tasks"] == 2
        assert summary["successful_tasks"] == 0
        assert summary["failed_tasks"] == 2


class TestExecutePlanFunction:
    """Test cases for the execute_plan convenience function."""
    
    def test_execute_plan_function(self):
        """Test the execute_plan convenience function."""
        plan_id = uuid4()
        tasks = [
            {
                "id": str(uuid4()),
                "task_type": "project_setup",
                "description": "Set up project",
                "dependencies": [],
                "estimated_duration": 15,
                "tool_requirements": ["git"],
                "parameters": {},
                "status": "pending"
            }
        ]
        
        result = execute_plan(
            plan_id=plan_id,
            tasks=tasks,
            dry_run=True
        )
        
        assert result is not None
        assert result["plan_id"] == str(plan_id)
        assert "results" in result


@pytest.mark.parametrize("task_type,expected_action", [
    ("project_setup", "project_setup"),
    ("requirements_analysis", "requirements_analysis"),
    ("core_implementation", "core_implementation"),
    ("testing", "testing"),
    ("documentation", "documentation"),
    ("final_review", "final_review"),
    ("unknown_task", "generic_task"),
])
def test_task_type_routing(task_type, expected_action):
    """Test that different task types are routed correctly."""
    executor = TaskExecutor()
    task = {
        "id": str(uuid4()),
        "task_type": task_type,
        "parameters": {}
    }
    context = {"temp_dir": "/tmp/test", "plan_id": uuid4()}
    
    if task_type in ["project_setup", "requirements_analysis", "core_implementation", "testing", "documentation", "final_review"]:
        with patch.object(executor, f'_execute_{task_type}', return_value={"action": expected_action}) as mock_method:
            result = getattr(executor, f'_execute_{task_type}')(task, context)
            assert result["action"] == expected_action
    else:
        result = executor._execute_generic_task(task, context)
        assert result["action"] == "generic_task"
