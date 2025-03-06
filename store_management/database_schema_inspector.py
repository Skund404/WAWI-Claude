# database_schema_inspector.py
import sqlite3
from sqlalchemy import create_engine, inspect


def inspect_table_schema(db_path, table_name):
    """
    Inspect the schema of a specific table using SQLite direct connection.

    Args:
        db_path (str): Path to the SQLite database
        table_name (str): Name of the table to inspect
    """
    # SQLite direct connection method
    print("=== SQLite Direct Connection Schema ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print(f"Columns in {table_name}:")
        for column in columns:
            print(f"  {column[1]} ({column[2]}): {column[4]} {'PRIMARY KEY' if column[5] else ''}")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

    # SQLAlchemy inspection method
    print("\n=== SQLAlchemy Inspection ===")
    engine = create_engine(f'sqlite:///{db_path}')
    inspector = inspect(engine)

    try:
        columns = inspector.get_columns(table_name)
        print(f"Columns in {table_name} (SQLAlchemy):")
        for column in columns:
            print(f"  {column['name']}: {column['type']}")
    except Exception as e:
        print(f"SQLAlchemy Inspection Error: {e}")


def main():
    db_path = 'data/database.db'
    tables_to_inspect = ['materials', 'storages']

    for table in tables_to_inspect:
        print(f"\nInspecting {table.upper()} table:")
        inspect_table_schema(db_path, table)


if __name__ == "__main__":
    main()