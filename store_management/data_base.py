import sqlite3
from pathlib import Path


def setup_database():
    """Create the database and all required tables"""
    # Create database in the project root directory
    db_path = Path('store_management.db')

    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create tables
        cursor.executescript('''
            -- Shelf management
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
            );

            -- Product storage
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
            );

            -- Recipe index
            CREATE TABLE IF NOT EXISTS recipe_index (
                unique_id_product TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                collection TEXT,
                notes TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Recipe details
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
            );

            -- Sorting system
            CREATE TABLE IF NOT EXISTS sorting_system (
                unique_id_parts TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                in_storage INTEGER NOT NULL DEFAULT 0,
                bin TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Table for saving view states
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
            );

            -- Audit log
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                action TEXT NOT NULL,
                record_id TEXT NOT NULL,
                old_values TEXT,
                new_values TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        conn.commit()
        print("Database setup completed successfully!")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()