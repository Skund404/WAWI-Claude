import sys
import os

# Add the parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function that gets the database path
from config.settings import get_database_path

# Print the database path
db_path = get_database_path()
print(f"Database path: {db_path}")

# Check if the file exists
if os.path.exists(db_path):
    print(f"Database file exists at this location.")
    print(f"File size: {os.path.getsize(db_path)} bytes")
else:
    print(f"Database file does not exist at this location.")