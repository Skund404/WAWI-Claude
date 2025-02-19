# store_management/database/make_color_optional.py

import sqlite3
import logging
from pathlib import Path
import shutil
from datetime import datetime

from store_management.config import get_database_path
from store_management.utils.logger import logger


def backup_database(db_path):
    """Create a backup of the database before making changes"""
    backup_dir = Path(db_path).parent / 'backups'
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'pre_color_update_{timestamp}.db'

    shutil.copy2(db_path, backup_path)
    logger.info(f"Created database backup at {backup_path}")
    return backup_path


def update_sorting_system_table():
    """Update the sorting_system table to make color field optional"""
    db_path = get_database_path()

    # Create backup first
    backup_path = backup_database(db_path)

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Create temporary table with desired schema
        cursor.execute("""
            CREATE TABLE sorting_system_temp (
                unique_id_parts TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT,  -- Made optional by removing NOT NULL
                in_storage INTEGER NOT NULL,
                warning_threshold INTEGER NOT NULL,
                bin TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Copy data from original table to temporary table
        cursor.execute("""
            INSERT INTO sorting_system_temp
            SELECT * FROM sorting_system
        """)

        # Drop original table
        cursor.execute("DROP TABLE sorting_system")

        # Rename temporary table to original name
        cursor.execute("ALTER TABLE sorting_system_temp RENAME TO sorting_system")

        # Commit changes
        conn.commit()
        logger.info("Successfully updated sorting_system table - color field is now optional")

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f"Failed to update database: {str(e)}")
        logger.info(f"Restoring from backup: {backup_path}")

        # Restore from backup
        conn.close()
        shutil.copy2(backup_path, db_path)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    try:
        update_sorting_system_table()
        print("Successfully updated sorting_system table - color field is now optional")
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        raise