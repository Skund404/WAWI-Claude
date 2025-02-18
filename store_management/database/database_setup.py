import sqlite3
import os
from pathlib import Path

def setup_database():
    """
    Alias for create_database to maintain backward compatibility.
    Creates the database with all necessary tables.
    """
    create_database()

def create_database():
    """
    Create the database with all necessary tables.

    This function ensures that all required tables are created with proper schemas,
    including relationships between tables and appropriate constraints.
    """
    # Use Path for more robust path handling
    current_dir = Path(__file__).parent
    db_path = current_dir / 'store_management.db'

    # Connect to database (will create if it doesn't exist)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Create tables with appropriate order to manage foreign key constraints
        cursor.executescript('''
            -- Sorting system (referenced by other tables)
            CREATE TABLE IF NOT EXISTS sorting_system (
            unique_id_parts TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            in_storage INTEGER NOT NULL DEFAULT 0,
            warning_threshold INTEGER NOT NULL DEFAULT 5,  -- Add this line
            bin TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Supplier table
            CREATE TABLE IF NOT EXISTS supplier (
                company_name TEXT PRIMARY KEY,
                contact_person TEXT,
                phone_number TEXT,
                email_address TEXT,
                website TEXT,
                street_address TEXT,
                city TEXT,
                state_province TEXT,
                postal_code TEXT,
                country TEXT,
                tax_id TEXT,
                business_type TEXT,
                payment_terms TEXT,
                currency TEXT,
                bank_details TEXT,
                products_offered TEXT,
                lead_time TEXT,
                last_order_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

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

            -- Recipe details (with foreign key constraints)
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

            -- Orders table (added for completeness)
            CREATE TABLE IF NOT EXISTS orders (
                order_number TEXT PRIMARY KEY,
                supplier TEXT NOT NULL,
                date_of_order DATE NOT NULL,
                status TEXT NOT NULL,
                payed TEXT NOT NULL,
                total_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier) REFERENCES supplier(company_name)
            );
        ''')

        # Commit changes
        conn.commit()
        print("Database created successfully with all tables!")

    except sqlite3.Error as e:
        print(f"An error occurred while creating the database: {e}")
        conn.rollback()

    finally:
        # Always close the connection
        conn.close()


def ensure_database():
    """
    Ensure database exists and is set up correctly.
    Creates the database if it doesn't exist.
    """
    db_path = Path(__file__).parent / 'store_management.db'

    # If database doesn't exist, create it
    if not db_path.exists():
        create_database()


def verify_database():
    """
    Verify the database structure and print out table information.
    Useful for debugging and confirming table creation.
    """
    current_dir = Path(__file__).parent
    db_path = current_dir / 'store_management.db'

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")

            # Print schema for each table
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            print("  Columns:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            print()

    except sqlite3.Error as e:
        print(f"An error occurred while verifying the database: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    # Remove existing database to start fresh
    current_dir = Path(__file__).parent
    db_path = current_dir / 'store_management.db'

    if db_path.exists():
        os.remove(db_path)

    # Create and verify the database
    create_database()
    verify_database()