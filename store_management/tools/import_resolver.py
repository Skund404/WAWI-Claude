

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ImportResolver:
    """
    Advanced import resolution and circular import management tool.
    """

    @inject(MaterialService)
        def __init__(self, project_root: str):
        """
        Initialize the import resolver.

        Args:
            project_root (str): Root directory of the Python project
        """
        self.project_root = os.path.abspath(project_root)
        self.import_graph: Dict[str, Set[str]] = {}
        self.circular_imports: List[Tuple[str, str]] = []
        self.import_suggestions: List[str] = []

        @inject(MaterialService)
            def find_python_files(self) -> List[str]:
        """
        Find all Python files in the project.

        Returns:
            List[str]: Paths to Python files
        """
        python_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(os.path.join(root, file))
        return python_files

        @inject(MaterialService)
            def parse_imports(self, file_path: str) -> Dict[str, Set[str]]:
        """
        Parse imports from a Python file.

        Args:
            file_path (str): Path to the Python file

        Returns:
            Dict[str, Set[str]]: Dictionary of import types and their modules
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                print(f'Syntax error in {file_path}')
                return {}
        imports = {'import': set(), 'from_import': set(), 'relative_import':
                   set()}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports['import'].add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.level > 0:
                        imports['relative_import'].add(node.module or '')
                    else:
                        imports['from_import'].add(node.module.split('.')[0])
        return imports

        @inject(MaterialService)
            def build_import_graph(self):
        """
        Build a comprehensive graph of import dependencies across the project.
        """
        python_files = self.find_python_files()
        for file_path in python_files:
            rel_path = os.path.relpath(file_path, self.project_root)
            module_path = rel_path.replace(os.path.sep, '.')[:-3]
            imports = self.parse_imports(file_path)
            self.import_graph[module_path] = imports

        @inject(MaterialService)
            def detect_circular_imports(self):
        """
        Detect circular imports in the project.

        Builds a more sophisticated circular import detection mechanism.
        """
        self.build_import_graph()
        self.circular_imports.clear()

        def dfs_cycle_detect(module, path=None):
            if path is None:
                path = []
            path.append(module)
            for import_type, imported_modules in self.import_graph.get(module,
                                                                       {}).items():
                for imported in imported_modules:
                    if imported in path:
                        cycle_start = path.index(imported)
                        cycle = path[cycle_start:]
                        self.circular_imports.append(tuple(cycle))
                    else:
                        dfs_cycle_detect(imported, path.copy())
            path.pop()
        for module in self.import_graph:
            dfs_cycle_detect(module)

        @inject(MaterialService)
            def generate_import_report(self) -> str:
        """
        Generate a detailed report of import analysis.

        Returns:
            str: Formatted report of import dependencies and issues
        """
        self.detect_circular_imports()
        report = 'Import Analysis Report\n'
        report += '=' * 40 + '\n\n'
        if not self.circular_imports:
            report += 'No Circular Imports Detected.\n\n'
        else:
            report += 'Circular Imports Detected:\n'
            for cycle in self.circular_imports:
                report += f"  Cycle: {' -> '.join(cycle)}\n"
            report += '\n'
        report += 'Import Dependency Graph:\n'
        for module, imports in self.import_graph.items():
            report += f'  {module}:\n'
            for import_type, modules in imports.items():
                if modules:
                    report += f"    {import_type}: {', '.join(modules)}\n"
        return report

        @inject(MaterialService)
            def suggest_import_fixes(self) -> List[str]:
        """
        Generate suggestions for resolving import issues.

        Returns:
            List[str]: Suggestions for fixing import problems
        """
        suggestions = []
        for cycle in self.circular_imports:
            suggestion = f"""Circular Import Cycle: {' -> '.join(cycle)}
Suggested Fixes:
  1. Use lazy imports (import inside functions)
  2. Create an intermediate interface module
  3. Restructure module dependencies
  4. Use type hints with TYPE_CHECKING
  5. Consider dependency injection
"""
            suggestions.append(suggestion)
        suggestions.append(
            """General Import Optimization:
  - Minimize cross-module dependencies
  - Use absolute imports
  - Avoid star imports
  - Group and organize imports
"""
        )
        return suggestions

        @inject(MaterialService)
            def fix_imports_in_file(self, file_path: str):
        """
        Attempt to automatically fix imports in a single file.

        Args:
            file_path (str): Path to the Python file to fix
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        import_patterns = ['^import\\s+[\\w.]+',
                           '^from\\s+[\\w.]+\\s+import\\s+[\\w*.,\\s]+']
        imports = []
        other_content = []
        for line in content.split('\n'):
            if any(re.match(pattern, line.strip()) for pattern in
                   import_patterns):
                imports.append(line)
            else:
                other_content.append(line)
        imports.sort()
        grouped_imports = {'stdlib': [], 'third_party': [], 'local': []}
        for imp in imports:
            if imp.startswith('import sys') or imp.startswith('from os'):
                grouped_imports['stdlib'].append(imp)
            elif imp.startswith('import ') or imp.startswith('from '):
                if imp.split()[1].startswith(('store_management',
                                              'database', 'services')):
                    grouped_imports['local'].append(imp)
                else:
                    grouped_imports['third_party'].append(imp)
        fixed_content = []
        for category in ['stdlib', 'third_party', 'local']:
            if grouped_imports[category]:
                fixed_content.extend(grouped_imports[category])
                fixed_content.append('')
        fixed_content.extend(other_content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_content))

        @inject(MaterialService)
            def run(self):
        """
        Run comprehensive import analysis and fixes.
        """
        print('Running Import Resolver...')
        report = self.generate_import_report()
        print(report)
        suggestions = self.suggest_import_fixes()
        print('\nImport Fix Suggestions:')
        for suggestion in suggestions:
            print(suggestion)


def main():
    """
    Main function to run the import resolver.
    """
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    resolver = ImportResolver(project_root)
    resolver.run()


if __name__ == '__main__':
    main()
