# Relative path: store_management/utils/circular_import_resolver.py

"""
Circular Import Resolver Utility

This module provides a utility to help manage and resolve circular import dependencies
in a modular and extensible manner.
"""

import importlib
import logging
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


class CircularImportResolver:
    pass
"""
A utility class to manage and resolve circular import dependencies.

This class provides methods to dynamically import modules and resolve
potential circular import issues by lazy loading and caching imported modules.
"""

_module_cache: Dict[str, Any] = {}
_import_lock: Dict[str, bool] = {}

@classmethod
def import_module(cls, module_path: str) -> Any:
"""
Dynamically import a module with circular import protection.

Args:
module_path (str): Fully qualified module path to import.

Returns:
Any: The imported module.

Raises:
ImportError: If the module cannot be imported after multiple attempts.
"""
if module_path in cls._module_cache:
    pass
return cls._module_cache[module_path]

# Prevent recursive import attempts
if cls._import_lock.get(module_path, False):
    pass
logger.warning(
f"Potential circular import detected for {module_path}")
return None

try:
    pass
# Lock the import to prevent recursive calls
cls._import_lock[module_path] = True

# Dynamically import the module
module = importlib.import_module(module_path)

# Cache the imported module
cls._module_cache[module_path] = module

return module

except ImportError as e:
    pass
logger.error(f"Failed to import module {module_path}: {e}")
raise

finally:
# Remove the import lock
cls._import_lock.pop(module_path, None)

@classmethod
def get_class(cls, module_path: str, class_name: str) -> Optional[Type[Any]]:
"""
Dynamically retrieve a class from a module.

Args:
module_path (str): Fully qualified module path.
class_name (str): Name of the class to retrieve.

Returns:
Optional[Type[Any]]: The requested class, or None if not found.
"""
try:
    pass
module = cls.import_module(module_path)

if module is None:
    pass
logger.warning(f"Module {module_path} could not be imported")
return None

# Retrieve the class from the module
requested_class = getattr(module, class_name, None)

if requested_class is None:
    pass
logger.error(
f"Class {class_name} not found in module {module_path}")

return requested_class

except (ImportError, AttributeError) as e:
    pass
logger.error(
f"Error retrieving class {class_name} from {module_path}: {e}")
return None

@classmethod
def clear_cache(cls):
    pass
"""
Clear the module and import caches.

Useful for testing or resetting the import state.
"""
cls._module_cache.clear()
cls._import_lock.clear()
