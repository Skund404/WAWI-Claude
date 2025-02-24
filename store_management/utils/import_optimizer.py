

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ImportOptimizer:
    """
    Advanced import management and optimization utility.
    """
    _import_cache: Dict[str, Any] = {}
    _dependency_graph: Dict[str, Set[str]] = {}
    _circular_imports: Set[tuple] = set()

    @classmethod
    def optimize_imports(cls, project_root: str):
        """
        Optimize import paths and detect potential issues.

        Args:
            project_root (str): Root directory of the project
        """
        key_dirs = [project_root, os.path.join(project_root,
                                               'store_management'), os.path.join(project_root,
                                                                                 'store_management', 'database'), os.path.join(project_root,
                                                                                                                               'store_management', 'services')]
        for directory in key_dirs:
            if directory not in sys.path:
                sys.path.insert(0, directory)

        @classmethod
    def safe_import(cls, module_path: str, class_name: Optional[str] = None
                    ) -> Any:
        """
        Safely import a module or class with advanced caching.

        Args:
            module_path (str): Dot-separated module path
            class_name (Optional[str]): Optional specific class to import

        Returns:
            Imported module or class
        """
        if module_path in cls._import_cache:
            imported = cls._import_cache[module_path]
            return getattr(imported, class_name) if class_name else imported
        try:
            imported = importlib.import_module(module_path)
            cls._import_cache[module_path] = imported
            cls._track_dependencies(module_path)
            return getattr(imported, class_name) if class_name else imported
        except (ImportError, AttributeError) as e:
            print(f'Import Error for {module_path}: {e}')
            raise

        @classmethod
    def _track_dependencies(cls, module_path: str):
        """
        Track module dependencies to detect potential circular imports.

        Args:
            module_path (str): Module path to analyze
        """
        try:
            module = sys.modules[module_path]
            dependencies = set()
            for name, value in module.__dict__.items():
                if hasattr(value, '__module__'):
                    dependencies.add(value.__module__)
            cls._dependency_graph[module_path] = dependencies
            for dep in dependencies:
                if module_path in cls._dependency_graph.get(dep, set()):
                    cls._circular_imports.add((module_path, dep))
        except Exception as e:
            print(f'Error tracking dependencies for {module_path}: {e}')

        @classmethod
    def get_dependency_report(cls) -> Dict:
        """
        Generate a report of module dependencies and potential issues.

        Returns:
            Dict containing dependency and import information
        """
        return {'dependency_graph': cls._dependency_graph,
                'circular_imports': list(cls._circular_imports),
                'cached_imports': list(cls._import_cache.keys())}


ImportOptimizer.optimize_imports(os.path.abspath(os.path.join(os.path.
                                                              dirname(__file__), '..', '..')))
