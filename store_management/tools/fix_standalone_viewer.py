# Path: tools/fix_standalone_viewer.py
"""
Fix for the standalone storage viewer.
"""
import os


def fix_viewer():
    """Fix the standalone storage viewer."""
    viewer_path = "tools/standalone_storage_viewer.py"

    if not os.path.exists(viewer_path):
        print(f"Standalone viewer not found at {viewer_path}")
        return False

    # Read the file
    with open(viewer_path, 'r') as f:
        content = f.read()

    # Fix the db_path initialization issue
    fixed_content = content.replace(
        "def __init__(self, root):",
        "def __init__(self, root):\n        \"\"\"Initialize the viewer.\"\"\"\n        self.root = root\n        self.root.title(\"Storage Locations Viewer\")\n        self.root.geometry(\"800x600\")\n        \n        self.db_path = find_database_file()\n        \n        if not self.db_path:\n            self.show_error(\"Database Error\", \"Could not find the database file.\")\n            \n        self.setup_ui()"
    )

    # Remove the duplicate setup in setup_ui method
    fixed_content = fixed_content.replace(
        "def setup_ui(self):\n        \"\"\"Set up the user interface.\"\"\"\n        # Main frame\n        main_frame = ttk.Frame(self.root, padding=\"10\")\n        main_frame.pack(fill=tk.BOTH, expand=True)\n        \n        # Button frame\n        button_frame = ttk.Frame(main_frame)\n        button_frame.pack(fill=tk.X, pady=(0, 10))\n        \n        refresh_btn = ttk.Button(button_frame, text=\"Refresh Data\", command=self.load_data)\n        refresh_btn.pack(side=tk.LEFT, padx=5)\n        \n        # Tree view\n        self.tree = ttk.Treeview(main_frame)\n        self.tree[\"columns\"] = (\"id\", \"name\", \"location\", \"capacity\", \"occupancy\", \"type\", \"status\")\n        \n        # Configure columns\n        self.tree.column(\"#0\", width=0, stretch=tk.NO)  # Hidden column\n        self.tree.column(\"id\", width=50, anchor=tk.CENTER)\n        self.tree.column(\"name\", width=150, anchor=tk.W)\n        self.tree.column(\"location\", width=150, anchor=tk.W)\n        self.tree.column(\"capacity\", width=100, anchor=tk.E)\n        self.tree.column(\"occupancy\", width=100, anchor=tk.E)\n        self.tree.column(\"type\", width=100, anchor=tk.W)\n        self.tree.column(\"status\", width=100, anchor=tk.W)\n        \n        # Configure headings\n        self.tree.heading(\"#0\", text=\"\")\n        self.tree.heading(\"id\", text=\"ID\")\n        self.tree.heading(\"name\", text=\"Name\")\n        self.tree.heading(\"location\", text=\"Location\")\n        self.tree.heading(\"capacity\", text=\"Capacity\")\n        self.tree.heading(\"occupancy\", text=\"Occupancy\")\n        self.tree.heading(\"type\", text=\"Type\")\n        self.tree.heading(\"status\", text=\"Status\")\n        \n        # Scrollbars\n        vsb = ttk.Scrollbar(main_frame, orient=\"vertical\", command=self.tree.yview)\n        hsb = ttk.Scrollbar(main_frame, orient=\"horizontal\", command=self.tree.xview)\n        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)\n        \n        # Grid layout\n        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)\n        vsb.pack(side=tk.RIGHT, fill=tk.Y)\n        hsb.pack(side=tk.BOTTOM, fill=tk.X)\n        \n        # Status bar\n        self.status_var = tk.StringVar()\n        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)\n        status_bar.pack(side=tk.BOTTOM, fill=tk.X)\n        \n        # Load data\n        self.load_data()",
        "def setup_ui(self):\n        \"\"\"Set up the user interface.\"\"\"\n        # Main frame\n        main_frame = ttk.Frame(self.root, padding=\"10\")\n        main_frame.pack(fill=tk.BOTH, expand=True)\n        \n        # Button frame\n        button_frame = ttk.Frame(main_frame)\n        button_frame.pack(fill=tk.X, pady=(0, 10))\n        \n        refresh_btn = ttk.Button(button_frame, text=\"Refresh Data\", command=self.load_data)\n        refresh_btn.pack(side=tk.LEFT, padx=5)\n        \n        # Tree view\n        self.tree = ttk.Treeview(main_frame)\n        self.tree[\"columns\"] = (\"id\", \"name\", \"location\", \"capacity\", \"occupancy\", \"type\", \"status\")\n        \n        # Configure columns\n        self.tree.column(\"#0\", width=0, stretch=tk.NO)  # Hidden column\n        self.tree.column(\"id\", width=50, anchor=tk.CENTER)\n        self.tree.column(\"name\", width=150, anchor=tk.W)\n        self.tree.column(\"location\", width=150, anchor=tk.W)\n        self.tree.column(\"capacity\", width=100, anchor=tk.E)\n        self.tree.column(\"occupancy\", width=100, anchor=tk.E)\n        self.tree.column(\"type\", width=100, anchor=tk.W)\n        self.tree.column(\"status\", width=100, anchor=tk.W)\n        \n        # Configure headings\n        self.tree.heading(\"#0\", text=\"\")\n        self.tree.heading(\"id\", text=\"ID\")\n        self.tree.heading(\"name\", text=\"Name\")\n        self.tree.heading(\"location\", text=\"Location\")\n        self.tree.heading(\"capacity\", text=\"Capacity\")\n        self.tree.heading(\"occupancy\", text=\"Occupancy\")\n        self.tree.heading(\"type\", text=\"Type\")\n        self.tree.heading(\"status\", text=\"Status\")\n        \n        # Scrollbars\n        vsb = ttk.Scrollbar(main_frame, orient=\"vertical\", command=self.tree.yview)\n        hsb = ttk.Scrollbar(main_frame, orient=\"horizontal\", command=self.tree.xview)\n        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)\n        \n        # Grid layout\n        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)\n        vsb.pack(side=tk.RIGHT, fill=tk.Y)\n        hsb.pack(side=tk.BOTTOM, fill=tk.X)\n        \n        # Status bar\n        self.status_var = tk.StringVar()\n        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)\n        status_bar.pack(side=tk.BOTTOM, fill=tk.X)"
    )

    # Write the fixed content back
    with open(viewer_path, 'w') as f:
        f.write(fixed_content)

    print(f"Fixed standalone viewer at {viewer_path}")
    return True


if __name__ == "__main__":
    fix_viewer()