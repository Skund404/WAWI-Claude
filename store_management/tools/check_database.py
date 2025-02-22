# Path: tools/check_database.py
"""
Script to check database contents and verify data is available.
"""
import sys
import os
import logging
import sqlite3
from pathlib import Path

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_checker")


def find_database_path():
    """
    Find the database file path by searching common locations.

    Returns:
        str: Path to the database file or None if not found
    """
    # Try to import the settings module properly
    try:
        from config.settings import get_database_path
        return get_database_path()
    except (ImportError, ModuleNotFoundError):
        logger.warning("Could not import config.settings module, searching for database file manually")

    # Common places to look for SQLite database files
    possible_paths = [
        os.path.join(project_root, "database.db"),
        os.path.join(project_root, "data", "database.db"),
        os.path.join(project_root, "store_management.db"),
        os.path.join(project_root, "data", "store_management.db"),
        os.path.join(project_root, "instance", "database.db"),
    ]

    # Search for config file that might contain database path
    config_file = os.path.join(project_root, "config", "config.py")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                # Look for database path in the content
                if "database_path" in content:
                    logger.info("Found config file with database path references")
        except Exception as e:
            logger.error(f"Error reading config file: {e}")

    # Check if any of the possible paths exist
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found database file at: {path}")
            return path

    # Search for SQLite files
    logger.info("Searching for SQLite database files in project")
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                path = os.path.join(root, file)
                logger.info(f"Found potential database file: {path}")
                return path

    logger.error("Could not find database file")
    return None


def check_database_file():
    """
    Check if the database file exists and has the expected tables.

    Returns:
        bool: True if the database file exists and has expected tables
    """
    db_path = find_database_path()

    if not db_path:
        logger.error("Database path could not be determined")
        return False

    logger.info(f"Database path: {db_path}")

    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False

    return True


def list_database_tables():
    """
    List all tables in the database.

    Returns:
        list: List of table names
    """
    db_path = find_database_path()

    if not db_path:
        logger.error("Cannot list tables: Database path not found")
        return []

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        table_names = [table[0] for table in tables]
        logger.info(f"Found {len(table_names)} tables: {', '.join(table_names)}")

        return table_names
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def check_table_contents(table_name):
    """
    Check the contents of a specific table.

    Args:
        table_name: Name of the table to check

    Returns:
        int: Number of rows in the table
    """
    db_path = find_database_path()

    if not db_path:
        logger.error(f"Cannot check table {table_name}: Database path not found")
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        logger.info(f"Table '{table_name}' has {count} rows")

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"Table '{table_name}' columns: {', '.join(column_names)}")

        # Get sample data if available
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            for i, row in enumerate(rows):
                logger.info(f"Sample row {i + 1}: {row}")

        return count
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {str(e)}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """
    Main function to run database checks.
    """
    logger.info("Starting database check")

    # Check database file
    if not check_database_file():
        logger.error("Database file check failed")
        return

    # List tables
    tables = list_database_tables()
    if not tables:
        logger.error("No tables found in database")
        return

    # Check each table
    for table in tables:
        if table != 'sqlite_sequence':  # Skip SQLite internal tables
            check_table_contents(table)

    logger.info("Database check completed")


if __name__ == "__main__":
    main()