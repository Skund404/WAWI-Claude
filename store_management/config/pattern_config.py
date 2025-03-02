# config/pattern_config.py
"""
Configuration settings for pattern management in the leatherworking application.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PatternConfiguration:
    """
    Comprehensive configuration class for pattern-related settings.

    Manages waste factors, complexity calculations, caching, and performance parameters.
    """
    # Inventory-related configurations
    inventory_page_size: int = 50
    max_material_cache_size: int = 100

    # Pattern complexity calculation parameters
    waste_factor: float = 0.1
    complexity_threshold: float = 0.75

    # Performance and caching settings
    enable_material_caching: bool = True
    material_cache_expiry_minutes: int = 60

    # Additional configuration options
    default_skill_level: str = "Intermediate"

    # Flexible configuration for additional settings
    extra_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Post-initialization validation and setup.
        """
        # Validate waste factor
        if not 0 <= self.waste_factor <= 1:
            raise ValueError("Waste factor must be between 0 and 1")

        # Validate complexity threshold
        if not 0 <= self.complexity_threshold <= 1:
            raise ValueError("Complexity threshold must be between 0 and 1")

        # Ensure page size is positive
        if self.inventory_page_size <= 0:
            raise ValueError("Inventory page size must be a positive integer")

    def update_config(self, **kwargs):
        """
        Update configuration dynamically.

        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.extra_config[key] = value

    def get_config(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieve a configuration value.

        Args:
            key (str): Configuration key to retrieve
            default (Optional[Any]): Default value if key is not found

        Returns:
            Configuration value or default
        """
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra_config.get(key, default)


# Create a singleton instance of the configuration
PATTERN_CONFIG = PatternConfiguration()