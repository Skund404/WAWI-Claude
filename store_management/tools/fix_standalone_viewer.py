from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
Fix for the standalone storage viewer.
"""


def fix_viewer():
    """Fix the standalone storage viewer."""
    viewer_path = "tools/standalone_storage_viewer.py"
    if not os.path.exists(viewer_path):
        print(f"Standalone viewer not found at {viewer_path}")
        return False
    with open(viewer_path, "r") as f:
        content = f.read()
    fixed_content = content.replace(
        "def __init__(self, root):",
        """def __init__(self, root):
        ""\"Initialize the viewer.""\"
        self.root = root
        self.root.title("Storage Locations Viewer")
        self.root.geometry("800x600")

        self.db_path = find_database_file()

        if not self.db_path:
            self.show_error("Database Error", "Could not find the database file.")

        self.setup_ui()""",
    )
    fixed_content = fixed_content.replace(
        """def setup_ui(self):
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
        self.load_data()""",
        """def setup_ui(self):
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
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)""",
    )
    with open(viewer_path, "w") as f:
        f.write(fixed_content)
    print(f"Fixed standalone viewer at {viewer_path}")
    return True


if __name__ == "__main__":
    fix_viewer()
