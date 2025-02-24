

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ConfigManager:
    """
    Centralized configuration management with environment support.
    """
    _config: Dict[str, Any] = {}
    _env: str = 'development'

    @classmethod
    def load_config(cls, config_path: Optional[str] = None):
        """
        Load configuration from file or environment.

        Args:
            config_path (Optional[str]): Path to config file
        """
        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__),
                                       f'{cls._env}_config.json')
        try:
            with open(config_path, 'r') as f:
                cls._config = json.load(f)
            logging.info(f'Loaded configuration from {config_path}')
        except FileNotFoundError:
            logging.warning(f'Config file not found: {config_path}')
            cls._config = {}
        except json.JSONDecodeError:
            logging.error(f'Invalid JSON in config file: {config_path}')
            cls._config = {}

        @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key (str): Configuration key
            default (Any, optional): Default value if key not found

        Returns:
            Configuration value
        """
        if not cls._config:
            cls.load_config()
        keys = key.split('.')
        value = cls._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default

        @classmethod
    def set_environment(cls, env: str):
        """
        Set the current environment.

        Args:
            env (str): Environment name (e.g., 'development', 'production')
        """
        cls._env = env
        cls.load_config()

        @classmethod
    def get_database_path(cls) -> str:
        """
        Get the database path from configuration.

        Returns:
            str: Path to the database
        """
        db_path = cls.get('database.path')
        if not db_path:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                   'store.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return db_path


ConfigManager.load_config()
