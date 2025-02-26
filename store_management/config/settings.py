# config/settings.py
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Union

APP_NAME = "Leatherworking Store Management"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Application for managing a leatherworking store"

DEVELOPMENT = 'development'
PRODUCTION = 'production'
TESTING = 'testing'


class Environment:
    """Manage application environment configurations."""

    def __init__(self, env: Optional[str] = None):
        self.env = env or os.environ.get('APP_ENV', DEVELOPMENT)

    def is_development(self) -> bool:
        return self.env == DEVELOPMENT

    def is_production(self) -> bool:
        return self.env == PRODUCTION

    def is_testing(self) -> bool:
        return self.env == TESTING


class ConfigurationManager:
    """Manages application configuration settings."""

    def __new__(cls):
        """Singleton pattern implementation.

        Returns:
            ConfigurationManager: Singleton instance
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(ConfigurationManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._environment = Environment()
        self._initialize()

    def _initialize(self):
        """Initialize configuration with default and environment-specific settings."""
        # Set default configuration
        self._config = {
            'debug': self._environment.is_development(),
            'testing': self._environment.is_testing(),
            'database': {
                'uri': 'sqlite:///leatherworks.db',
            },
            'logging': {
                'level': 'DEBUG' if self._environment.is_development() else 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        }

        project_root = Path(__file__).resolve().parent.parent
        self._setup_directories(project_root)

        self._load_environment_config()

    def _setup_directories(self, project_root: Path):
        """Set up and create necessary application directories.

        Args:
            project_root (Path): Root directory of the project
        """
        self._config['project_root'] = str(project_root)
        self._config['logs_dir'] = str(project_root / 'logs')
        self._config['data_dir'] = str(project_root / 'data')
        self._config['backups_dir'] = str(project_root / 'backups')

        os.makedirs(self._config['logs_dir'], exist_ok=True)
        os.makedirs(self._config['data_dir'], exist_ok=True)
        os.makedirs(self._config['backups_dir'], exist_ok=True)

    def _load_environment_config(self):
        """Load environment-specific configuration from environment variables or config file."""
        env_config: Dict[str, Any] = {}

        # Load from environment variables
        env_config_json = os.environ.get('APP_CONFIG')
        if env_config_json:
            try:
                env_config = json.loads(env_config_json)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON in APP_CONFIG environment variable: {env_config_json}")

        # Load from file
        env = self._environment.env
        env_config_path = Path(self._config['project_root']) / 'config' / f'{env}.json'
        if env_config_path.exists():
            try:
                with open(env_config_path, 'r') as f:
                    file_config = json.load(f)
                    env_config = self._deep_update(env_config, file_config)
            except (IOError, OSError, json.JSONDecodeError) as e:
                logging.warning(f"Failed to load configuration file for {env} environment: {e}")

        self._deep_update(self._config, env_config)

    def _deep_update(self, original: Dict[str, Any], update: Dict[str, Any]):
        """Recursively update a nested dictionary.

        Args:
            original (Dict[str, Any]): Original configuration dictionary
            update (Dict[str, Any]): Dictionary with updates

        Returns:
            Dict[str, Any]: Updated configuration dictionary
        """
        for key, value in update.items():
            if isinstance(value, dict):
                original[key] = self._deep_update(original.get(key, {}), value)
            else:
                original[key] = value
        return original

    def set(self, key: str, value: Any):
        """Set a configuration value.

        Args:
            key (str): Dot-separated configuration key
            value (Any): Value to set
        """
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key (str): Dot-separated configuration key
            default (Any): Default value if key is not found

        Returns:
            Any: Configuration value or default if not found
        """
        keys = key.split('.')
        config = self._config
        for k in keys:
            if k in config:
                config = config[k]
            else:
                return default
        return config

    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary-style access.

        Args:
            key (str): Dot-separated configuration key

        Returns:
            Any: Configuration value

        Raises:
            KeyError: If the specified key is not found
        """
        value = self.get(key)
        if value is None:
            raise KeyError(f"Configuration key not found: {key}")
        return value


def get_database_path() -> Path:
    """Returns the absolute path to the database file.

    Returns:
        Path: The absolute path to the database file.
    """
    config = ConfigurationManager()
    project_root = Path(config['project_root'])
    return project_root / 'data' / 'database.db'