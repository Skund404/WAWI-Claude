# database/add_color_column.py
import sqlite3
from pathlib import Path

# Use the same database path as in config.py
DATABASE_PATH = Path(__file__).parent.parent / 'database' / 'store_management.db'


def add_color_column():
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    try:
        # Check if color column exists
        cursor.execute("PRAGMA table_info(recipe_index)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'color' not in columns:
            # Add color column
            cursor.execute("ALTER TABLE recipe_index ADD COLUMN color TEXT")
            print("Added 'color' column to recipe_index")
            conn.commit()
        else:
            print("'color' column already exists")

        # Print out all columns to verify
        print("Columns in recipe_index:")
        cursor.execute("PRAGMA table_info(recipe_index)")
        for column in cursor.fetchall():
            print(f"- {column[1]} ({column[2]})")

    except sqlite3.Error as e:
        print(f"Error adding 'color' column: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    add_color_column()