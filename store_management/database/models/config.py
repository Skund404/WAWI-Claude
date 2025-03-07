# database/models/config.py
"""
Comprehensive Configuration Models for Leatherworking Management System

This module defines configuration classes for database-related settings
with proper typing and structure.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Setup logger
logger = logging.getLogger(__name__)


class MaterialConfig:
    """
    Configuration settings for material-related parameters.

    Manages configuration for material processing, validation thresholds,
    and default values.
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize material configuration.

        Args:
            config_data: Configuration dictionary
        """
        self._config = config_data or {}
        self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default configuration values if not provided."""
        defaults = {
            'min_thickness_mm': 0.1,
            'max_thickness_mm': 15.0,
            'default_unit': 'square_foot',
            'min_stock_threshold': 5.0,
            'auto_reorder_enabled': False,
            'quality_check_required': True
        }

        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

    def get_material_setting(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific material configuration setting.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update material configuration settings.

        Args:
            updates: Dictionary of configuration updates
        """
        self._config.update(updates)
        logger.debug(f"Updated material configuration with {len(updates)} settings")

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all material configuration settings.

        Returns:
            Dict containing all configuration settings
        """
        return self._config.copy()


class ModelConfiguration:
    """
    Comprehensive model configuration management for leatherworking system.

    Centralizes all configuration settings and provides facilities for
    loading, saving, and managing configurations.
    """

    def __init__(self):
        """
        Initialize model configuration with default settings.
        """
        self.material_config = MaterialConfig()
        self.component_config = ComponentConfig()
        self.last_updated = datetime.utcnow()

    def load_configuration(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from a specified path.

        Args:
            config_path: Path to configuration file
        """
        try:
            if not config_path:
                config_path = os.environ.get('LEATHERWORK_CONFIG', 'config/default_config.json')

            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)

                if 'material' in config_data:
                    self.material_config = MaterialConfig(config_data['material'])

                if 'component' in config_data:
                    self.component_config = ComponentConfig(config_data['component'])

                self.last_updated = datetime.utcnow()
                logger.info(f"Configuration loaded from {config_path}")
            else:
                logger.warning(f"Configuration file {config_path} not found, using defaults")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Continue with defaults

    def save_configuration(self, config_path: Optional[str] = None) -> None:
        """
        Save current configuration to a specified path.

        Args:
            config_path: Path to save configuration file
        """
        try:
            if not config_path:
                config_path = os.environ.get('LEATHERWORK_CONFIG', 'config/default_config.json')

            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # Prepare configuration data
            config_data = {
                'material': self.material_config.get_all_settings(),
                'component': self.component_config.get_all_settings(),
                'last_updated': datetime.utcnow().isoformat()
            }

            # Save to file
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def update_material_settings(self, updates: Dict[str, Any]) -> None:
        """
        Update material configuration settings.

        Args:
            updates: Dictionary of material configuration updates
        """
        self.material_config.update_config(updates)
        self.last_updated = datetime.utcnow()

    def update_component_settings(self, updates: Dict[str, Any]) -> None:
        """
        Update component configuration settings.

        Args:
            updates: Dictionary of component configuration updates
        """
        self.component_config.update_config(updates)
        self.last_updated = datetime.utcnow()

    def get_last_updated(self) -> str:
        """
        Get the timestamp of the last configuration update.

        Returns:
            ISO formatted timestamp
        """
        return self.last_updated.isoformat()


def create_default_configuration() -> ModelConfiguration:
    """
    Create a default model configuration with standard settings.

    Returns:
        Default configuration instance
    """
    config = ModelConfiguration()
    # Add any specialized default configuration settings here
    return config


class ComponentConfig:
    """
    Configuration settings for component-related parameters.

    Manages configuration for component processing, validation thresholds,
    and default values for leatherworking components.
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize component configuration.

        Args:
            config_data: Configuration dictionary
        """
        self._config = config_data or {}
        self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default configuration values if not provided."""
        defaults = {
            'validate_material_requirements': True,
            'default_wastage_percentage': 5.0,
            'allow_material_substitution': False,
            'component_naming_pattern': '{project}_{type}_{index}',
            'auto_update_costs': True,
            'require_dimensions': True
        }

        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value

    def get_component_setting(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific component configuration setting.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update component configuration settings.

        Args:
            updates: Dictionary of configuration updates
        """
        self._config.update(updates)
        logger.debug(f"Updated component configuration with {len(updates)} settings")

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all component configuration settings.

        Returns:
            Dict containing all configuration settings
        """
        return self._config.copy()