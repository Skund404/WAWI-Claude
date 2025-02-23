#!/usr/bin/env python3
"""
Comprehensive reorganization script for store_management project.
This script:
1. Reorganizes the file structure
2. Updates import paths
3. Consolidates duplicate implementations
4. Creates a detailed log of changes
"""

import os
import shutil
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple


class ProjectReorganizer:
    """Handles project reorganization tasks."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.log_file = self.project_root / "reorganization_log.md"
        self.changes: List[str] = []

        # Define the new structure
        self.new_structure = {
            "services": {
                "interfaces": ["base_service.py", "pattern_service.py", "leather_inventory_service.py"],
                "implementations": ["pattern_service.py", "leather_inventory_service.py"]
            },
            "repositories": {
                "interfaces": ["base_repository.py", "pattern_repository.py", "leather_repository.py"],
                "implementations": ["pattern_repository.py", "leather_repository.py"]
            },
            "unit_of_work": ["unit_of_work.py", "exceptions.py"]
        }

        # Files to be consolidated
        self.consolidate_files = {
            "services/service_registry.py": ["services/service_registry.py", "di/service_registry.py"],
            "services/service_provider.py": ["services/service_provider.py", "di/service_provider.py"],
            "unit_of_work/unit_of_work.py": ["database/repositories/unit_of_work.py",
                                             "database/sqlalchemy/core/unit_of_work.py"]
        }

    def create_new_structure(self):
        """Create the new directory structure."""
        for main_dir, sub_dirs in self.new_structure.items():
            base_path = self.project_root / "database" / main_dir
            base_path.mkdir(parents=True, exist_ok=True)

            if isinstance(sub_dirs, dict):
                for sub_dir in sub_dirs:
                    (base_path / sub_dir).mkdir(exist_ok=True)

            self.changes.append(f"Created directory structure: {main_dir}")

    def move_files(self):
        """Move files to their new locations."""
        moves = {
            "database/repositories/interfaces/base_service.py":
                "database/services/interfaces/base_service.py",
            "database/repositories/interfaces/leather_inventory_service.py":
                "database/services/interfaces/leather_inventory_service.py",
            # Add all other file moves
        }

        for old_path, new_path in moves.items():
            old_full = self.project_root / old_path
            new_full = self.project_root / new_path

            if old_full.exists():
                new_full.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_full), str(new_full))
                self.changes.append(f"Moved: {old_path} -> {new_path}")

    def update_imports(self, file_path: Path):
        """Update import statements in a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Import path mappings
        import_updates = {
            "from database.repositories.interfaces.base_service":
                "from database.services.interfaces.base_service",
            "from database.repositories.unit_of_work":
                "from database.unit_of_work.unit_of_work",
            # Add all other import updates
        }

        updated_content = content
        for old_import, new_import in import_updates.items():
            updated_content = updated_content.replace(old_import, new_import)

        if updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            self.changes.append(f"Updated imports in: {file_path}")

    def consolidate_implementations(self):
        """Consolidate duplicate implementations."""
        for target, sources in self.consolidate_files.items():
            target_path = self.project_root / target
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Combine content from all source files
            combined_content = []
            for source in sources:
                source_path = self.project_root / source
                if source_path.exists():
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        combined_content.append(content)
                    source_path.unlink()
                    self.changes.append(f"Consolidated from: {source}")

            # Write combined content
            if combined_content:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(combined_content))
                self.changes.append(f"Created consolidated file: {target}")

    def create_log(self):
        """Create a detailed log of all changes."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = f"""# Project Reorganization Log
Timestamp: {timestamp}

## Changes Made:
{"".join(f"- {change}\n" for change in self.changes)}

## New Structure:
```
database/
├── services/
│   ├── interfaces/
│   └── implementations/
├── repositories/
│   ├── interfaces/
│   └── implementations/
└── unit_of_work/
```

## Consolidated Files:
{"".join(f"- {target}\n" for target in self.consolidate_files.keys())}

## Next Steps:
1. Review updated import paths in all files
2. Run tests to verify functionality
3. Update documentation with new structure
"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

    def run(self):
        """Execute the reorganization process."""
        print("Starting project reorganization...")

        self.create_new_structure()
        self.move_files()

        # Update imports in all Python files
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    self.update_imports(Path(root) / file)

        self.consolidate_implementations()
        self.create_log()

        print("Reorganization completed! Check reorganization_log.md for details.")


if __name__ == '__main__':
    reorganizer = ProjectReorganizer('path/to/store_management')
    reorganizer.run()