# gui/utils/utils_service_provider_bridge.py
"""
Bridge module for resolving 'utils.service_provider' imports.
This module adds a custom import hook to redirect 'utils.service_provider' imports
to 'gui.utils.service_provider' to maintain backward compatibility.
"""

import sys
import logging
import importlib.abc
import importlib.machinery
from types import ModuleType

# Configure module-level logger
logger = logging.getLogger(__name__)
logger.info("Initializing utils service provider bridge")


class ServiceProviderImportFinder(importlib.abc.MetaPathFinder):
    """
    Custom import finder to redirect 'utils.service_provider' imports
    to 'gui.utils.service_provider'.
    """

    def find_spec(self, fullname, path, target=None):
        """
        Find the module spec for the requested import.

        Args:
            fullname: The full name of the module being imported
            path: The path to search for the module
            target: The target module

        Returns:
            The module spec if this finder can find it, otherwise None
        """
        # Check if we're looking for utils.service_provider
        if fullname == 'utils.service_provider':
            logger.debug(f"Redirecting import of {fullname} to gui.utils.service_provider")

            # Get the spec for gui.utils.service_provider
            try:
                spec = importlib.util.find_spec('gui.utils.service_provider')
                if spec:
                    logger.info("Successfully redirected import to gui.utils.service_provider")
                    return spec
                else:
                    logger.error("Failed to find gui.utils.service_provider module spec")
            except Exception as e:
                logger.error(f"Error finding module spec: {str(e)}")

        # Not a module we're looking for
        return None


def install_import_hook():
    """
    Install the custom import hook to handle 'utils.service_provider' imports.
    """
    logger.info("Installing service provider import hook")

    try:
        # Create the utils package if it doesn't exist
        if 'utils' not in sys.modules:
            logger.debug("Creating utils package module")
            utils_module = ModuleType('utils')
            utils_module.__path__ = []  # Empty path to indicate it's a namespace
            sys.modules['utils'] = utils_module

        # Register our custom finder
        sys.meta_path.insert(0, ServiceProviderImportFinder())
        logger.info("Import hook installed successfully")

        return True
    except Exception as e:
        logger.error(f"Failed to install import hook: {str(e)}")
        return False


# Install the import hook when this module is imported
success = install_import_hook()
if success:
    logger.info("Bridging for utils.service_provider is now active")
else:
    logger.error("Failed to set up bridging for utils.service_provider")