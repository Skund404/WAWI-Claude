# database_init.py
import sqlite3
from pathlib import Path


def init_database():
    # Create database directory if it doesn't exist
    db_dir = Path("../database")
    db_dir.mkdir(exist_ok=True)

    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_dir / 'store_management.db')
    cursor = conn.cursor()

    # Create tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS shelf (
            unique_id_leather TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            color TEXT NOT NULL,
            thickness REAL NOT NULL,
            size_ft REAL NOT NULL,
            area_sqft REAL NOT NULL,
            shelf TEXT UNIQUE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS storage (
            unique_id_product TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            collection TEXT,
            color TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK (amount >= 0),
            bin TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recipe_index (
            unique_id_product TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            collection TEXT,
            notes TEXT,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recipe_details (
            recipe_id TEXT,
            unique_id_parts TEXT,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            amount INTEGER NOT NULL,
            size TEXT,
            in_storage INTEGER,
            pattern_id TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipe_index(unique_id_product),
            FOREIGN KEY (unique_id_parts) REFERENCES sorting_system(unique_id_parts),
            PRIMARY KEY (recipe_id, unique_id_parts)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sorting_system (
            unique_id_parts TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            in_storage INTEGER NOT NULL DEFAULT 0,
            bin TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_views (
            view_id TEXT PRIMARY KEY,
            view_name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            column_order TEXT NOT NULL,
            column_widths TEXT NOT NULL,
            sort_column TEXT,
            sort_direction TEXT,
            filter_conditions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            action TEXT NOT NULL,
            record_id TEXT NOT NULL,
            old_values TEXT,
            new_values TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]

    # Execute each table creation command
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"Successfully created table")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database initialization completed successfully!")


if __name__ == "__main__":
    init_database()