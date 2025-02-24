

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ApplicationConfig:
    pass
"""Centralized application configuration"""
_instance = None

def __new__(cls):
    pass
"""Singleton pattern to ensure only one configuration instance"""
if cls._instance is None:
    pass
cls._instance = super(ApplicationConfig, cls).__new__(cls)
cls._instance._initialized = False
return cls._instance

@inject(MaterialService)
def __init__(self):
    pass
if not self._initialized:
    pass
self._config = {}
self._config_path = None
self._load_config()
self._initialized = True

@inject(MaterialService)
def _load_config(self):
    pass
"""Load configuration from file and environment variables"""
self._config = {'app_name': 'Store Management', 'app_version':
'1.0.0', 'database': {'url': 'sqlite:///store_management.db',
'pool_size': 5, 'max_overflow': 10, 'timeout': 30}, 'gui': {
'window_size': (1024, 768), 'theme': 'default',
'default_padding': 5, 'minimum_column_width': 80}, 'logging': {
'level': 'INFO', 'file': 'store_management.log', 'max_size':
10485760, 'backup_count': 3}, 'paths': {'config_dir': self.
_get_config_dir(), 'database_file': 'store_management.db',
'backup_dir': 'backups', 'log_dir': 'logs'}}
config_path = self._get_config_path()
if config_path.exists():
    pass
try:
    pass
with open(config_path, 'r') as f:
    pass
file_config = json.load(f)
self._merge_config(file_config)
except Exception as e:
    pass
print(f'Error loading configuration file: {e}')
self._load_from_env()

@inject(MaterialService)
def _get_config_dir(self) -> Path:
"""Get the configuration directory"""
if os.name == 'nt':
    pass
app_data = os.environ.get('APPDATA', '')
return Path(app_data) / 'StoreManagement'
else:
home = os.path.expanduser('~')
return Path(home) / '.store_management'

@inject(MaterialService)
def _get_config_path(self) -> Path:
"""Get the path to the configuration file"""
config_dir = self._get_config_dir()
config_dir.mkdir(parents=True, exist_ok=True)
return config_dir / 'config.json'

@inject(MaterialService)
def _merge_config(self, config: Dict[str, Any]):
    pass
"""Recursively merge configuration dictionaries"""
for key, value in config.items():
    pass
if key in self._config and isinstance(self._config[key], dict
) and isinstance(value, dict):
self._merge_config(self._config[key], value)
else:
self._config[key] = value

@inject(MaterialService)
def _load_from_env(self):
    pass
"""Load configuration from environment variables"""
prefix = 'SM_'
for key, value in os.environ.items():
    pass
if key.startswith(prefix):
    pass
parts = key[len(prefix):].lower().split('_')
config = self._config
for part in parts[:-1]:
    pass
if part not in config:
    pass
config[part] = {}
config = config[part]
config[parts[-1]] = value

@inject(MaterialService)
def get(self, *keys, default=None) -> Any:
"""Get a configuration value by key path"""
config = self._config
try:
    pass
for key in keys:
    pass
config = config[key]
return config
except (KeyError, TypeError):
    pass
return default

@inject(MaterialService)
def set(self, value: Any, *keys) -> None:
"""Set a configuration value by key path"""
if not keys:
    pass
return
config = self._config
for key in keys[:-1]:
    pass
if key not in config:
    pass
config[key] = {}
config = config[key]
config[keys[-1]] = value

@inject(MaterialService)
def save(self) -> None:
"""Save configuration to file"""
config_path = self._get_config_path()
try:
    pass
with open(config_path, 'w') as f:
    pass
json.dump(self._config, f, indent=2)
except Exception as e:
    pass
print(f'Error saving configuration: {e}')
