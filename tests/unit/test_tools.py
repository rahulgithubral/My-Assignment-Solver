"""
Unit tests for the agent tools.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from agent.tools.code_gen import CodeGenerator
from agent.tools.git_util import GitManager
from agent.tools.test_runner import TestRunner


class TestCodeGenerator:
    """Test cases for the CodeGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.code_gen = CodeGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_project_structure_python(self):
        """Test Python project structure creation."""
        result = self.code_gen.create_project_structure(
            language="python",
            framework="fastapi",
            output_dir=self.temp_dir
        )
        
        assert result["language"] == "python"
        assert result["framework"] == "fastapi"
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that files were actually created
        assert os.path.exists(os.path.join(self.temp_dir, "main.py"))
        assert os.path.exists(os.path.join(self.temp_dir, "requirements.txt"))
        assert os.path.exists(os.path.join(self.temp_dir, "README.md"))
    
    def test_create_project_structure_javascript(self):
        """Test JavaScript project structure creation."""
        result = self.code_gen.create_project_structure(
            language="javascript",
            framework="react",
            output_dir=self.temp_dir
        )
        
        assert result["language"] == "javascript"
        assert result["framework"] == "react"
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that files were actually created
        assert os.path.exists(os.path.join(self.temp_dir, "package.json"))
        assert os.path.exists(os.path.join(self.temp_dir, "index.js"))
        assert os.path.exists(os.path.join(self.temp_dir, "README.md"))
    
    def test_create_project_structure_java(self):
        """Test Java project structure creation."""
        result = self.code_gen.create_project_structure(
            language="java",
            framework="spring",
            output_dir=self.temp_dir
        )
        
        assert result["language"] == "java"
        assert result["framework"] == "spring"
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that files were actually created
        assert os.path.exists(os.path.join(self.temp_dir, "src", "main", "java", "Main.java"))
        assert os.path.exists(os.path.join(self.temp_dir, "pom.xml"))
        assert os.path.exists(os.path.join(self.temp_dir, "README.md"))
    
    def test_create_requirements_doc(self):
        """Test requirements document creation."""
        result = self.code_gen.create_requirements_doc(self.temp_dir)
        
        assert isinstance(result, str)
        assert os.path.exists(result)
        assert result.endswith("REQUIREMENTS.md")
        
        # Check content
        with open(result, 'r') as f:
            content = f.read()
            assert "Requirements Analysis" in content
            assert "Functional Requirements" in content
    
    def test_create_sample_implementation_python(self):
        """Test Python sample implementation creation."""
        result = self.code_gen.create_sample_implementation(
            language="python",
            output_dir=self.temp_dir
        )
        
        assert result["language"] == "python"
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that sample file was created
        sample_file = os.path.join(self.temp_dir, "sample_module.py")
        assert os.path.exists(sample_file)
        
        # Check content
        with open(sample_file, 'r') as f:
            content = f.read()
            assert "SampleClass" in content
            assert "sample_function" in content
    
    def test_create_sample_implementation_javascript(self):
        """Test JavaScript sample implementation creation."""
        result = self.code_gen.create_sample_implementation(
            language="javascript",
            output_dir=self.temp_dir
        )
        
        assert result["language"] == "javascript"
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that sample file was created
        sample_file = os.path.join(self.temp_dir, "sample_module.js")
        assert os.path.exists(sample_file)
        
        # Check content
        with open(sample_file, 'r') as f:
            content = f.read()
            assert "SampleClass" in content
            assert "sampleFunction" in content
    
    def test_create_documentation(self):
        """Test documentation creation."""
        result = self.code_gen.create_documentation(
            output_dir=self.temp_dir,
            include_api_docs=True
        )
        
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that documentation files were created
        setup_doc = os.path.join(self.temp_dir, "SETUP.md")
        assert os.path.exists(setup_doc)
        
        api_doc = os.path.join(self.temp_dir, "API.md")
        assert os.path.exists(api_doc)
    
    def test_create_documentation_no_api_docs(self):
        """Test documentation creation without API docs."""
        result = self.code_gen.create_documentation(
            output_dir=self.temp_dir,
            include_api_docs=False
        )
        
        assert "files_created" in result
        assert len(result["files_created"]) > 0
        
        # Check that setup doc was created but not API doc
        setup_doc = os.path.join(self.temp_dir, "SETUP.md")
        assert os.path.exists(setup_doc)
        
        api_doc = os.path.join(self.temp_dir, "API.md")
        assert not os.path.exists(api_doc)


class TestGitManager:
    """Test cases for the GitManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.git_manager = GitManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init_repository(self):
        """Test Git repository initialization."""
        result = self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        assert result["status"] == "success"
        assert result["repo_path"] == self.temp_dir
        assert result["initial_commit"] is True
        
        # Check that .git directory was created
        assert os.path.exists(os.path.join(self.temp_dir, ".git"))
        
        # Check that .gitignore was created
        assert os.path.exists(os.path.join(self.temp_dir, ".gitignore"))
    
    def test_init_repository_no_initial_commit(self):
        """Test Git repository initialization without initial commit."""
        result = self.git_manager.init_repository(self.temp_dir, initial_commit=False)
        
        assert result["status"] == "success"
        assert result["repo_path"] == self.temp_dir
        assert result["initial_commit"] is False
        
        # Check that .git directory was created
        assert os.path.exists(os.path.join(self.temp_dir, ".git"))
    
    def test_add_files(self):
        """Test adding files to Git."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=False)
        
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = self.git_manager.add_files(self.temp_dir, files=["test.txt"])
        
        assert result["status"] == "success"
        assert result["files_added"] == ["test.txt"]
    
    def test_add_all_files(self):
        """Test adding all files to Git."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=False)
        
        # Create test files
        test_file1 = os.path.join(self.temp_dir, "test1.txt")
        test_file2 = os.path.join(self.temp_dir, "test2.txt")
        with open(test_file1, 'w') as f:
            f.write("test content 1")
        with open(test_file2, 'w') as f:
            f.write("test content 2")
        
        result = self.git_manager.add_files(self.temp_dir, files=None)
        
        assert result["status"] == "success"
        assert result["files_added"] == "all"
    
    def test_commit_changes(self):
        """Test committing changes."""
        # Initialize repository and add files
        self.git_manager.init_repository(self.temp_dir, initial_commit=False)
        
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        self.git_manager.add_files(self.temp_dir, files=["test.txt"])
        
        result = self.git_manager.commit_changes(self.temp_dir, "Test commit")
        
        assert result["status"] == "success"
        assert result["commit_message"] == "Test commit"
    
    def test_create_branch(self):
        """Test creating a new branch."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        result = self.git_manager.create_branch(self.temp_dir, "feature-branch", checkout=True)
        
        assert result["status"] == "success"
        assert result["branch_name"] == "feature-branch"
        assert result["checked_out"] is True
    
    def test_get_status(self):
        """Test getting Git status."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        result = self.git_manager.get_status(self.temp_dir)
        
        assert result["status"] == "success"
        assert "current_branch" in result
        assert "last_commit" in result
        assert "modified_files" in result
        assert "untracked_files" in result
        assert "is_clean" in result
    
    def test_add_remote(self):
        """Test adding a remote repository."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        result = self.git_manager.add_remote(
            self.temp_dir,
            "origin",
            "https://github.com/test/repo.git"
        )
        
        assert result["status"] == "success"
        assert result["remote_name"] == "origin"
        assert result["remote_url"] == "https://github.com/test/repo.git"
    
    def test_create_tag(self):
        """Test creating a Git tag."""
        # Initialize repository first
        self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        result = self.git_manager.create_tag(self.temp_dir, "v1.0.0", "Version 1.0.0")
        
        assert result["status"] == "success"
        assert result["tag_name"] == "v1.0.0"
        assert result["tag_message"] == "Version 1.0.0"
    
    def test_get_commit_history(self):
        """Test getting commit history."""
        # Initialize repository and make a commit
        self.git_manager.init_repository(self.temp_dir, initial_commit=True)
        
        result = self.git_manager.get_commit_history(self.temp_dir, limit=5)
        
        assert result["status"] == "success"
        assert "commits" in result
        assert "total_commits" in result
        assert result["total_commits"] > 0


class TestTestRunner:
    """Test cases for the TestRunner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_runner = TestRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_run_tests_python(self):
        """Test running Python tests."""
        result = self.test_runner.run_tests("python", self.temp_dir)
        
        assert "status" in result
        assert "tests_run" in result
        assert "tests_passed" in result
        assert "tests_failed" in result
        
        # Check that a sample test file was created
        test_file = os.path.join(self.temp_dir, "test_sample.py")
        assert os.path.exists(test_file)
    
    def test_run_tests_javascript(self):
        """Test running JavaScript tests."""
        result = self.test_runner.run_tests("javascript", self.temp_dir)
        
        assert "status" in result
        assert "tests_run" in result
        assert "tests_passed" in result
        assert "tests_failed" in result
        
        # Check that a sample test file was created
        test_file = os.path.join(self.temp_dir, "test_sample.js")
        assert os.path.exists(test_file)
    
    def test_run_tests_java(self):
        """Test running Java tests."""
        result = self.test_runner.run_tests("java", self.temp_dir)
        
        assert "status" in result
        assert "tests_run" in result
        assert "tests_passed" in result
        assert "tests_failed" in result
        
        # Check that a sample test file was created
        test_file = os.path.join(self.temp_dir, "TestSample.java")
        assert os.path.exists(test_file)
    
    def test_run_tests_with_pattern(self):
        """Test running tests with a specific pattern."""
        result = self.test_runner.run_tests("python", self.temp_dir, test_pattern="basic")
        
        assert "status" in result
        assert "tests_run" in result
        assert "tests_passed" in result
        assert "tests_failed" in result
    
    def test_run_tests_unknown_language(self):
        """Test running tests for unknown language."""
        result = self.test_runner.run_tests("unknown", self.temp_dir)
        
        assert result["status"] == "skipped"
        assert "not implemented" in result["message"].lower()
        assert result["tests_run"] == 0
        assert result["tests_passed"] == 0
        assert result["tests_failed"] == 0
    
    def test_get_test_coverage_python(self):
        """Test getting Python test coverage."""
        result = self.test_runner.get_test_coverage("python", self.temp_dir)
        
        # Coverage might not be available, so we just check the structure
        assert "status" in result
    
    def test_get_test_coverage_javascript(self):
        """Test getting JavaScript test coverage."""
        result = self.test_runner.get_test_coverage("javascript", self.temp_dir)
        
        # Coverage might not be available, so we just check the structure
        assert "status" in result
    
    def test_get_test_coverage_unsupported(self):
        """Test getting test coverage for unsupported language."""
        result = self.test_runner.get_test_coverage("java", self.temp_dir)
        
        assert result["status"] == "not_supported"
        assert "not implemented" in result["message"].lower()
    
    def test_create_sample_python_test(self):
        """Test creating sample Python test file."""
        self.test_runner._create_sample_python_test(self.temp_dir)
        
        test_file = os.path.join(self.temp_dir, "test_sample.py")
        assert os.path.exists(test_file)
        
        # Check content
        with open(test_file, 'r') as f:
            content = f.read()
            assert "TestSample" in content
            assert "test_basic_math" in content
            assert "test_string_operations" in content
            assert "test_list_operations" in content
    
    def test_create_sample_javascript_test(self):
        """Test creating sample JavaScript test file."""
        self.test_runner._create_sample_javascript_test(self.temp_dir)
        
        test_file = os.path.join(self.temp_dir, "test_sample.js")
        assert os.path.exists(test_file)
        
        # Check content
        with open(test_file, 'r') as f:
            content = f.read()
            assert "describe" in content
            assert "test" in content
            assert "expect" in content
    
    def test_create_sample_java_test(self):
        """Test creating sample Java test file."""
        self.test_runner._create_sample_java_test(self.temp_dir)
        
        test_file = os.path.join(self.temp_dir, "TestSample.java")
        assert os.path.exists(test_file)
        
        # Check content
        with open(test_file, 'r') as f:
            content = f.read()
            assert "TestSample" in content
            assert "testBasicMath" in content
            assert "testStringOperations" in content
