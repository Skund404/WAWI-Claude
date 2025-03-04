# utils/import_optimizer.py
import os
import sys
import ast
import importlib
import pkgutil
import traceback
from typing import Dict, List, Set, Any


class ImportOptimizer:
    """
    Comprehensive import analysis and optimization utility.
    """

    @classmethod
    def optimize_imports(cls, project_root: str) -> Dict[str, Any]:
        """
        Perform comprehensive import optimization for a project.

        Args:
            project_root (str): Root directory of the project

        Returns:
            Dict containing optimization analysis results
        """
        # Ensure project root is in Python path
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Initialize results dictionary
        results = {
            'total_modules': 0,
            'circular_dependencies': {},
            'optimization_suggestions': {},
            'unused_imports': {}
        }

        # Find all Python modules in the project
        modules = cls._find_python_modules(project_root)
        results['total_modules'] = len(modules)

        # Analyze each module
        for module_path in modules:
            try:
                # Relative path from project root
                rel_path = os.path.relpath(module_path, project_root)
                module_name = rel_path.replace(os.path.sep, '.')[:-3]  # Remove .py extension

                # Analyze imports
                module_results = cls._analyze_module_imports(module_path)

                # Store results if any findings
                if module_results['circular_dependencies']:
                    results['circular_dependencies'][module_name] = module_results['circular_dependencies']

                if module_results['optimization_suggestions']:
                    results['optimization_suggestions'][module_name] = module_results['optimization_suggestions']

                if module_results['unused_imports']:
                    results['unused_imports'][module_name] = module_results['unused_imports']

            except Exception as e:
                print(f"Error analyzing {module_path}: {e}")
                traceback.print_exc()

        return results

    @classmethod
    def _find_python_modules(cls, project_root: str) -> List[str]:
        """
        Find all Python modules in the project.

        Args:
            project_root (str): Root directory to search

        Returns:
            List of full paths to Python modules
        """
        python_modules = []
        for root, _, files in os.walk(project_root):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    full_path = os.path.join(root, file)
                    python_modules.append(full_path)
        return python_modules

    @classmethod
    def _analyze_module_imports(cls, module_path: str) -> Dict[str, List[str]]:
        """
        Analyze imports in a single module.

        Args:
            module_path (str): Full path to the Python module

        Returns:
            Dictionary with import analysis results
        """
        with open(module_path, 'r') as file:
            try:
                module_ast = ast.parse(file.read())
            except SyntaxError:
                return {
                    'circular_dependencies': [],
                    'optimization_suggestions': [],
                    'unused_imports': []
                }

        # Track imports and their usage
        imports = {}
        used_names = set()
        circular_dependencies = []
        optimization_suggestions = []
        unused_imports = []

        # Analyze module
        for node in ast.walk(module_ast):
            # Track import statements
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                cls._process_import_node(node, imports)

            # Track name usage
            if isinstance(node, (ast.Name, ast.Attribute)):
                used_names.add(getattr(node, 'id', None))

        # Identify unused imports and potential optimizations
        for import_name, details in imports.items():
            # Check for unused imports
            if import_name not in used_names:
                unused_imports.append(f"{details['type']}: {import_name}")

            # Suggest import optimizations
            if details['type'] == 'from' and details['module'] == 'typing':
                optimization_suggestions.append(f"Consider using typing.TYPE_CHECKING for {import_name}")

        # Detect potential circular dependencies (simplified)
        try:
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            imported_module_names = [imp for imp in imports.keys()]
            if module_name in imported_module_names:
                circular_dependencies.append(f"Potential self-import or circular dependency")
        except Exception:
            pass

        return {
            'circular_dependencies': circular_dependencies,
            'optimization_suggestions': optimization_suggestions,
            'unused_imports': unused_imports
        }

    @classmethod
    def _process_import_node(cls, node: ast.AST, imports: Dict[str, Dict[str, str]]):
        """
        Process import nodes to extract import details.

        Args:
            node (ast.AST): Import AST node
            imports (Dict): Dictionary to store import details
        """
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.name] = {
                    'type': 'import',
                    'module': alias.name,
                    'asname': alias.asname
                }

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                imports[alias.name] = {
                    'type': 'from',
                    'module': module,
                    'name': alias.name,
                    'asname': alias.asname
                }