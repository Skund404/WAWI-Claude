import sqlite3
from pathlib import Path
from config import DATABASE_PATH, TABLES


def check_database():
    """Check database structure and attempt to fix issues"""
    print(f"Checking database at: {DATABASE_PATH}")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Check table structure
        cursor.execute(f"PRAGMA table_info({TABLES['SORTING_SYSTEM']})")
        columns = cursor.fetchall()
        print("\nCurrent table structure:")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, DefaultValue: {col[4]}")

        # Check if warning_threshold exists
        has_warning_threshold = any(col[1] == 'warning_threshold' for col in columns)

        if not has_warning_threshold:
            print("\nWarning threshold column missing. Adding it now...")
            try:
                cursor.execute(f'''
                    ALTER TABLE {TABLES['SORTING_SYSTEM']}
                    ADD COLUMN warning_threshold INTEGER NOT NULL DEFAULT 5
                ''')
                conn.commit()
                print("Successfully added warning_threshold column")

                # Verify the addition
                cursor.execute(f"PRAGMA table_info({TABLES['SORTING_SYSTEM']})")
                columns = cursor.fetchall()
                print("\nUpdated table structure:")
                for col in columns:
                    print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, DefaultValue: {col[4]}")

            except sqlite3.Error as e:
                print(f"Error adding column: {e}")

        else:
            print("\nwarning_threshold column already exists")

        # Show sample data
        print("\nSample data from table:")
        cursor.execute(f"SELECT * FROM {TABLES['SORTING_SYSTEM']} LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_database()