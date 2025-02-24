

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class ImportAnalyzer:
    """
    A tool to analyze and fix circular import issues in a Python project.
    """

        @inject(MaterialService)
        def __init__(self, project_root: str):
        """
        Initialize the import analyzer.

        Args:
            project_root (str): Root directory of the Python project
        """
        self.project_root = os.path.abspath(project_root)
        self.import_graph: Dict[str, Set[str]] = {}
        self.circular_imports: List[Tuple[str, str]] = []

        @inject(MaterialService)
        def find_python_files(self) ->List[str]:
        """
        Find all Python files in the project.

        Returns:
            List[str]: Paths to Python files
        """
        python_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

        @inject(MaterialService)
        def parse_imports(self, file_path: str) ->Set[str]:
        """
        Parse imports from a Python file.

        Args:
            file_path (str): Path to the Python file

        Returns:
            Set[str]: Set of imported module names
        """
        with open(file_path, 'r') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                print(f'Syntax error in {file_path}')
                return set()
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports

        @inject(MaterialService)
        def build_import_graph(self):
        """
        Build a graph of import dependencies across the project.
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
        """
        self.build_import_graph()
        for module, dependencies in self.import_graph.items():
            for dep in dependencies:
                if module in self.import_graph.get(dep, set()):
                    self.circular_imports.append((module, dep))

        @inject(MaterialService)
        def generate_import_report(self) ->str:
        """
        Generate a report of circular imports.

        Returns:
            str: Formatted report of circular imports
        """
        self.detect_circular_imports()
        if not self.circular_imports:
            return 'No circular imports detected.'
        report = 'Circular Imports Detected:\n'
        for mod1, mod2 in self.circular_imports:
            report += f'  - {mod1} <-> {mod2}\n'
        return report

        @inject(MaterialService)
        def fix_circular_imports(self):
        """
        Attempt to fix circular imports by suggesting refactoring strategies.
        """
        fix_suggestions = []
        for mod1, mod2 in self.circular_imports:
            suggestion = f"""Circular Import between {mod1} and {mod2}:
Suggested Fixes:
  1. Use lazy imports (import inside functions)
  2. Restructure to use dependency injection
  3. Create an intermediate interface module
  4. Use type hints with TYPE_CHECKING
"""
            fix_suggestions.append(suggestion)
        return '\n\n'.join(fix_suggestions)


def main():
    """
    Main function to run the import analyzer.
    """
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    analyzer = ImportAnalyzer(project_root)
    print('Import Analysis Report:')
    print('-' * 40)
    print(analyzer.generate_import_report())
    print('\nImport Fix Suggestions:')
    print('-' * 40)
    print(analyzer.fix_circular_imports())


if __name__ == '__main__':
    main()
