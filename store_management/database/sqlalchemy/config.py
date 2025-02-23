# database/sqlalchemy/config.py

"""
Database configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL from configuration.

    Returns:
        Database URL string
    """
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_PATH')

    if not db_path:
        # Use default path in project directory
        project_root = _find_project_root()
        db_path = str(project_root / 'data' / 'store.db')

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    logger.debug(f"Using database path: {db_path}")
    return f'sqlite:///{db_path}'


def _find_project_root() -> Path:
    """
    Find the project root directory.

    Returns:
        Path to project root
    """
    current_dir = Path(__file__).resolve().parent

    # Search up the directory tree for setup.py or .git
    while current_dir.parent != current_dir:
        if (current_dir / 'setup.py').exists() or (current_dir / '.git').exists():
            return current_dir
        current_dir = current_dir.parent

    # If not found, use the current directory
    return Path.cwd()