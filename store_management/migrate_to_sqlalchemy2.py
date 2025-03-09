#!/usr/bin/env python
"""
Migration helper script for transitioning to SQLAlchemy 2.0.

This script:
1. Scans your model files for SQLAlchemy 1.x patterns
2. Suggests changes to update to SQLAlchemy 2.0
3. Can optionally apply basic automatic conversions

Usage:
    python migrate_to_sqlalchemy2.py [--path=/path/to/models] [--apply]

Arguments:
    --path: Path to your model files (default: ./database/models)
    --apply: Apply automatic changes (default: False, just report)
"""

import os
import re
import argparse
import shutil
from pathlib import Path


class SQLAlchemyMigrator:
    def __init__(self, path, apply_changes=False):
        self.path = Path(path)
        self.apply_changes = apply_changes
        self.files_checked = 0
        self.files_needing_changes = 0
        self.backup_dir = self.path / "pre_migration_backup"

    def run(self):
        """Run the migration analysis"""
        print(f"SQLAlchemy 2.0 Migration Helper")
        print(f"==============================")
        print(f"Scanning directory: {self.path}")
        print(f"Apply changes: {self.apply_changes}")
        print()

        if self.apply_changes:
            # Create backup directory
            os.makedirs(self.backup_dir, exist_ok=True)
            print(f"Created backup directory: {self.backup_dir}")

        # Scan python files
        self._scan_directory(self.path)

        print(f"\nSummary:")
        print(f"- Files checked: {self.files_checked}")
        print(f"- Files needing changes: {self.files_needing_changes}")

        if self.apply_changes:
            print(f"- Changes applied: Yes (backups in {self.backup_dir})")
        else:
            print(f"- Changes applied: No (dry-run)")
            print("\nTo apply changes, run with --apply")

    def _scan_directory(self, directory):
        """Recursively scan directory for Python files"""
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith(".") and item.name != "pre_migration_backup":
                self._scan_directory(item)
            elif item.is_file() and item.suffix == ".py":
                self._analyze_file(item)

    def _analyze_file(self, file_path):
        """Analyze a single Python file for SQLAlchemy 1.x patterns"""
        self.files_checked += 1

        with open(file_path, "r") as f:
            content = f.read()

        changes_needed = False
        new_content = content

        # Check for Column usage in class definitions
        if re.search(r"class\s+\w+\([^)]*\):\s*[\r\n]+\s*.*=\s*Column\(", content, re.MULTILINE):
            changes_needed = True
            print(f"\n{file_path}:")
            print("  - Found Column() usage in class definition, should use mapped_column()")

            if self.apply_changes:
                new_content = re.sub(
                    r"(\s*)(\w+)\s*=\s*Column\(([^)]*)\)",
                    r"\1\2: Mapped[Any] = mapped_column(\3)",
                    new_content
                )

        # Check for query.all() pattern
        if "query." in content:
            changes_needed = True
            print(f"  - Found query.* usage, should use select() and session.execute()")

        # Check for import patterns
        if "from sqlalchemy import Column" in content:
            changes_needed = True
            print(f"  - Found 'from sqlalchemy import Column', should import mapped_column")

            if self.apply_changes:
                new_content = new_content.replace(
                    "from sqlalchemy import Column",
                    "from sqlalchemy import Column  # TODO: Replace with mapped_column"
                )

                # Add import if not already present
                if "from sqlalchemy.orm import Mapped, mapped_column" not in new_content:
                    new_content = "from sqlalchemy.orm import Mapped, mapped_column\nfrom typing import Any, Optional, List\n" + new_content

        # Check for relationship usage without Mapped annotation
        if "relationship(" in content and "Mapped[" not in content:
            changes_needed = True
            print(f"  - Found relationship() without Mapped[] type annotations")

        # Check for Base class
        if "Base = declarative_base()" in content:
            changes_needed = True
            print(f"  - Found old-style declarative_base(), should use DeclarativeBase class")

            if self.apply_changes:
                new_content = new_content.replace(
                    "Base = declarative_base()",
                    "# TODO: Replace with modern Base class\n# class Base(DeclarativeBase):\n#     pass"
                )

        if changes_needed:
            self.files_needing_changes += 1

            if self.apply_changes:
                # Backup original file
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)

                # Write updated content
                with open(file_path, "w") as f:
                    f.write(new_content)

                print(f"  ✓ Applied changes (backup at {backup_path})")


def main():
    parser = argparse.ArgumentParser(description="SQLAlchemy 2.0 Migration Helper")
    parser.add_argument("--path", default="./database/models", help="Path to model files")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    args = parser.parse_args()

    migrator = SQLAlchemyMigrator(args.path, args.apply)
    migrator.run()


if __name__ == "__main__":
    main()