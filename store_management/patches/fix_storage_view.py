# Path: patches/fix_storage_view.py
"""
Quick fix for the storage view to debug data loading issues.
"""
import sys
import os
import logging
import tkinter as tk
from tkinter import ttk

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("storage_view_fix")


def manually_load_storage_view():
    """
    Manually create and load the storage view to debug issues.
    """
    from database.session import get_db_session
    from database.models.storage import Storage
    from application import Application

    logger.info("Starting manual storage view loading")

    # Create application
    app = Application()

    # Create a test window
    root = tk.Tk()
    root.title("Storage View Debug")
    root.geometry("800x600")

    # Create a frame to hold the view
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    # Create columns and treeview directly
    columns = ("id", "name", "location", "capacity", "occupancy", "type", "status")
    tree = ttk.Treeview(frame, columns=columns, show="headings")

    # Add column headings
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=100)

    # Add scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # Pack scrollbars and treeview
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    hsb.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Load data directly from database
    try:
        session = get_db_session()
        storage_locations = session.query(Storage).all()
        logger.info(f"Found {len(storage_locations)} storage locations")

        # Add to treeview
        for storage in storage_locations:
            tree.insert("", tk.END, values=(
                storage.id,
                storage.name,
                storage.location,
                storage.capacity,
                storage.current_occupancy,
                storage.type,
                storage.status
            ))

        # Add control buttons
        button_frame = ttk.Frame(root)
        button_frame.pack(fill=tk.X, pady=5)

        # Refresh button
        def refresh_data():
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)

            # Reload data
            session = get_db_session()
            storage_locations = session.query(Storage).all()
            logger.info(f"Refreshed: Found {len(storage_locations)} storage locations")

            # Add to treeview
            for storage in storage_locations:
                tree.insert("", tk.END, values=(
                    storage.id,
                    storage.name,
                    storage.location,
                    storage.capacity,
                    storage.current_occupancy,
                    storage.type,
                    storage.status
                ))
            session.close()

        refresh_btn = ttk.Button(button_frame, text="Refresh", command=refresh_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        close_btn = ttk.Button(button_frame, text="Close", command=root.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

        # Start the main loop
        logger.info("Starting main loop")
        root.mainloop()

    except Exception as e:
        logger.error(f"Error loading storage data: {str(e)}", exc_info=True)
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    manually_load_storage_view()