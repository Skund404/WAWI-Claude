# Path: tools/check_database_data.py
"""
Script to check if there is data in the storage table.
"""
import os
import sys
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("database_checker")


def find_database_file():
    """Find the SQLite database file."""
    # List of possible locations
    possible_locations = [
        "store_management.db",
        "data/store_management.db",
        "database/store_management.db",
        "config/database/store_management.db"
    ]

    for location in possible_locations:
        if os.path.exists(location):
            return location

    # If not found in the predefined locations, search for it
    logger.info("Searching for database file...")
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                logger.info(f"Found database file: {path}")
                return path

    return None


def check_storage_table():
    """Check if the storage table exists and has data."""
    db_path = find_database_file()
    if not db_path:
        logger.error("Database file not found.")
        return False

    logger.info(f"Using database at: {db_path}")

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if storage table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='storage';
        """)
        if not cursor.fetchone():
            logger.error("Storage table doesn't exist in the database.")
            return False

        # Check if there's data in the storage table
        cursor.execute("SELECT COUNT(*) FROM storage;")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} records in the storage table.")

        if count > 0:
            # Show sample data
            cursor.execute("SELECT * FROM storage LIMIT 5;")
            rows = cursor.fetchall()

            # Get column names
            cursor.execute("PRAGMA table_info(storage);")
            columns = [info[1] for info in cursor.fetchall()]

            logger.info(f"Column names: {columns}")
            logger.info("Sample data:")
            for row in rows:
                logger.info(f"  {row}")

            return True
        else:
            logger.warning("Storage table exists but has no data.")
            return False

    except Exception as e:
        logger.error(f"Error checking storage table: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def add_sample_data():
    """Add sample data to the storage table if it's empty."""
    db_path = find_database_file()
    if not db_path:
        logger.error("Database file not found.")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if storage table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='storage';
        """)
        if not cursor.fetchone():
            logger.info("Creating storage table...")

            # Create the storage table
            cursor.execute("""
                CREATE TABLE storage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    capacity REAL NOT NULL,
                    current_occupancy REAL NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL
                );
            """)

        # Check if there's already data
        cursor.execute("SELECT COUNT(*) FROM storage;")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Adding sample data to storage table...")

            # Add sample data
            sample_data = [
                ("Main Warehouse", "Building A", 1000.0, 650.0, "Warehouse", "Main storage facility", "active"),
                ("Shelf A1", "Main Warehouse - Section A", 50.0, 30.0, "Shelf", "Small parts storage", "active"),
                ("Shelf B2", "Main Warehouse - Section B", 75.0, 45.0, "Shelf", "Medium parts storage", "active"),
                (
                "Cold Storage", "Building B", 500.0, 200.0, "Refrigerated", "Temperature controlled storage", "active"),
                ("Archive Room", "Building C", 300.0, 280.0, "Archive", "Document and sample storage", "active")
            ]

            cursor.executemany("""
                INSERT INTO storage (name, location, capacity, current_occupancy, type, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, sample_data)

            conn.commit()
            logger.info(f"Added {len(sample_data)} sample records to the storage table.")
            return True
        else:
            logger.info("Storage table already has data, skipping sample data insertion.")
            return True

    except Exception as e:
        logger.error(f"Error adding sample data: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """Main function."""
    logger.info("Checking database storage table...")

    if not check_storage_table():
        logger.warning("Storage table is missing or empty.")

        # Ask if user wants to add sample data
        response = input("Would you like to add sample data to the storage table? (y/n): ")
        if response.lower() == 'y':
            if add_sample_data():
                logger.info("Sample data added successfully.")
                check_storage_table()  # Show the data that was added
            else:
                logger.error("Failed to add sample data.")
    else:
        logger.info("Storage table exists and has data.")


if __name__ == "__main__":
    main()