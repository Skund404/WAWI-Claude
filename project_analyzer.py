# Standard library imports for file operations, AST parsing, and JSON handling
import os
import ast  # Abstract Syntax Tree - for parsing Python code
import json
from typing import Dict, List  # Type hints for better code documentation
from dataclasses import dataclass, asdict  # For creating data classes with less boilerplate
from pathlib import Path  # Modern path manipulation


# Data class for storing function information
@dataclass
class FunctionInfo:
    name: str  # Name of the function
    docstring: str  # Function's documentation string
    args: List[str]  # List of function arguments


# Data class for storing class information
@dataclass
class ClassInfo:
    name: str  # Name of the class
    docstring: str  # Class's documentation string
    methods: List[FunctionInfo]  # List of class methods
    base_classes: List[str]  # List of parent classes


# Data class for storing file information
@dataclass
class FileInfo:
    path: str  # Path to the file
    imports: List[str]  # List of imports in the file
    classes: List[ClassInfo]  # List of classes defined in the file
    functions: List[FunctionInfo]  # List of functions defined in the file
    global_variables: List[str]  # List of global variables


class ProjectAnalyzer:
    """Main class for analyzing Python project structure"""

    def __init__(self, project_path: str):
        """Initialize analyzer with project path"""
        self.project_path = Path(project_path)
        self.files_info: Dict[str, FileInfo] = {}  # Store info for each file

    def analyze_project(self) -> Dict:
        """Analyze all Python files in the project directory"""
        # Recursively find all .py files
        for file_path in self.project_path.rglob("*.py"):
            # Skip __pycache__ directories
            if "__pycache__" not in str(file_path):
                try:
                    self.analyze_file(file_path)
                except Exception as e:
                    print(f"Warning: Could not analyze {file_path}: {str(e)}")
        return self.generate_summary()

    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file and extract its information"""
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the file into an AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {str(e)}")
            return

        # Initialize containers for file information
        imports = []
        classes = []
        functions = []
        global_vars = []

        # Analyze each node in the module body
        for node in tree.body:
            if isinstance(node, ast.Import):
                # Handle direct imports (import x)
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                # Handle from imports (from x import y)
                module = node.module or ''
                for name in node.names:
                    imports.append(f"{module}.{name.name}")
            elif isinstance(node, ast.ClassDef):
                # Handle class definitions
                classes.append(self._extract_class_info(node))
            elif isinstance(node, ast.FunctionDef):
                # Handle function definitions
                functions.append(self._extract_function_info(node))
            elif isinstance(node, ast.Assign):
                # Handle global variable assignments
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)

        # Store file information
        relative_path = str(file_path.relative_to(self.project_path))
        self.files_info[relative_path] = FileInfo(
            path=relative_path,
            imports=imports,
            classes=classes,
            functions=functions,
            global_variables=global_vars
        )
