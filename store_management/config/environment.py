from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class EnvironmentManager:
    """
    Manage application environment configuration.
    """
    _debug_mode = False
    _log_level = 'INFO'

    @classmethod
    def __new__(cls):
        """
        Prevent direct instantiation.

        Returns:
            EnvironmentManager: Class reference
        """
        raise TypeError(
            'EnvironmentManager is a static class and cannot be instantiated')

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.

        Args:
            key (str): Environment variable name
            default (Optional[str]): Default value if not found

        Returns:
            Optional[str]: Environment variable value
        """
        return os.environ.get(key, default)

    @classmethod
    def is_debug(cls) -> bool:
        """
        Check if application is in debug mode.

        Returns:
            bool: True if in debug mode, False otherwise
        """
        debug_env = os.environ.get('DEBUG', '').lower()
        return debug_env in ('1', 'true', 'yes') or cls._debug_mode

    @classmethod
    def get_log_level(cls) -> str:
        """
        Get the current logging level.

        Returns:
            str: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level_env = os.environ.get('LOG_LEVEL', '').upper()
        if log_level_env in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            return log_level_env
        if cls.is_debug():
            return 'DEBUG'
        return cls._log_level

    @classmethod
    def set_debug(cls, enable: bool = True):
        """
        Enable or disable debug mode.

        Args:
            enable (bool): Whether to enable debug mode
        """
        cls._debug_mode = enable
        cls._log_level = 'DEBUG' if enable else 'INFO'