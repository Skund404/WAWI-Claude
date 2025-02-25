# utils/config_tracker.py
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

"""
Configuration Tracking and Logging Utility for Store Management System.

Provides comprehensive logging and tracking of configuration changes,
with support for environment-specific configurations.
"""


class ConfigurationTracker:
    """
    Centralized configuration tracking and logging system.

    Manages configuration changes, provides audit trails,
    and supports environment-specific configurations.
    """

    def __init__(self, base_config_dir: Optional[str] = None, log_dir: Optional[str] = None):
        """
        Initialize Configuration Tracker.

        Args:
            base_config_dir: Base directory for configuration files
            log_dir: Directory for storing configuration logs
        """
        self.base_config_dir = base_config_dir or os.path.join(os.path.dirname(__file__), '..', 'config')
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', 'logs', 'config')

        # Create directories if they don't exist
        os.makedirs(self.base_config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Set up logger
        self.logger = logging.getLogger('config_tracker')
        self.logger.setLevel(logging.INFO)

        # Add file handler
        log_file = os.path.join(self.log_dir, f"config_changes_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

    def load_environment_config(self, environment: str = 'development',
                                default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration for a specific environment.

        Args:
            environment: Target environment (development, production, testing)
            default_config: Fallback configuration

        Returns:
            Dict[str, Any]: Loaded configuration
        """
        config_filename = f'config.{environment}.json'
        config_path = os.path.join(self.base_config_dir, config_filename)

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as config_file:
                    config = json.load(config_file)
                self.logger.info(f'Loaded {environment} configuration from {config_filename}')
                return config

            if default_config:
                self.logger.warning(
                    f'No configuration found for {environment}. Using provided default configuration.'
                )
                return default_config

            self.logger.error(
                f'No configuration found for {environment} and no default provided.'
            )
            return {}

        except json.JSONDecodeError:
            self.logger.error(f'Invalid JSON in {config_filename}')
            return default_config or {}

        except Exception as e:
            self.logger.error(f'Error loading configuration: {e}')
            return default_config or {}

    def track_config_change(self, config_name: str, old_value: Any,
                            new_value: Any, context: Optional[Dict[str, Any]] = None):
        """
        Log configuration changes with detailed context.

        Args:
            config_name: Name of the changed configuration parameter
            old_value: Previous configuration value
            new_value: New configuration value
            context: Additional context information
        """
        change_log = {
            'config_name': config_name,
            'old_value': str(old_value),
            'new_value': str(new_value),
            'timestamp': datetime.now().isoformat()
        }

        if context:
            change_log['context'] = context

        self.logger.info(f'Configuration Change: {json.dumps(change_log)}')

    def save_config_snapshot(self, config: Dict[str, Any], environment: str = 'development'):
        """
        Save a snapshot of the current configuration.

        Args:
            config: Configuration to save
            environment: Environment identifier
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'config_snapshot_{environment}_{timestamp}.json'
        snapshot_path = os.path.join(self.log_dir, 'snapshots', filename)

        # Create snapshots directory if it doesn't exist
        os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)

        try:
            with open(snapshot_path, 'w') as snapshot_file:
                json.dump(config, snapshot_file, indent=4)
            self.logger.info(f'Configuration snapshot saved: {filename}')

        except Exception as e:
            self.logger.error(f'Failed to save configuration snapshot: {e}')


# Global instance for easy access
CONFIG_TRACKER = ConfigurationTracker()