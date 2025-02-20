# File: store_management/config/environment.py
import os
from pathlib import Path
from dotenv import load_dotenv


class EnvironmentManager:
    """
    Centralized environment configuration management
    """
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Determine project root
        self.project_root = Path(__file__).resolve().parents[2]

        # Potential .env file locations
        env_paths = [
            self.project_root / '.env',
            self.project_root / '.env.local',
        ]

        # Load first existing .env file
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break

    @staticmethod
    def get(key: str, default: str = None) -> str:
        """
        Retrieve environment variable with optional default
        """
        return os.getenv(key, default)

    @staticmethod
    def is_debug() -> bool:
        """
        Check if application is in debug mode
        """
        return EnvironmentManager.get('DEBUG', 'False').lower() == 'true'

    @staticmethod
    def get_log_level() -> str:
        """
        Get configured log level
        """
        return EnvironmentManager.get('LOG_LEVEL', 'INFO')


# Create a singleton instance
env = EnvironmentManager()