"""
Assignment Executor Agent
Executes planned tasks with proper tooling and monitoring.
"""

import logging
import asyncio
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
import json
import os

from agent.tools.code_gen import CodeGenerator
from agent.tools.test_runner import TestRunner
from agent.tools.git_util import GitManager

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executor agent that runs planned tasks with appropriate tools."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools = {
            "code_gen": CodeGenerator(),
            "test_runner": TestRunner(),
            "git": GitManager()
        }
        self.execution_logs = []
    
    def execute_plan(
        self,
        plan_id: UUID,
        tasks: List[Dict[str, Any]],
        dry_run: bool = False,
        parallel_execution: bool = True,
        max_parallel_tasks: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a plan with the given tasks.
        
        Args:
            plan_id: ID of the plan being executed
            tasks: List of tasks to execute
            dry_run: If True, simulate execution without making changes
            parallel_execution: Whether to run tasks in parallel when possible
            max_parallel_tasks: Maximum number of parallel tasks
            
        Returns:
            Dict containing execution results
        """
        try:
            self.logger.info(f"Executing plan {plan_id} with {len(tasks)} tasks")
            
            if dry_run:
                return self._simulate_execution(plan_id, tasks)
            
            # Create execution context
            execution_context = self._create_execution_context(plan_id)
            
            # Execute tasks
            if parallel_execution:
                results = self._execute_parallel(tasks, execution_context, max_parallel_tasks)
            else:
                results = self._execute_sequential(tasks, execution_context)
            
            # Generate execution summary
            summary = self._generate_execution_summary(results)
            
            self.logger.info(f"Plan execution completed: {plan_id}")
            
            return {
                "plan_id": str(plan_id),
                "status": summary["status"],
                "results": results,
                "summary": summary,
                "execution_time": summary["total_execution_time"],
                "logs": self.execution_logs
            }
            
        except Exception as e:
            self.logger.error(f"Error executing plan {plan_id}: {e}")
            return {
                "plan_id": str(plan_id),
                "status": "failed",
                "error": str(e),
                "results": [],
                "logs": self.execution_logs
            }
    
    def _create_execution_context(self, plan_id: UUID) -> Dict[str, Any]:
        """Create execution context for the plan."""
        # Create temporary directory for this execution
        temp_dir = tempfile.mkdtemp(prefix=f"assignment_agent_{plan_id}_")
        
        return {
            "plan_id": plan_id,
            "temp_dir": temp_dir,
            "start_time": datetime.utcnow(),
            "environment": {
                "PYTHONPATH": temp_dir,
                "NODE_PATH": temp_dir
            }
        }
    
    def _execute_sequential(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute tasks sequentially."""
        results = []
        completed_tasks = set()
        
        for task in tasks:
            if self._can_execute_task(task, completed_tasks):
                result = self._execute_single_task(task, context)
                results.append(result)
                
                if result["status"] == "success":
                    completed_tasks.add(task["id"])
                else:
                    # Stop execution on failure
                    break
            else:
                # Task dependencies not met
                results.append({
                    "task_id": task["id"],
                    "status": "skipped",
                    "reason": "Dependencies not met",
                    "execution_time": 0
                })
        
        return results
    
    def _execute_parallel(self, tasks: List[Dict[str, Any]], context: Dict[str, Any], max_parallel: int) -> List[Dict[str, Any]]:
        """Execute tasks in parallel when possible."""
        results = []
        completed_tasks = set()
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            # Find tasks that can be executed now
            ready_tasks = [
                task for task in remaining_tasks
                if self._can_execute_task(task, completed_tasks)
            ]
            
            if not ready_tasks:
                # No tasks can be executed (circular dependency or all failed)
                break
            
            # Limit parallel execution
            tasks_to_run = ready_tasks[:max_parallel]
            
            # Execute tasks in parallel
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                parallel_results = loop.run_until_complete(
                    self._execute_tasks_parallel(tasks_to_run, context)
                )
            finally:
                loop.close()
            
            results.extend(parallel_results)
            
            # Update completed tasks
            for result in parallel_results:
                if result["status"] == "success":
                    completed_tasks.add(result["task_id"])
            
            # Remove executed tasks from remaining
            for task in tasks_to_run:
                remaining_tasks.remove(task)
        
        return results
    
    async def _execute_tasks_parallel(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel using asyncio."""
        tasks_coroutines = [
            self._execute_single_task_async(task, context)
            for task in tasks
        ]
        
        return await asyncio.gather(*tasks_coroutines, return_exceptions=True)
    
    def _can_execute_task(self, task: Dict[str, Any], completed_tasks: set) -> bool:
        """Check if a task can be executed based on its dependencies."""
        dependencies = task.get("dependencies", [])
        
        for dep in dependencies:
            if isinstance(dep, dict) and "task_id" in dep:
                if dep["task_id"] not in completed_tasks:
                    return False
            elif isinstance(dep, str) and dep not in completed_tasks:
                return False
        
        return True
    
    def _execute_single_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task."""
        start_time = datetime.utcnow()
        task_id = task["id"]
        task_type = task["task_type"]
        
        try:
            self.logger.info(f"Executing task {task_id}: {task_type}")
            
            # Route to appropriate tool
            if task_type == "project_setup":
                result = self._execute_project_setup(task, context)
            elif task_type == "requirements_analysis":
                result = self._execute_requirements_analysis(task, context)
            elif task_type == "core_implementation":
                result = self._execute_core_implementation(task, context)
            elif task_type == "testing":
                result = self._execute_testing(task, context)
            elif task_type == "documentation":
                result = self._execute_documentation(task, context)
            elif task_type == "final_review":
                result = self._execute_final_review(task, context)
            else:
                result = self._execute_generic_task(task, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "task_id": task_id,
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "logs": result.get("logs", [])
            }
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Task execution failed: {str(e)}"
            
            self.logger.error(f"Task {task_id} failed: {e}")
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "execution_time": execution_time,
                "logs": [error_msg]
            }
    
    async def _execute_single_task_async(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of single task execution."""
        # For now, just call the sync version
        # In production, this would be truly async
        return self._execute_single_task(task, context)
    
    def _execute_project_setup(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project setup task."""
        params = task.get("parameters", {})
        language = params.get("language", "python")
        framework = params.get("framework", "none")
        
        # Use code generator to set up project
        result = self.tools["code_gen"].create_project_structure(
            language=language,
            framework=framework,
            output_dir=context["temp_dir"]
        )
        
        return {
            "action": "project_setup",
            "language": language,
            "framework": framework,
            "output_dir": context["temp_dir"],
            "files_created": result.get("files_created", []),
            "logs": result.get("logs", [])
        }
    
    def _execute_requirements_analysis(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requirements analysis task."""
        # Create requirements document
        requirements_doc = self.tools["code_gen"].create_requirements_doc(
            output_dir=context["temp_dir"]
        )
        
        return {
            "action": "requirements_analysis",
            "document_created": requirements_doc,
            "logs": ["Requirements analysis completed"]
        }
    
    def _execute_core_implementation(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute core implementation task."""
        params = task.get("parameters", {})
        language = params.get("language", "python")
        
        # Generate sample implementation
        implementation = self.tools["code_gen"].create_sample_implementation(
            language=language,
            output_dir=context["temp_dir"]
        )
        
        return {
            "action": "core_implementation",
            "language": language,
            "files_created": implementation.get("files_created", []),
            "logs": ["Core implementation completed"]
        }
    
    def _execute_testing(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing task."""
        params = task.get("parameters", {})
        language = params.get("language", "python")
        
        # Run tests
        test_result = self.tools["test_runner"].run_tests(
            language=language,
            test_dir=context["temp_dir"]
        )
        
        return {
            "action": "testing",
            "language": language,
            "test_results": test_result,
            "logs": ["Testing completed"]
        }
    
    def _execute_documentation(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation task."""
        params = task.get("parameters", {})
        
        # Create documentation
        docs = self.tools["code_gen"].create_documentation(
            output_dir=context["temp_dir"],
            include_api_docs=params.get("include_api_docs", True)
        )
        
        return {
            "action": "documentation",
            "files_created": docs.get("files_created", []),
            "logs": ["Documentation created"]
        }
    
    def _execute_final_review(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute final review task."""
        params = task.get("parameters", {})
        deliverables = params.get("deliverables", [])
        
        # Perform final checks
        review_result = self._perform_final_review(context["temp_dir"], deliverables)
        
        return {
            "action": "final_review",
            "deliverables": deliverables,
            "review_results": review_result,
            "logs": ["Final review completed"]
        }
    
    def _execute_generic_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic task."""
        return {
            "action": "generic_task",
            "task_type": task["task_type"],
            "logs": [f"Generic task {task['task_type']} executed"]
        }
    
    def _perform_final_review(self, output_dir: str, deliverables: List[str]) -> Dict[str, Any]:
        """Perform final review of deliverables."""
        review_results = {
            "files_present": [],
            "files_missing": [],
            "quality_checks": {}
        }
        
        # Check for required files
        for deliverable in deliverables:
            if deliverable == "source_code":
                # Check for source files
                source_files = [f for f in os.listdir(output_dir) if f.endswith(('.py', '.js', '.java', '.cpp'))]
                if source_files:
                    review_results["files_present"].extend(source_files)
                else:
                    review_results["files_missing"].append("source_code")
            
            elif deliverable == "tests":
                # Check for test files
                test_files = [f for f in os.listdir(output_dir) if 'test' in f.lower()]
                if test_files:
                    review_results["files_present"].extend(test_files)
                else:
                    review_results["files_missing"].append("tests")
            
            elif deliverable == "documentation":
                # Check for documentation
                doc_files = [f for f in os.listdir(output_dir) if f.lower() in ['readme.md', 'readme.txt', 'docs']]
                if doc_files:
                    review_results["files_present"].extend(doc_files)
                else:
                    review_results["files_missing"].append("documentation")
        
        return review_results
    
    def _simulate_execution(self, plan_id: UUID, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate execution without making actual changes."""
        results = []
        total_time = 0
        
        for task in tasks:
            estimated_time = task.get("estimated_duration", 0) * 60  # Convert to seconds
            total_time += estimated_time
            
            results.append({
                "task_id": task["id"],
                "status": "simulated",
                "estimated_time": estimated_time,
                "logs": [f"Simulated execution of {task['task_type']}"]
            })
        
        return {
            "plan_id": str(plan_id),
            "status": "simulated",
            "results": results,
            "total_estimated_time": total_time,
            "logs": ["Dry run simulation completed"]
        }
    
    def _generate_execution_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate execution summary from results."""
        total_tasks = len(results)
        successful_tasks = len([r for r in results if r["status"] == "success"])
        failed_tasks = len([r for r in results if r["status"] == "failed"])
        total_execution_time = sum(r.get("execution_time", 0) for r in results)
        
        status = "completed" if failed_tasks == 0 else "failed" if successful_tasks == 0 else "partial"
        
        return {
            "status": status,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "total_execution_time": total_execution_time
        }
    
    def cleanup(self, context: Dict[str, Any]):
        """Clean up execution context."""
        if "temp_dir" in context and os.path.exists(context["temp_dir"]):
            shutil.rmtree(context["temp_dir"])


# Convenience function for external use
def execute_plan(
    plan_id: UUID,
    tasks: List[Dict[str, Any]],
    dry_run: bool = False,
    parallel_execution: bool = True,
    max_parallel_tasks: int = 3
) -> Dict[str, Any]:
    """Execute a plan with the given tasks."""
    executor = TaskExecutor()
    try:
        return executor.execute_plan(plan_id, tasks, dry_run, parallel_execution, max_parallel_tasks)
    finally:
        # Cleanup would happen here in a real implementation
        pass
