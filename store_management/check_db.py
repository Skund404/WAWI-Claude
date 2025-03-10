# check_db.py
import os
from pathlib import Path

# Function to search for the database file
def find_db_file(start_dir, filename="leatherworking_database.db"):
    for root, dirs, files in os.walk(start_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None

# List potential database locations
base_dir = Path(__file__).resolve().parent
data_dir = base_dir / 'data'
alt_data_dir = base_dir / 'database' / 'data'

# Check if database exists in expected locations
print(f"Checking standard data directory: {data_dir}")
db_path = data_dir / 'leatherworking_database.db'
if db_path.exists():
    print(f"Database found at: {db_path}")
    print(f"File size: {db_path.stat().st_size} bytes")
else:
    print(f"Database not found at expected path: {db_path}")

# Check alternative location
print(f"\nChecking alternative data directory: {alt_data_dir}")
alt_db_path = alt_data_dir / 'leatherworking_database.db'
if alt_db_path.exists():
    print(f"Database found at: {alt_db_path}")
    print(f"File size: {alt_db_path.stat().st_size} bytes")
else:
    print(f"Database not found at alternative path: {alt_db_path}")

# Search for the database file in the project directory
print("\nSearching for database file in project directory...")
found_path = find_db_file(base_dir)
if found_path:
    print(f"Database found at: {found_path}")
    print(f"File size: {os.path.getsize(found_path)} bytes")
else:
    print("Database not found in project directory.")