from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

# F:\WAWI Homebrew\WAWI Claude\store_management\tools\dependency_migration.py

import os
import sys
import re
import logging
from typing import List, Optional


# Avoid using astor to prevent potential issues
class SimpleASTTransformer:
    """
    Simplified AST transformation without external libraries.
    """

    @staticmethod
    def transform_imports(content: str) -> str:
        """
        Simple import transformation.

        Args:
            content (str): File content

        Returns:
            Transformed file content
        """
        # Remove existing imports if present
        lines = content.split("\n")

        # Remove specific imports
        filtered_lines = [
            line
            for line in lines
            if not (
                line.strip().startswith("from di.core import inject")
                or line.strip().startswith("from services.interfaces import")
            )
        ]

        # Add new imports at the top
        new_imports = [
            "from di.core import inject",
            "from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService",
        ]

        # Insert imports after existing imports and before first non-import line
        import_inserted = False
        final_lines = []
        import_block_ended = False

        for line in filtered_lines:
            # Skip empty lines
            if not line.strip():
                final_lines.append(line)
                continue

            # Check if we're still in the import block
            is_import_line = line.strip().startswith(
                "import "
            ) or line.strip().startswith("from ")

            if not import_block_ended and is_import_line:
                final_lines.append(line)
                continue

            # First non-import line
            if not import_block_ended:
                # Insert new imports before first non-import line
                final_lines.extend(new_imports)
                import_block_ended = True

            final_lines.append(line)

        return "\n".join(final_lines)

    @staticmethod
    def transform_methods(content: str) -> str:
        """
        Add inject decorator to methods.

        Args:
            content (str): File content

        Returns:
            Transformed file content
        """
        lines = content.split("\n")
        final_lines = []

        # Track method indentation and decorator state
        for i, line in enumerate(lines):
            # Look for method definitions
            if re.match(r"^(\s*)def\s+\w+\(self", line):
                # Add inject decorator
                final_lines.append(
                    f'{" " * (len(line.split("def")[0]))}@inject(MaterialService)'
                )

            final_lines.append(line)

        return "\n".join(final_lines)


class DependencyMigrationTool:
    """
    Automated tool for migrating project dependencies.
    """

    @inject(MaterialService)
        def __init__(self, project_root: str):
        """
        Initialize the migration tool.

        Args:
            project_root (str): Root directory of the project
        """
        self.project_root = os.path.abspath(project_root)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @inject(MaterialService)
        def find_python_files(self) -> List[str]:
        """
        Find all Python files in the project.

        Returns:
            List of Python file paths
        """
        python_files = []
        ignore_dirs = {
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "site-packages",
            "build",
            "dist",
        }

        for root, dirs, files in os.walk(self.project_root):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    full_path = os.path.join(root, file)

                    # Additional filter to ensure it's within project
                    if self.project_root in full_path:
                        python_files.append(full_path)

        return python_files

    @inject(MaterialService)
        def migrate_file(self, file_path: str):
        """
        Migrate a single Python file.

        Args:
            file_path (str): Path to the Python file
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Transform imports
            content = SimpleASTTransformer.transform_imports(content)

            # Transform methods to add inject decorator
            content = SimpleASTTransformer.transform_methods(content)

            # Write back to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Migrated: {file_path}")

        except Exception as e:
            self.logger.error(f"Error migrating {file_path}: {e}")

    @inject(MaterialService)
        def migrate_project(self):
        """
        Migrate entire project dependencies.
        """
        # Find Python files
        python_files = self.find_python_files()

        # Migrate files
        for file_path in python_files:
            self.migrate_file(file_path)

        self.logger.info("Dependency migration completed")

    @inject(MaterialService)
        def register_services(self):
        """
        Generate service registration script.
        """
        registration_script = """
# Service Registration Script
from di.core import DependencyContainer
from services.implementations.material_service import MaterialServiceImpl
from services.implementations.project_service import ProjectServiceImpl

# Register service implementations
DependencyContainer.register(MaterialService, MaterialServiceImpl)
DependencyContainer.register(ProjectService, ProjectServiceImpl)
"""


# Write registration script
registration_path = os.path.join(
    self.project_root, "store_management", "services", "service_registration.py"
)

# Ensure directory exists
os.makedirs(os.path.dirname(registration_path), exist_ok=True)

with open(registration_path, "w", encoding="utf-8") as f:
    f.write(registration_script)

    self.logger.info(
        f"Service registration script created: {registration_path}")


def main():
    """
    Main entry point for dependency migration.
    """
    # Specify the exact project root
    project_root = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", ".."))

    # Validate project root
    if not os.path.exists(os.path.join(project_root, "store_management")):
        print(f"Invalid project root: {project_root}")
        print("Please ensure the script is run from the correct location.")
        return

    # Create migration tool
    migration_tool = DependencyMigrationTool(project_root)

    # Run migration
    migration_tool.migrate_project()

    # Generate service registration
    migration_tool.register_services()


if __name__ == "__main__":
    main()
