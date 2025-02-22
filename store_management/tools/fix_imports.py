# Path: tools/fix_imports.py
"""
Script to fix import issues in the project.
"""
import os
import sys
import re
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("import_fixer")


def scan_for_problematic_imports():
    """
    Scan for files with problematic imports (using store_management prefix).
    """
    logger.info("Scanning for problematic imports...")

    problematic_files = []

    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Check for imports that include 'store_management'
                        if re.search(r'(from|import)\s+store_management', content):
                            logger.info(f"Found problematic import in: {file_path}")
                            problematic_files.append(file_path)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")

    return problematic_files


def fix_imports(file_paths, dry_run=True):
    """
    Fix the imports in the specified files.

    Args:
        file_paths: List of file paths to fix
        dry_run: If True, only show what would be changed without making changes
    """
    if not file_paths:
        logger.info("No problematic files found.")
        return

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace store_management.X imports with just X
            new_content = re.sub(
                r'from\s+store_management\.([^\s]+)\s+import',
                r'from \1 import',
                content
            )

            # Replace direct store_management imports
            new_content = re.sub(
                r'import\s+store_management\.([^\s]+)',
                r'import \1',
                new_content
            )

            # Check if any changes were made
            if content != new_content:
                if dry_run:
                    logger.info(f"Would fix imports in: {file_path}")

                    # Show a diff of the changes
                    original_lines = content.splitlines()
                    new_lines = new_content.splitlines()

                    for i, (orig, new) in enumerate(zip(original_lines, new_lines)):
                        if orig != new:
                            logger.info(f"  Line {i + 1}:")
                            logger.info(f"    - {orig}")
                            logger.info(f"    + {new}")
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logger.info(f"Fixed imports in: {file_path}")
            else:
                logger.info(f"No problematic imports found in: {file_path}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")


def create_standalone_viewer():
    """
    Create a standalone storage viewer script that doesn't rely on the application.
    """
    viewer_path = "tools/standalone_storage_viewer.py"

    viewer_code = """
# Path: tools/standalone_storage_viewer.py
\"\"\"
Standalone storage viewer that directly accesses the database.
\"\"\"
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
    \"\"\"Find the SQLite database file.\"\"\"
    # List of possible locations
    possible_locations = [
        "store_management.db",
        "data/store_management.db",
        "database/store_management.db",
        "config/database/store_management.db"
    ]

    for location in possible_locations:
        if os.path.exists(location):
            return location

    # If not found in the predefined locations, search for it
    logger.info("Searching for database file...")
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                logger.info(f"Found database file: {path}")
                return path

    return None

class StorageViewer:
    \"\"\"Simple viewer for storage data.\"\"\"

    def __init__(self, root):
        \"\"\"Initialize the viewer.\"\"\"
        self.root = root
        self.root.title("Storage Locations Viewer")
        self.root.geometry("800x600")

        self.setup_ui()
        self.db_path = find_database_file()

        if not self.db_path:
            self.show_error("Database Error", "Could not find the database file.")

    def setup_ui(self):
        \"\"\"Set up the user interface.\"\"\"
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

    def load_data(self):
        \"\"\"Load storage data from the database.\"\"\"
        # Clear existing data
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.db_path:
            self.status_var.set("Database not found")
            return

        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if storage table exists
            cursor.execute(\"\"\"
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='storage';
            \"\"\")
            if not cursor.fetchone():
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
                values = [row[i] if i < len(row) else "" for i in range(7)]
                self.tree.insert("", tk.END, values=values)

            self.status_var.set(f"Loaded {len(rows)} storage locations")
            logger.info(f"Loaded {len(rows)} storage locations")

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_error(self, title, message):
        \"\"\"Show an error message.\"\"\"
        from tkinter import messagebox
        messagebox.showerror(title, message)

def main():
    \"\"\"Main function.\"\"\"
    root = tk.Tk()
    app = StorageViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
"""

    try:
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(viewer_code.lstrip())
        logger.info(f"Created standalone viewer at: {viewer_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating standalone viewer: {str(e)}")
        return False


def main():
    """Main function."""
    logger.info("Starting import fixer...")

    # Check for problematic imports
    problematic_files = scan_for_problematic_imports()

    if problematic_files:
        logger.info(f"Found {len(problematic_files)} files with problematic imports.")

        # Show what would be changed first
        fix_imports(problematic_files, dry_run=True)

        # Ask user if they want to apply the fixes
        response = input("Do you want to fix these imports? (y/n): ")
        if response.lower() == 'y':
            fix_imports(problematic_files, dry_run=False)
            logger.info("Imports fixed successfully.")
        else:
            logger.info("No changes made.")
    else:
        logger.info("No problematic imports found.")

    # Create standalone viewer
    logger.info("Creating standalone storage viewer...")
    if create_standalone_viewer():
        logger.info(
            "Standalone viewer created successfully. You can run it with: python tools/standalone_storage_viewer.py")


if __name__ == "__main__":
    main()