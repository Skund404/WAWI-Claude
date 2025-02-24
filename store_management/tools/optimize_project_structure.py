# /tools/fix_project_structure.py

"""
A comprehensive script to fix various structural issues in the store_management project.
This script handles:
1. Code cleanup and consolidation
2. Directory structure optimization
3. Backup management
4. Log centralization
5. Service deduplication
6. Configuration standardization

Author: Project Optimization Team
Date: 2024-02-24
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
import re
import time
from datetime import datetime
import ast
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_fixes.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ProjectFixer:
    """Implements fixes for identified project issues."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.backup_path = None
        self.centralized_logs_dir = self.project_root / 'logs'
        self.centralized_backups_dir = self.project_root / 'backups'

    def fix_all(self) -> None:
        """Execute all fixes in the correct order."""
        try:
            logger.info("Starting project fixes...")

            # Create backup
            self._create_backup()

            # Execute fixes in order
            self.centralize_logs()
            self.consolidate_backups()
            self.clean_duplicate_files()
            self.remove_redundant_paths()
            self.fix_syntax_errors()
            self.consolidate_services()
            self.standardize_configs()

            logger.info("Project fixes completed successfully")

        except Exception as e:
            logger.error(f"Error during fixes: {e}")
            self._restore_backup()
            raise

    def centralize_logs(self) -> None:
        """Centralize all log files into a single directory."""
        logger.info("Centralizing log files...")

        # Ensure centralized logs directory exists
        self.centralized_logs_dir.mkdir(exist_ok=True)

        # Find all log files
        log_files = list(self.project_root.rglob("*.log"))

        for log_file in log_files:
            if self.centralized_logs_dir in log_file.parents:
                continue

            # Create new log name with directory prefix
            new_name = f"{log_file.parent.name}_{log_file.name}"
            new_path = self.centralized_logs_dir / new_name

            try:
                # Move log file
                if log_file.exists():
                    shutil.move(str(log_file), str(new_path))
                    logger.info(f"Moved {log_file} to {new_path}")
            except Exception as e:
                logger.error(f"Error moving log file {log_file}: {e}")

    def consolidate_backups(self) -> None:
        """Consolidate all backup files into a single directory."""
        logger.info("Consolidating backup files...")

        # Ensure centralized backups directory exists
        self.centralized_backups_dir.mkdir(exist_ok=True)

        # Find all backup files
        backup_files = []
        backup_files.extend(self.project_root.rglob("*.bak"))
        backup_files.extend(self.project_root.rglob("*.backup"))
        backup_files.extend(self.project_root.rglob("*_backup_*"))

        for backup_file in backup_files:
            if self.centralized_backups_dir in backup_file.parents:
                continue

            # Create new backup name with timestamp
            timestamp = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
            new_name = f"{backup_file.parent.name}_{backup_file.stem}_{timestamp}{backup_file.suffix}"
            new_path = self.centralized_backups_dir / new_name

            try:
                # Move backup file
                if backup_file.exists():
                    shutil.move(str(backup_file), str(new_path))
                    logger.info(f"Moved {backup_file} to {new_path}")
            except Exception as e:
                logger.error(f"Error moving backup file {backup_file}: {e}")

    def clean_duplicate_files(self) -> None:
        """Remove duplicate implementations and consolidate code."""
        logger.info("Cleaning duplicate files...")

        # Check for duplicate service implementations
        service_files = list((self.project_root / 'services').rglob("*.py"))
        implementation_map: Dict[str, List[Path]] = {}

        for service_file in service_files:
            if service_file.name == "__init__.py":
                continue

            # Group by base name (without _service suffix)
            base_name = service_file.stem.replace('_service', '')
            if base_name not in implementation_map:
                implementation_map[base_name] = []
            implementation_map[base_name].append(service_file)

        # Consolidate duplicates
        for base_name, implementations in implementation_map.items():
            if len(implementations) > 1:
                logger.info(f"Found duplicate implementations for {base_name}")
                self._consolidate_implementations(base_name, implementations)

    def remove_redundant_paths(self) -> None:
        """Remove redundant path structures."""
        logger.info("Removing redundant paths...")

        redundant_paths = [
            self.project_root / "path",
            self.project_root / "database/sqlalchemy/path"
        ]

        for path in redundant_paths:
            if path.exists():
                try:
                    shutil.rmtree(path)
                    logger.info(f"Removed redundant path: {path}")
                except Exception as e:
                    logger.error(f"Error removing path {path}: {e}")

    def fix_syntax_errors(self) -> None:
        """Fix identified syntax errors in Python files."""
        logger.info("Fixing syntax errors...")

        files_to_fix = {
            self.project_root / "pyproject.toml.py": self._fix_pyproject_toml,
            self.project_root / "database/sqlalchemy/mixins/validation_mixing.py": self._fix_validation_mixing
        }

        for file_path, fix_func in files_to_fix.items():
            if file_path.exists():
                try:
                    fix_func(file_path)
                    logger.info(f"Fixed syntax in {file_path}")
                except Exception as e:
                    logger.error(f"Error fixing {file_path}: {e}")

    def consolidate_services(self) -> None:
        """Consolidate service implementations using best practices."""
        logger.info("Consolidating services...")

        services_dir = self.project_root / "services"
        implementations_dir = services_dir / "implementations"
        interfaces_dir = services_dir / "interfaces"

        # Ensure directory structure
        implementations_dir.mkdir(exist_ok=True)
        interfaces_dir.mkdir(exist_ok=True)

        # Move and consolidate service implementations
        service_files = list(services_dir.glob("*.py"))
        for service_file in service_files:
            if service_file.name == "__init__.py":
                continue

            if "_service" in service_file.name.lower():
                try:
                    # Move to implementations if not already there
                    if service_file.parent == services_dir:
                        new_path = implementations_dir / service_file.name
                        shutil.move(str(service_file), str(new_path))
                        logger.info(f"Moved {service_file} to implementations directory")
                except Exception as e:
                    logger.error(f"Error moving service file {service_file}: {e}")

    def standardize_configs(self) -> None:
        """Standardize configuration management."""
        logger.info("Standardizing configurations...")

        config_dir = self.project_root / "config"
        config_files = list(config_dir.glob("*.py"))

        # Collect all config settings
        all_configs = {}
        for config_file in config_files:
            if config_file.name == "__init__.py":
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                # Extract configuration variables
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                all_configs[target.id] = {
                                    'file': config_file.name,
                                    'value': self._get_value_from_node(node.value)
                                }
            except Exception as e:
                logger.error(f"Error analyzing config file {config_file}: {e}")

        # Create centralized configuration
        self._create_centralized_config(all_configs)

    def _fix_pyproject_toml(self, file_path: Path) -> None:
        """Fix syntax in pyproject.toml.py."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix common syntax error in pyproject.toml.py
        fixed_content = content.replace(" = ", " == ")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

    def _fix_validation_mixing(self, file_path: Path) -> None:
        """Fix syntax in validation_mixing.py."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix missing parentheses
        fixed_content = re.sub(r'class (\w+):', r'class \1():', content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

    def _consolidate_implementations(self, base_name: str, implementations: List[Path]) -> None:
        """Consolidate multiple implementations into a single best version."""
        # Sort by modification time to keep the most recent
        implementations.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Keep the most recent implementation
        keeper = implementations[0]

        # Move others to backup
        for impl in implementations[1:]:
            backup_path = self.centralized_backups_dir / f"{impl.stem}_deprecated_{time.strftime('%Y%m%d_%H%M%S')}{impl.suffix}"
            shutil.move(str(impl), str(backup_path))
            logger.info(f"Moved duplicate implementation {impl} to {backup_path}")

    def _create_centralized_config(self, configs: Dict[str, Any]) -> None:
        """Create a centralized configuration file."""
        config_path = self.project_root / "config" / "configuration.py"

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('"""Centralized configuration management."""\n\n')

            # Write imports
            f.write('import os\n')
            f.write('from pathlib import Path\n\n')

            # Write configuration class
            f.write('class Configuration:\n')
            f.write('    """Central configuration management class."""\n\n')

            # Write config values
            for name, details in configs.items():
                value = details['value']
                f.write(f'    {name} = {value!r}  # from {details["file"]}\n')

    def _create_backup(self) -> None:
        """Create a backup of the project."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.project_root.parent / f"{self.project_root.name}_backup_{timestamp}"
        shutil.copytree(self.project_root, self.backup_path)
        logger.info(f"Created backup at {self.backup_path}")

    def _restore_backup(self) -> None:
        """Restore from backup if available."""
        if self.backup_path and self.backup_path.exists():
            shutil.rmtree(self.project_root)
            shutil.copytree(self.backup_path, self.project_root)
            logger.info("Restored from backup")

    def _get_value_from_node(self, node: ast.AST) -> Any:
        """Convert AST node to Python value."""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.Dict):
            return {
                self._get_value_from_node(k): self._get_value_from_node(v)
                for k, v in zip(node.keys, node.values)
            }
        return str(ast.dump(node))


def main() -> None:
    """Main entry point for the script."""
    try:
        # Get project root from command line or use default
        if len(sys.argv) > 1:
            project_root = Path(sys.argv[1])
        else:
            project_root = Path(__file__).resolve().parent.parent

        # Validate project root
        if not project_root.exists():
            raise FileNotFoundError(f"Project root not found: {project_root}")

        # Create and run fixer
        fixer = ProjectFixer(project_root)
        fixer.fix_all()

    except Exception as e:
        logger.error(f"Project fixes failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()