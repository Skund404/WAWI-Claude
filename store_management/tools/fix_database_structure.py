# Path: tools/fix_database_structure.py
"""
Script to fix database structure issues.
"""
import os
import sys
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_fixer")


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
    for root, _, files in os.walk(""):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                logger.info(f"Found database file: {path}")
                return path

    return None


def check_storage_table_structure():
    """Check the actual structure of the storage table."""
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

        # Get the current table structure
        cursor.execute("PRAGMA table_info(storage);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        logger.info(f"Current storage table columns: {column_names}")

        # Check if current_occupancy column exists
        if 'current_occupancy' not in column_names:
            logger.warning("The 'current_occupancy' column is missing from the storage table")
            return False

        return True

    except Exception as e:
        logger.error(f"Error checking storage table structure: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def fix_storage_table():
    """Fix the structure of the storage table."""
    db_path = find_database_file()
    if not db_path:
        logger.error("Database file not found.")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get current table structure
        cursor.execute("PRAGMA table_info(storage);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        logger.info(f"Current storage table columns: {column_names}")

        # Check which expected columns are missing
        expected_columns = [
            "id", "name", "location", "capacity", "current_occupancy",
            "type", "description", "status"
        ]

        missing_columns = [col for col in expected_columns if col not in column_names]

        if missing_columns:
            logger.info(f"Missing columns: {missing_columns}")

            # Add missing columns
            for column in missing_columns:
                # Define the column type based on its name
                if column == "id":
                    col_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
                elif column in ["capacity", "current_occupancy"]:
                    col_type = "REAL NOT NULL DEFAULT 0.0"
                elif column in ["name", "location", "type", "status"]:
                    col_type = "TEXT NOT NULL DEFAULT ''"
                else:
                    col_type = "TEXT"

                try:
                    cursor.execute(f"ALTER TABLE storage ADD COLUMN {column} {col_type};")
                    logger.info(f"Added column '{column}' to storage table")
                except Exception as e:
                    # If column already exists or other error
                    logger.error(f"Error adding column '{column}': {str(e)}")

        conn.commit()
        logger.info("Storage table structure updated successfully")
        return True

    except Exception as e:
        logger.error(f"Error fixing storage table: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def add_sample_data():
    """Add sample data to the storage table."""
    db_path = find_database_file()
    if not db_path:
        logger.error("Database file not found.")
        return False

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if there's already data
        cursor.execute("SELECT COUNT(*) FROM storage;")
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("Adding sample data to storage table...")

            # Add sample data with correct column names
            sample_data = [
                ("Main Warehouse", "Building A", 1000.0, 650.0, "Warehouse", "Main storage facility", "active"),
                ("Shelf A1", "Main Warehouse - Section A", 50.0, 30.0, "Shelf", "Small parts storage", "active"),
                ("Shelf B2", "Main Warehouse - Section B", 75.0, 45.0, "Shelf", "Medium parts storage", "active"),
                (
                "Cold Storage", "Building B", 500.0, 200.0, "Refrigerated", "Temperature controlled storage", "active"),
                ("Archive Room", "Building C", 300.0, 280.0, "Archive", "Document and sample storage", "active")
            ]

            # Get current columns to construct the SQL query correctly
            cursor.execute("PRAGMA table_info(storage);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Remove id column as it's auto-incremented
            if "id" in column_names:
                column_names.remove("id")

            # Check if we have all needed columns
            needed_columns = ["name", "location", "capacity", "current_occupancy", "type", "description", "status"]
            missing_columns = [col for col in needed_columns if col not in column_names]

            if missing_columns:
                logger.error(f"Cannot add sample data: missing columns {missing_columns}")
                return False

            # Construct INSERT statement with the right columns
            query = f"""
                INSERT INTO storage ({', '.join(needed_columns)})
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """

            cursor.executemany(query, sample_data)

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


def backup_database():
    """Create a backup of the database before modifying it."""
    db_path = find_database_file()
    if not db_path:
        logger.error("Database file not found.")
        return False

    backup_path = db_path + ".backup"

    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created database backup at: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        return False


def main():
    """Main function."""
    logger.info("Starting database structure fix...")

    # Create a backup first
    if not backup_database():
        logger.warning("Could not create a backup, proceeding without it.")

    # Check current structure
    if check_storage_table_structure():
        logger.info("Storage table structure is correct.")
    else:
        logger.warning("Storage table structure needs fixing.")

        # Ask user confirmation
        response = input("Would you like to fix the storage table structure? (y/n): ")
        if response.lower() == 'y':
            if fix_storage_table():
                logger.info("Storage table structure fixed successfully.")

                # Ask if user wants to add sample data
                response = input("Would you like to add sample data to the storage table? (y/n): ")
                if response.lower() == 'y':
                    if add_sample_data():
                        logger.info("Sample data added successfully.")
                    else:
                        logger.error("Failed to add sample data.")
            else:
                logger.error("Failed to fix storage table structure.")
        else:
            logger.info("No changes made to table structure.")


if __name__ == "__main__":
    main()