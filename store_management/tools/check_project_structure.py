from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Script to check the project structure and verify imports work properly.
"""
logging.basicConfig(
level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("project_checker")


def get_project_root():
    pass
"""
Get the project root directory.

Returns:
Path: Path to project root
"""
return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_directory_structure():
    pass
"""
Check the directory structure of the project.
"""
root = get_project_root()
logger.info(f"Project root: {root}")
important_dirs = ["config", "database", "gui", "services", "utils"]
for dir_name in important_dirs:
    pass
dir_path = root / dir_name
if dir_path.exists() and dir_path.is_dir():
    pass
files = list(dir_path.glob("*.py"))
logger.info(
f"Directory '{dir_name}' exists with {len(files)} Python files")
for file in files:
    pass
logger.info(f"  - {file.name}")
else:
logger.warning(
f"Directory '{dir_name}' not found or not a directory")


def check_module_imports():
    pass
"""
Check if important modules can be imported correctly.
"""
modules_to_check = [
"config",
"database",
"gui",
"services",
"utils",
"database.models",
"database.session",
"gui.main_window",
"services.implementations.storage_service",
]
for module_name in modules_to_check:
    pass
try:
    pass
module = importlib.import_module(module_name)
logger.info(f"Successfully imported module: {module_name}")
except ImportError as e:
    pass
logger.error(f"Failed to import module {module_name}: {e}")


def check_database_config():
    pass
"""
Try to find and read database configuration.
"""
root = get_project_root()
config_files = [
root / "config" / "settings.py",
root / "config" / "config.py",
root / "config.py",
root / "settings.py",
]
for config_file in config_files:
    pass
if config_file.exists():
    pass
logger.info(f"Found config file: {config_file}")
try:
    pass
with open(config_file, "r") as f:
    pass
content = f.read()
if any(
term in content for term in ["database", "db_path", "sqlite"]
):
logger.info(
f"Config file {config_file} contains database settings"
)
lines = content.split("\n")
db_lines = [
line
for line in lines
if any(
term in line.lower()
for term in ["database", "db_path", "sqlite"]
)
]
for line in db_lines:
    pass
logger.info(f"  DB CONFIG: {line.strip()}")
except Exception as e:
    pass
logger.error(f"Error reading config file {config_file}: {e}")


def main():
    pass
"""
Run all project structure checks.
"""
logger.info("Starting project structure check")
project_root = str(get_project_root())
sys.path.insert(0, project_root)
check_directory_structure()
check_database_config()
check_module_imports()
logger.info("Project structure check completed")


if __name__ == "__main__":
    pass
main()
