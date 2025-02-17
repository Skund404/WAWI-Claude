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
            -- Orders table
            CREATE TABLE IF NOT EXISTS orders (
                order_number TEXT PRIMARY KEY,
                supplier TEXT NOT NULL,
                date_of_order DATE NOT NULL,
                status TEXT NOT NULL,
                payed TEXT NOT NULL,
                total_amount REAL DEFAULT 0,
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

            -- Shelf table
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

            -- Sorting system table
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