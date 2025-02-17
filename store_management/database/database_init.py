# database_init.py
import sqlite3
from pathlib import Path

def init_database():
    """Initialize the database with all required tables"""
    # Get the directory where the script is located
    db_path = Path(__file__).parent.parent / 'store_management.db'

    print(f"Initializing database at: {db_path}")

    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables with full scripts
    cursor.executescript('''
        -- Supplier management
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
            last_order_date TEXT,
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

        -- Sorting System
        CREATE TABLE IF NOT EXISTS sorting_system (
            unique_id_parts TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            in_storage INTEGER DEFAULT 0,
            bin TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Storage
        CREATE TABLE IF NOT EXISTS storage (
            unique_id_product TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            collection TEXT,
            color TEXT NOT NULL,
            amount INTEGER NOT NULL,
            bin TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Recipe Index
        CREATE TABLE IF NOT EXISTS recipe_index (
            unique_id_product TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            collection TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Recipe Details
        CREATE TABLE IF NOT EXISTS recipe_details (
            recipe_id TEXT NOT NULL,
            unique_id_parts TEXT NOT NULL,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            amount INTEGER NOT NULL,
            size REAL,
            in_storage INTEGER,
            pattern_id TEXT,
            notes TEXT,
            PRIMARY KEY (recipe_id, unique_id_parts),
            FOREIGN KEY (recipe_id) REFERENCES recipe_index(unique_id_product),
            FOREIGN KEY (unique_id_parts) REFERENCES sorting_system(unique_id_parts)
        );

        -- Orders Table
        CREATE TABLE IF NOT EXISTS orders (
            order_number TEXT PRIMARY KEY,
            supplier TEXT NOT NULL,
            date_of_order TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('ordered', 'being processed', 'shipped', 'received', 'returned', 'partially returned', 'completed')),
            payed TEXT NOT NULL CHECK(payed IN ('yes', 'no')) DEFAULT 'no',
            total_amount REAL DEFAULT 0,
            shipping_cost REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier) REFERENCES supplier(company_name)
        );

        -- Note: Order details tables will be created dynamically at runtime
    ''')

    # Add indexes for better performance
    cursor.executescript('''
        -- Supplier Indexes
        CREATE INDEX IF NOT EXISTS idx_supplier_business_type ON supplier(business_type);
        CREATE INDEX IF NOT EXISTS idx_supplier_country ON supplier(country);
        CREATE INDEX IF NOT EXISTS idx_supplier_payment_terms ON supplier(payment_terms);

        -- Shelf Indexes
        CREATE INDEX IF NOT EXISTS idx_shelf_type ON shelf(type);
        CREATE INDEX IF NOT EXISTS idx_shelf_color ON shelf(color);

        -- Sorting System Indexes
        CREATE INDEX IF NOT EXISTS idx_sorting_system_bin ON sorting_system(bin);
        CREATE INDEX IF NOT EXISTS idx_sorting_system_color ON sorting_system(color);

        -- Storage Indexes
        CREATE INDEX IF NOT EXISTS idx_storage_bin ON storage(bin);
        CREATE INDEX IF NOT EXISTS idx_storage_type ON storage(type);

        -- Orders Indexes
        CREATE INDEX IF NOT EXISTS idx_orders_supplier ON orders(supplier);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(date_of_order);
        CREATE INDEX IF NOT EXISTS idx_orders_payment ON orders(payed);
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()