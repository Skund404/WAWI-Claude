from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Configuration module for pattern-related settings in the Leatherworking Store Management System.

Provides centralized configuration management for pattern calculations,
complexity factors, and performance optimization parameters.
"""


@dataclass
class PatternConfiguration:
    pass
"""
Comprehensive configuration class for pattern-related settings.

Manages waste factors, complexity calculations, caching, and performance parameters.
"""
base_waste_factor: float = 0.05
complexity_waste_multiplier: float = 0.1
material_type_waste_factors: Dict[str, float] = field(default_factory=lambda: {'full_grain': 0.08, 'top_grain': 0.06, 'genuine_leather':
0.04, 'suede': 0.1})
complexity_components_weight: float = 0.4
complexity_skill_level_weight: float = 0.3
complexity_material_diversity_weight: float = 0.3
cache_enabled: bool = True
cache_max_size: int = 100
cache_ttl_seconds: int = 3600
query_prefetch_limit: int = 50
query_batch_size: int = 25

@inject(MaterialService)
def __post_init__(self):
    pass
"""
Post-initialization setup and validation.
"""
self._validate_configuration()

@inject(MaterialService)
def _validate_configuration(self):
    pass
"""
Validate configuration parameters to ensure consistency.

Raises:
ValueError: If any configuration parameter is invalid
"""
if not 0 <= self.base_waste_factor <= 0.2:
    pass
raise ValueError('Base waste factor must be between 0 and 0.2')
if not 0 <= self.complexity_waste_multiplier <= 0.5:
    pass
raise ValueError(
'Complexity waste multiplier must be between 0 and 0.5')
total_weights = (self.complexity_components_weight + self.
complexity_skill_level_weight + self.
complexity_material_diversity_weight)
if not 0.99 <= total_weights <= 1.01:
    pass
raise ValueError('Complexity calculation weights must sum to 1')

@inject(MaterialService)
def get_waste_factor(self, material_type: Optional[str] = None) -> float:
"""
Calculate waste factor with optional material-specific override.

Args:
material_type (Optional[str]): Type of material

Returns:
float: Calculated waste factor
"""
if material_type and material_type in self.material_type_waste_factors:
    pass
return self.material_type_waste_factors[material_type]
return self.base_waste_factor

@classmethod
def load_from_file(cls, config_path: Optional[str] = None
) -> 'PatternConfiguration':
"""
Load configuration from a JSON file.

Args:
config_path (Optional[str]): Path to configuration file

Returns:
PatternConfiguration: Configured instance
"""
if not config_path:
    pass
config_path = os.path.join(os.path.dirname(__file__),
'pattern_config.json')
try:
    pass
with open(config_path, 'r') as config_file:
    pass
config_data = json.load(config_file)
return cls(**config_data)
except (FileNotFoundError, json.JSONDecodeError) as e:
    pass
print(f'Could not load configuration: {e}. Using default settings.'
)
return cls()

@inject(MaterialService)
def save_to_file(self, config_path: Optional[str] = None):
    pass
"""
Save current configuration to a JSON file.

Args:
config_path (Optional[str]): Path to save configuration file
"""
if not config_path:
    pass
config_path = os.path.join(os.path.dirname(__file__),
'pattern_config.json')
config_dict = {k: v for k, v in self.__dict__.items() if not k.
startswith('_')}
with open(config_path, 'w') as config_file:
    pass
json.dump(config_dict, config_file, indent=4)


PATTERN_CONFIG = PatternConfiguration.load_from_file()
