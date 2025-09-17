"""
Assignment Planner Agent
Creates structured execution plans from assignment descriptions and context.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

logger = logging.getLogger(__name__)


class AssignmentPlanner:
    """Planner agent that creates execution plans for assignments."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_plan(
        self,
        assignment_title: str,
        assignment_description: str = "",
        file_content: List[Dict[str, Any]] = None,
        assignment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create an execution plan for an assignment.
        
        Args:
            assignment_title: Title of the assignment
            assignment_description: Description of the assignment
            file_content: List of similar documents for context
            assignment_id: ID of the assignment
            
        Returns:
            Dict containing the execution plan
        """
        try:
            self.logger.info(f"Creating plan for assignment: {assignment_title}")
            
            # Analyze assignment requirements
            requirements = self._analyze_requirements(
                assignment_title, 
                assignment_description, 
                file_content or []
            )
            
            # Generate task sequence
            tasks = self._generate_task_sequence(requirements)
            
            # Create plan structure
            plan = {
                "id": str(uuid4()),
                "assignment_id": str(assignment_id) if assignment_id else None,
                "name": f"Execution Plan for {assignment_title}",
                "description": f"Generated plan for assignment: {assignment_title}",
                "created_at": datetime.utcnow().isoformat(),
                "requirements": requirements,
                "tasks": tasks,
                "estimated_duration": sum(task.get("estimated_duration", 0) for task in tasks),
                "status": "created"
            }
            
            self.logger.info(f"Plan created with {len(tasks)} tasks")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            raise
    
    def _analyze_requirements(
        self, 
        title: str, 
        description: str, 
        context_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze assignment requirements and extract key information."""
        
        # Combine all text content for analysis
        full_text = f"{title}\n{description}"
        for doc in context_docs:
            if isinstance(doc, dict) and "content" in doc:
                full_text += f"\n{doc['content']}"
        
        # Simple keyword-based analysis (in production, use LLM)
        requirements = {
            "programming_language": self._detect_programming_language(full_text),
            "framework": self._detect_framework(full_text),
            "deliverables": self._extract_deliverables(full_text),
            "complexity": self._assess_complexity(full_text),
            "deadline": self._extract_deadline(full_text),
            "testing_required": "test" in full_text.lower() or "testing" in full_text.lower(),
            "documentation_required": "documentation" in full_text.lower() or "readme" in full_text.lower(),
            "git_required": "git" in full_text.lower() or "repository" in full_text.lower()
        }
        
        return requirements
    
    def _detect_programming_language(self, text: str) -> str:
        """Detect programming language from assignment text."""
        text_lower = text.lower()
        
        if "python" in text_lower:
            return "python"
        elif "javascript" in text_lower or "js" in text_lower:
            return "javascript"
        elif "java" in text_lower:
            return "java"
        elif "c++" in text_lower or "cpp" in text_lower:
            return "cpp"
        elif "c#" in text_lower or "csharp" in text_lower:
            return "csharp"
        elif "go" in text_lower or "golang" in text_lower:
            return "go"
        elif "rust" in text_lower:
            return "rust"
        else:
            return "python"  # Default to Python
    
    def _detect_framework(self, text: str) -> str:
        """Detect framework or technology stack."""
        text_lower = text.lower()
        
        if "django" in text_lower:
            return "django"
        elif "flask" in text_lower:
            return "flask"
        elif "fastapi" in text_lower:
            return "fastapi"
        elif "react" in text_lower:
            return "react"
        elif "vue" in text_lower:
            return "vue"
        elif "angular" in text_lower:
            return "angular"
        elif "spring" in text_lower:
            return "spring"
        else:
            return "none"
    
    def _extract_deliverables(self, text: str) -> List[str]:
        """Extract required deliverables from assignment text."""
        deliverables = []
        text_lower = text.lower()
        
        if "code" in text_lower or "implementation" in text_lower:
            deliverables.append("source_code")
        if "test" in text_lower or "testing" in text_lower:
            deliverables.append("tests")
        if "documentation" in text_lower or "readme" in text_lower:
            deliverables.append("documentation")
        if "report" in text_lower:
            deliverables.append("report")
        if "presentation" in text_lower:
            deliverables.append("presentation")
        if "demo" in text_lower:
            deliverables.append("demo")
        
        return deliverables if deliverables else ["source_code"]
    
    def _assess_complexity(self, text: str) -> str:
        """Assess assignment complexity."""
        text_lower = text.lower()
        
        # Simple heuristics for complexity assessment
        complex_keywords = ["algorithm", "data structure", "optimization", "performance", "scalability"]
        medium_keywords = ["api", "database", "authentication", "validation"]
        
        complex_count = sum(1 for keyword in complex_keywords if keyword in text_lower)
        medium_count = sum(1 for keyword in medium_keywords if keyword in text_lower)
        
        if complex_count >= 2:
            return "high"
        elif medium_count >= 2 or complex_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline information if present."""
        # Simple regex-like extraction (in production, use proper date parsing)
        import re
        
        # Look for common date patterns
        date_patterns = [
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\w+ \d{1,2}, \d{4})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _generate_task_sequence(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a sequence of tasks based on requirements."""
        tasks = []
        task_id = 1
        
        # Task 1: Project Setup
        tasks.append({
            "id": str(uuid4()),
            "task_type": "project_setup",
            "description": f"Set up {requirements['programming_language']} project structure",
            "dependencies": [],
            "estimated_duration": 15,
            "tool_requirements": ["git", "package_manager"],
            "parameters": {
                "language": requirements["programming_language"],
                "framework": requirements["framework"]
            },
            "status": "pending"
        })
        
        # Task 2: Requirements Analysis
        tasks.append({
            "id": str(uuid4()),
            "task_type": "requirements_analysis",
            "description": "Analyze and document requirements",
            "dependencies": [tasks[0]["id"]],
            "estimated_duration": 30,
            "tool_requirements": ["text_editor"],
            "parameters": {
                "complexity": requirements["complexity"]
            },
            "status": "pending"
        })
        
        # Task 3: Core Implementation
        tasks.append({
            "id": str(uuid4()),
            "task_type": "core_implementation",
            "description": "Implement core functionality",
            "dependencies": [tasks[1]["id"]],
            "estimated_duration": 120 if requirements["complexity"] == "high" else 60,
            "tool_requirements": ["code_editor", "linter"],
            "parameters": {
                "language": requirements["programming_language"],
                "framework": requirements["framework"]
            },
            "status": "pending"
        })
        
        # Task 4: Testing (if required)
        if requirements["testing_required"]:
            tasks.append({
                "id": str(uuid4()),
                "task_type": "testing",
                "description": "Write and run tests",
                "dependencies": [tasks[2]["id"]],
                "estimated_duration": 45,
                "tool_requirements": ["test_framework", "test_runner"],
                "parameters": {
                    "language": requirements["programming_language"]
                },
                "status": "pending"
            })
        
        # Task 5: Documentation (if required)
        if requirements["documentation_required"]:
            doc_deps = [tasks[2]["id"]]
            if requirements["testing_required"]:
                doc_deps.append(tasks[-1]["id"])  # Last task (testing)
            
            tasks.append({
                "id": str(uuid4()),
                "task_type": "documentation",
                "description": "Create documentation and README",
                "dependencies": doc_deps,
                "estimated_duration": 30,
                "tool_requirements": ["markdown_editor"],
                "parameters": {
                    "include_api_docs": True,
                    "include_setup_instructions": True
                },
                "status": "pending"
            })
        
        # Task 6: Final Review and Packaging
        final_deps = [tasks[2]["id"]]  # Core implementation
        if requirements["testing_required"]:
            final_deps.append(tasks[-2]["id"] if requirements["documentation_required"] else tasks[-1]["id"])
        if requirements["documentation_required"]:
            final_deps.append(tasks[-1]["id"])
        
        tasks.append({
            "id": str(uuid4()),
            "task_type": "final_review",
            "description": "Final review and package deliverables",
            "dependencies": final_deps,
            "estimated_duration": 20,
            "tool_requirements": ["linter", "formatter"],
            "parameters": {
                "deliverables": requirements["deliverables"]
            },
            "status": "pending"
        })
        
        return tasks


# Convenience function for external use
def create_plan(
    assignment_title: str,
    assignment_description: str = "",
    file_content: List[Dict[str, Any]] = None,
    assignment_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create a plan for an assignment."""
    planner = AssignmentPlanner()
    return planner.create_plan(assignment_title, assignment_description, file_content, assignment_id)
