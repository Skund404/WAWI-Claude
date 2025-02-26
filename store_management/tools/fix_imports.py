from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Script to fix import issues in the project.
"""
logging.basicConfig(
level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("import_fixer")


def scan_for_problematic_imports():
    pass
"""
Scan for files with problematic imports (using store_management prefix).
"""
logger.info("Scanning for problematic imports...")
problematic_files = []
for root, _, files in os.walk(""):
    pass
for file in files:
    pass
if file.endswith(".py"):
    pass
file_path = os.path.join(root, file)
try:
    pass
with open(file_path, "r", encoding="utf-8") as f:
    pass
content = f.read()
if re.search("(from|import)\\s+store_management", content):
    pass
logger.info(
f"Found problematic import in: {file_path}")
problematic_files.append(file_path)
except Exception as e:
    pass
logger.error(f"Error reading file {file_path}: {str(e)}")
return problematic_files


def fix_imports(file_paths, dry_run=True):
    pass
"""
Fix the imports in the specified files.

Args:
file_paths: List of file paths to fix
dry_run: If True, only show what would be changed without making changes
"""
if not file_paths:
    pass
logger.info("No problematic files found.")
return
for file_path in file_paths:
    pass
try:
    pass
with open(file_path, "r", encoding="utf-8") as f:
    pass
content = f.read()
new_content = re.sub(
"from\\s+store_management\\.([^\\s]+)\\s+import",
"from \\1 import",
content,
)
new_content = re.sub(
"import\\s+store_management\\.([^\\s]+)", "import \\1", new_content
)
if content != new_content:
    pass
if dry_run:
    pass
logger.info(f"Would fix imports in: {file_path}")
original_lines = content.splitlines()
new_lines = new_content.splitlines()
for i, (orig, new) in enumerate(zip(original_lines, new_lines)):
    pass
if orig != new:
    pass
logger.info(f"  Line {i + 1}:")
logger.info(f"    - {orig}")
logger.info(f"    + {new}")
else:
with open(file_path, "w", encoding="utf-8") as f:
    pass
f.write(new_content)
logger.info(f"Fixed imports in: {file_path}")
else:
logger.info(f"No problematic imports found in: {file_path}")
except Exception as e:
    pass
logger.error(f"Error processing file {file_path}: {str(e)}")


def create_standalone_viewer():
    pass
"""
Create a standalone storage viewer script that doesn't rely on the application.
"""
viewer_path = "tools/standalone_storage_viewer.py"
viewer_code = """
# Path: tools/standalone_storage_viewer.py
""\"
Standalone storage viewer that directly accesses the database.
""\"
import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("standalone_viewer")

def find_database_file():
    pass
""\"Find the SQLite database file.""\"
# List of possible locations
possible_locations = [
"store_management.db",
"data/store_management.db",
"database/store_management.db",
"config/database/store_management.db"
]

for location in possible_locations:
    pass
if os.path.exists(location):
    pass
return location

# If not found in the predefined locations, search for it
logger.info("Searching for database file...")
for root, _, files in os.walk("."):
    pass
for file in files:
    pass
if file.endswith('.db'):
    pass
path = os.path.join(root, file)
logger.info(f"Found database file: {path}")
return path

return None

class StorageViewer:
    pass
""\"Simple viewer for storage data.""\"

@inject(MaterialService)
def __init__(self, root):
    pass
""\"Initialize the viewer.""\"
self.root = root
self.root.title("Storage Locations Viewer")
self.root.geometry("800x600")

self.setup_ui()
self.db_path = find_database_file()

if not self.db_path:
    pass
self.show_error("Database Error", "Could not find the database file.")

@inject(MaterialService)
def setup_ui(self):
    pass
""\"Set up the user interface.""\"
# Main frame
main_frame = ttk.Frame(self.root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Button frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=(0, 10))

refresh_btn = ttk.Button(button_frame, text="Refresh Data", command=self.load_data)
refresh_btn.pack(side=tk.LEFT, padx=5)

# Tree view
self.tree = ttk.Treeview(main_frame)
self.tree["columns"] = ("id", "name", "location", "capacity", "occupancy", "type", "status")

# Configure columns
self.tree.column("#0", width=0, stretch=tk.NO)  # Hidden column
self.tree.column("id", width=50, anchor=tk.CENTER)
self.tree.column("name", width=150, anchor=tk.W)
self.tree.column("location", width=150, anchor=tk.W)
self.tree.column("capacity", width=100, anchor=tk.E)
self.tree.column("occupancy", width=100, anchor=tk.E)
self.tree.column("type", width=100, anchor=tk.W)
self.tree.column("status", width=100, anchor=tk.W)

# Configure headings
self.tree.heading("#0", text="")
self.tree.heading("id", text="ID")
self.tree.heading("name", text="Name")
self.tree.heading("location", text="Location")
self.tree.heading("capacity", text="Capacity")
self.tree.heading("occupancy", text="Occupancy")
self.tree.heading("type", text="Type")
self.tree.heading("status", text="Status")

# Scrollbars
vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

# Grid layout
self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
hsb.pack(side=tk.BOTTOM, fill=tk.X)

# Status bar
self.status_var = tk.StringVar()
status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Load data
self.load_data()

@inject(MaterialService)
def load_data(self):
    pass
""\"Load storage data from the database.""\"
# Clear existing data
for i in self.tree.get_children():
    pass
self.tree.delete(i)

if not self.db_path:
    pass
self.status_var.set("Database not found")
return

try:
    pass
# Connect to the database
conn = sqlite3.connect(self.db_path)
cursor = conn.cursor()

# Check if storage table exists
cursor.execute(""\"
SELECT name FROM sqlite_master 
WHERE type='table' AND name='storage';
""\")
if not cursor.fetchone():
    pass
self.status_var.set("Storage table doesn't exist")
return

# Get the data
cursor.execute("SELECT * FROM storage;")
rows = cursor.fetchall()

# Get column names
cursor.execute("PRAGMA table_info(storage);")
columns = [info[1] for info in cursor.fetchall()]

# Insert data into tree
for row in rows:
    pass
values = [row[i] if i < len(row) else "" for i in range(7)]
self.tree.insert("", tk.END, values=values)

self.status_var.set(f"Loaded {len(rows)} storage locations")
logger.info(f"Loaded {len(rows)} storage locations")

except Exception as e:
    pass
logger.error(f"Error loading data: {str(e)}")
self.status_var.set(f"Error: {str(e)}")
finally:
if 'conn' in locals():
    pass
conn.close()

@inject(MaterialService)
def show_error(self, title, message):
    pass
""\"Show an error message.""\"
from tkinter import messagebox
messagebox.showerror(title, message)

def main():
    pass
""\"Main function.""\"
root = tk.Tk()
app = StorageViewer(root)
root.mainloop()

if __name__ == "__main__":
    pass
main()
"""
try:
    pass
with open(viewer_path, "w", encoding="utf-8") as f:
    pass
f.write(viewer_code.lstrip())
logger.info(f"Created standalone viewer at: {viewer_path}")
return True
except Exception as e:
    pass
logger.error(f"Error creating standalone viewer: {str(e)}")
return False


def main():
    pass
"""Main function."""
logger.info("Starting import fixer...")
problematic_files = scan_for_problematic_imports()
if problematic_files:
    pass
logger.info(
f"Found {len(problematic_files)} files with problematic imports.")
fix_imports(problematic_files, dry_run=True)
response = input("Do you want to fix these imports? (y/n): ")
if response.lower() == "y":
    pass
fix_imports(problematic_files, dry_run=False)
logger.info("Imports fixed successfully.")
else:
logger.info("No changes made.")
else:
logger.info("No problematic imports found.")
logger.info("Creating standalone storage viewer...")
if create_standalone_viewer():
    pass
logger.info(
"Standalone viewer created successfully. You can run it with: python tools/standalone_storage_viewer.py"
)


if __name__ == "__main__":
    pass
main()
