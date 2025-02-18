import sqlite3
import sys
from pathlib import Path

# Add the parent directory to Python path to find the local config.py
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import DATABASE_PATH, TABLES


def recreate_sorting_system():
    """Safely recreate the sorting_system table with the warning_threshold column"""
    print(f"Recreating sorting_system table at: {DATABASE_PATH}")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # First, rename the existing table
        print("Backing up existing table...")
        cursor.execute(f'''
            ALTER TABLE {TABLES['SORTING_SYSTEM']} 
            RENAME TO sorting_system_backup
        ''')

        # Create new table with all columns
        print("Creating new table with warning_threshold...")
        cursor.execute('''
            CREATE TABLE sorting_system (
                unique_id_parts TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                in_storage INTEGER NOT NULL DEFAULT 0,
                warning_threshold INTEGER NOT NULL DEFAULT 5,
                bin TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Copy data from backup table
        print("Copying data from backup...")
        cursor.execute('''
            INSERT INTO sorting_system (
                unique_id_parts, name, color, in_storage, bin, notes, 
                created_at, modified_at
            )
            SELECT unique_id_parts, name, color, in_storage, bin, notes,
                   created_at, modified_at
            FROM sorting_system_backup
        ''')

        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM sorting_system")
        new_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM sorting_system_backup")
        old_count = cursor.fetchone()[0]

        if new_count == old_count:
            print(f"Data transfer successful. {new_count} rows copied.")
            # Drop the backup table
            cursor.execute("DROP TABLE sorting_system_backup")
            conn.commit()
            print("Backup table dropped. Update complete.")
        else:
            print("Warning: Row count mismatch. Keeping backup table for verification.")
            conn.rollback()

        # Show sample data
        print("\nSample data from new table:")
        cursor.execute("SELECT * FROM sorting_system LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    except sqlite3.Error as e:
        print(f"Error recreating table: {e}")
        conn.rollback()
        print("\nError details:", str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    recreate_sorting_system()