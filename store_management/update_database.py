import sqlite3
from pathlib import Path
import datetime

# Use relative import or full path
DATABASE_PATH = Path(__file__).parent / "store_management.db"


def table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    """Check if a specific column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Add a column to a table if it doesn't already exist."""
    if not column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"Added {column_name} column to {table_name}")
            return True
        except sqlite3.OperationalError as e:
            print(f"Error adding {column_name} to {table_name}: {e}")
            return False
    return False


def update_recipe_tables():
    """
    Update recipe-related tables with necessary schema changes.
    This function handles:
    1. Adding missing columns
    2. Creating tables if they don't exist
    3. Restructuring tables if needed
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Recipe Index Table
        if not table_exists(cursor, 'recipe_index'):
            cursor.execute('''
                CREATE TABLE recipe_index (
                    unique_id_product TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    collection TEXT,
                    color TEXT,
                    pattern_id TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    modified_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Created recipe_index table")
        else:
            # Add missing columns to existing table
            columns_to_add = [
                ('color', 'TEXT'),
                ('pattern_id', 'TEXT'),
                ('created_at', 'TEXT DEFAULT CURRENT_TIMESTAMP'),
                ('modified_at', 'TEXT DEFAULT CURRENT_TIMESTAMP')
            ]

            for column_name, column_type in columns_to_add:
                add_column_if_not_exists(cursor, 'recipe_index', column_name, column_type)

        # Recipe Details Table
        if not table_exists(cursor, 'recipe_details'):
            cursor.execute('''
                CREATE TABLE recipe_details (
                    recipe_id TEXT,
                    unique_id_parts TEXT,
                    name TEXT,
                    color TEXT,
                    amount INTEGER,
                    size TEXT,
                    in_storage INTEGER,
                    notes TEXT,
                    pattern_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (recipe_id, unique_id_parts)
                )
            ''')
            print("Created recipe_details table")
        else:
            # Add missing columns to existing table
            columns_to_add = [
                ('color', 'TEXT'),
                ('pattern_id', 'TEXT'),
                ('created_at', 'TEXT DEFAULT CURRENT_TIMESTAMP'),
                ('modified_at', 'TEXT DEFAULT CURRENT_TIMESTAMP')
            ]

            for column_name, column_type in columns_to_add:
                add_column_if_not_exists(cursor, 'recipe_details', column_name, column_type)

        # Commit changes
        conn.commit()
        print(f"Database update completed at {timestamp}")

    except sqlite3.Error as e:
        print(f"Database update error: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    """Main function to run database updates."""
    print("Starting database update process...")
    update_recipe_tables()
    print("Database update process completed.")


if __name__ == "__main__":
    main()