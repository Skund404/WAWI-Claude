from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

# F:\WAWI Homebrew\WAWI Claude\store_management\tools\dependency_rollback.py

import os
import sys
import re
import shutil
import logging
from typing import List, Optional


class DependencyRollbackTool:
    pass
"""
Comprehensive tool to rollback dependency migration changes.
"""

@inject(MaterialService)
def __init__(self, project_root: str):
    pass
"""
Initialize rollback tool.

Args:
project_root (str): Root directory of the project
"""
self.project_root = os.path.abspath(project_root)
self.venv_path = self._find_virtual_env()

logging.basicConfig(
level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)
self.logger = logging.getLogger(__name__)

@inject(MaterialService)
def _find_virtual_env(self) -> Optional[str]:
"""
Find the virtual environment directory.

Returns:
Optional path to virtual environment
"""
# Common virtual environment directory names
venv_names = [".venv", "venv", "env"]

# Check project root and parent directories
current = self.project_root
while current != os.path.dirname(current):
    pass
for venv_name in venv_names:
    pass
potential_venv = os.path.join(current, venv_name)
if os.path.isdir(potential_venv):
    pass
return potential_venv
current = os.path.dirname(current)

# Fallback to sys.prefix (current Python environment)
return os.path.join(sys.prefix, "Lib", "site-packages")

@inject(MaterialService)
def _find_modified_python_files(self) -> List[str]:
"""
Find Python files modified by the migration script.

Returns:
List of modified file paths
"""
modified_files = []

# Directories to search
search_dirs = [self.project_root,
self.venv_path if self.venv_path else ""]

# Ignore directories
ignore_dirs = {"__pycache__", ".git", "build", "dist"}

for base_dir in search_dirs:
    pass
if not base_dir or not os.path.isdir(base_dir):
    pass
continue

for root, dirs, files in os.walk(base_dir):
    pass
# Remove ignored directories
dirs[:] = [d for d in dirs if d not in ignore_dirs]

for file in files:
    pass
if file.endswith(".py"):
    pass
full_path = os.path.join(root, file)

# Check for added imports or inject decorators
try:
    pass
with open(full_path, "r", encoding="utf-8") as f:
    pass
content = f.read()
if (
"@inject(" in content
or "" in content
or "from services.interfaces import" in content
):
modified_files.append(full_path)
except Exception as e:
    pass
self.logger.warning(
f"Could not read {full_path}: {e}")

return modified_files

@inject(MaterialService)
def rollback_file(self, file_path: str):
    pass
"""
Rollback changes in a single file.

Args:
file_path (str): Path to the Python file
"""
try:
    pass
with open(file_path, "r", encoding="utf-8") as f:
    pass
content = f.read()

# Remove specific imports
imports_to_remove = [
r"from\s+di\.core\s+import\s+inject\n?",
r"from\s+services\.interfaces\s+import\s+.*\n?",
]

for import_pattern in imports_to_remove:
    pass
content = re.sub(import_pattern, "", content)

# Remove @inject decorators (complex regex to handle different scenarios)
content = re.sub(r"@inject\(.*?\)\n", "", content)

# Write back to file
with open(file_path, "w", encoding="utf-8") as f:
    pass
f.write(content)

self.logger.info(f"Rolled back: {file_path}")

except Exception as e:
    pass
self.logger.error(f"Error rolling back {file_path}: {e}")

@inject(MaterialService)
def remove_registration_scripts(self):
    pass
"""
Remove service registration scripts.
"""
registration_paths = [
# Project service registration
os.path.join(
self.project_root,
"store_management",
"services",
"service_registration.py",
),
# Virtual env potential registration
os.path.join(self.venv_path, "services",
"service_registration.py"),
]

for path in registration_paths:
    pass
if os.path.exists(path):
    pass
try:
    pass
os.remove(path)
self.logger.info(f"Removed registration script: {path}")
except Exception as e:
    pass
self.logger.warning(f"Could not remove {path}: {e}")

@inject(MaterialService)
def rollback(self):
    pass
"""
Comprehensive rollback of dependency migration.
"""
self.logger.info("Starting dependency migration rollback...")

# Log environment details
self.logger.info(f"Project Root: {self.project_root}")
self.logger.info(f"Virtual Environment: {self.venv_path}")

# Find modified files
modified_files = self._find_modified_python_files()

# Rollback each file
for file_path in modified_files:
    pass
self.rollback_file(file_path)

# Remove registration scripts
self.remove_registration_scripts()

self.logger.info("Dependency migration rollback completed")


def main():
    pass
"""
Main entry point for dependency rollback.
"""
# Determine project root
project_root = os.path.abspath(os.path.join(
os.path.dirname(__file__), "..", ".."))

# Validate project root
if not os.path.exists(os.path.join(project_root, "store_management")):
    pass
print(f"Invalid project root: {project_root}")
print("Please ensure the script is run from the correct location.")
return

# Create rollback tool
rollback_tool = DependencyRollbackTool(project_root)

# Run rollback
rollback_tool.rollback()


if __name__ == "__main__":
    pass
main()
