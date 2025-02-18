import sqlite3
from pathlib import Path
from config import DATABASE_PATH, TABLES


def update_sorting_system():
    """Add warning_threshold column to sorting_system table"""
    print(f"Connecting to database at: {DATABASE_PATH}")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({TABLES['SORTING_SYSTEM']})")
        columns = [column[1] for column in cursor.fetchall()]

        if 'warning_threshold' not in columns:
            print("Adding warning_threshold column...")
            cursor.execute(f'''
                ALTER TABLE {TABLES['SORTING_SYSTEM']}
                ADD COLUMN warning_threshold INTEGER NOT NULL DEFAULT 5
            ''')
            conn.commit()
            print("Successfully added warning_threshold column")
        else:
            print("Column warning_threshold already exists")

        # Verify the column was added
        cursor.execute(f"PRAGMA table_info({TABLES['SORTING_SYSTEM']})")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in sorting_system: {columns}")

    except sqlite3.Error as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    update_sorting_system()