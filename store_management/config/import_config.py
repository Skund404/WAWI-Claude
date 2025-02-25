from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ImportConfig:
    """
    Centralized configuration for managing Python import paths.
    """

    @staticmethod
    def setup_project_path():
        """
        Automatically add project root and key directories to Python path.

        This helps with import resolution and avoids explicit sys.path modifications.
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(
            __file__), '..'))
        key_dirs = [project_root, os.path.join(project_root,
                                                'store_management'), os.path.join(project_root,
                                                                                  'store_management', 'database'), os.path.join(project_root,
                                                                                                                                   'store_management', 'services')]
        for directory in key_dirs:
            if directory not in sys.path:
                sys.path.insert(0, directory)

    @staticmethod
    def get_project_root() -> str:
        """
        Get the absolute path to the project root.

        Returns:
            str: Absolute path to the project root directory
        """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @staticmethod
    def list_python_modules(directory: str) -> List[str]:
        """
        List all Python modules in a given directory.

        Args:
            directory (str): Path to the directory to search

        Returns:
            List[str]: List of Python module names
        """
        modules = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    relative_path = os.path.relpath(module_path, directory)
                    module_name = relative_path.replace(os.path.sep, '.')[:-3]
                    modules.append(module_name)
        return modules


ImportConfig.setup_project_path()