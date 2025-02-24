

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
@dataclass
class FunctionInfo:
    name: str
    docstring: str
    args: List[str]


@dataclass
class ClassInfo:
    name: str
    docstring: str
    methods: List[FunctionInfo]
    base_classes: List[str]


@dataclass
class FileInfo:
    path: str
    imports: List[str]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    global_variables: List[str]


class ProjectAnalyzer:
    """Main class for analyzing Python project structure"""

        @inject(MaterialService)
        def __init__(self, project_path: str):
        """Initialize analyzer with project path"""
        self.project_path = Path(project_path)
        self.files_info: Dict[str, FileInfo] = {}

        @inject(MaterialService)
        def analyze_project(self) ->Dict:
        """Analyze all Python files in the project directory"""
        for file_path in self.project_path.rglob('*.py'):
            if '__pycache__' not in str(file_path):
                try:
                    self.analyze_file(file_path)
                except Exception as e:
                    print(f'Warning: Could not analyze {file_path}: {str(e)}')
        return self.generate_summary()

        @inject(MaterialService)
        def analyze_file(self, file_path: Path) ->None:
        """Analyze a single Python file and extract its information"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f'Syntax error in {file_path}: {str(e)}')
            return
        imports = []
        classes = []
        functions = []
        global_vars = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    imports.append(f'{module}.{name.name}')
            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class_info(node))
            elif isinstance(node, ast.FunctionDef):
                functions.append(self._extract_function_info(node))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        global_vars.append(target.id)
        relative_path = str(file_path.relative_to(self.project_path))
        self.files_info[relative_path] = FileInfo(path=relative_path,
            imports=imports, classes=classes, functions=functions,
            global_variables=global_vars)
