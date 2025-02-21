# store_management/config/application_config.py
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class ApplicationConfig:
    """Centralized application configuration"""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one configuration instance"""
        if cls._instance is None:
            cls._instance = super(ApplicationConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._config = {}
            self._config_path = None
            self._load_config()
            self._initialized = True

    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Default configuration
        self._config = {
            'app_name': 'Store Management',
            'app_version': '1.0.0',
            'database': {
                'url': 'sqlite:///store_management.db',
                'pool_size': 5,
                'max_overflow': 10,
                'timeout': 30
            },
            'gui': {
                'window_size': (1024, 768),
                'theme': 'default',
                'default_padding': 5,
                'minimum_column_width': 80
            },
            'logging': {
                'level': 'INFO',
                'file': 'store_management.log',
                'max_size': 10485760,
                'backup_count': 3
            },
            'paths': {
                'config_dir': self._get_config_dir(),
                'database_file': 'store_management.db',
                'backup_dir': 'backups',
                'log_dir': 'logs'
            }
        }

        # Load from configuration file if exists
        config_path = self._get_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
            except Exception as e:
                print(f"Error loading configuration file: {e}")

        # Override with environment variables
        self._load_from_env()

    def _get_config_dir(self) -> Path:
        """Get the configuration directory"""
        # Use platform-specific configuration directory
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', '')
            return Path(app_data) / 'StoreManagement'
        else:  # Linux/Mac
            home = os.path.expanduser('~')
            return Path(home) / '.store_management'

    def _get_config_path(self) -> Path:
        """Get the path to the configuration file"""
        config_dir = self._get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'

    def _merge_config(self, config: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in config.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._merge_config(self._config[key], value)
            else:
                self._config[key] = value

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Example: SM_DATABASE_URL overrides self._config['database']['url']
        prefix = 'SM_'
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split('_')
                config = self._config
                for part in parts[:-1]:
                    if part not in config:
                        config[part] = {}
                    config = config[part]
                config[parts[-1]] = value

    def get(self, *keys, default=None) -> Any:
        """Get a configuration value by key path"""
        config = self._config
        try:
            for key in keys:
                config = config[key]
            return config
        except (KeyError, TypeError):
            return default

    def set(self, value: Any, *keys) -> None:
        """Set a configuration value by key path"""
        if not keys:
            return

        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to file"""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")