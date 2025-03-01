import logging
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

from gui.base_view import BaseView
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel
from services.interfaces.material_service import IMaterialService, MaterialType
from utils.circular_import_resolver import lazy_import
from utils.error_handler import ApplicationError

# Use lazy imports to avoid circular dependencies
MaterialServiceImpl = lazy_import('services.implementations.material_service.MaterialServiceImpl')
ProjectServiceImpl = lazy_import('services.implementations.project_service.ProjectServiceImpl')

from database.models.enums import MaterialType, ProjectStatus, ProjectType

# Configure logger
logger = logging.getLogger(__name__)


class ProjectCostAnalyzer(BaseView):
    """
    Cost analysis tool for leatherworking projects.

    Provides functionality to:
    - Calculate material costs for a project
    - Estimate labor costs based on time and skill level
    - Add tools and overhead costs
    - Generate detailed cost breakdowns and pricing recommendations
    """

    def __init__(self, parent, controller):
        """
        Initialize the Project Cost Analyzer.

        Args:
            parent: Parent widget
            controller: Application controller
        """
        super().__init__(parent, controller)

        # Logging
        logger.info("Initializing Project Cost Analyzer")

        # Initialize status tracking
        self._status_var = tk.StringVar(value="Ready")

        # Initialize project data
        self.project_data = {
            "name": "",
            "description": "",
            "materials": [],
            "labor_hours": 0.0,
            "labor_rate": 15.0,
            "overhead_percentage": 15.0,
            "profit_margin": 30.0,
            "tools": [],
            "total_material_cost": 0.0,
            "total_labor_cost": 0.0,
            "total_overhead": 0.0,
            "total_cost": 0.0,
            "suggested_price": 0.0
        }

        # Store notebook reference
        self.notebook = None

        # Setup UI
        self._create_ui()

        # Load initial sample data
        self._load_initial_data()

        logger.info("Project Cost Analyzer initialized")

    def _create_ui(self):
        """Create the user interface for the cost analyzer."""
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for different cost analysis sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Project info tab
        project_frame = ttk.Frame(self.notebook)
        self.notebook.add(project_frame, text="Project Info")
        self._create_project_info_tab(project_frame)

        # Materials tab
        materials_frame = ttk.Frame(self.notebook)
        self.notebook.add(materials_frame, text="Materials")
        self._create_materials_tab(materials_frame)

        # Labor tab
        labor_frame = ttk.Frame(self.notebook)
        self.notebook.add(labor_frame, text="Labor")
        self._create_labor_tab(labor_frame)

        # Summary tab
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="Summary")
        self._create_summary_tab(summary_frame)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        status_label = ttk.Label(
            status_frame,
            textvariable=self._status_var,
            anchor=tk.W,
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        status_label.pack(fill=tk.X, expand=True)

    def set_status(self, message: str):
        """
        Set the status message.

        Args:
            message (str): Status message to display
        """
        try:
            self._status_var.set(message)
            logger.info(f"Status: {message}")
        except Exception as e:
            logger.error(f"Error setting status: {e}")

    def _create_project_info_tab(self, parent):
        """
        Create the project info tab.

        Args:
            parent: Parent widget for the tab
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Project details
        details_frame = ttk.LabelFrame(frame, text="Project Details")
        details_frame.pack(fill=tk.X, pady=(0, 10))

        detail_grid = ttk.Frame(details_frame)
        detail_grid.pack(fill=tk.X, padx=10, pady=10)

        # Project name
        ttk.Label(detail_grid, text="Project Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar(value="")
        ttk.Entry(detail_grid, textvariable=self.name_var, width=30).grid(
            row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        # Project type
        ttk.Label(detail_grid, text="Project Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(detail_grid, textvariable=self.type_var, width=28)
        type_combo['values'] = [t.name for t in ProjectType if t.name != "OTHER"]  # Exclude OTHER
        type_combo.grid(row=1, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        type_combo.current(0)  # Default to first type

        # Skill level
        ttk.Label(detail_grid, text="Skill Level:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.skill_var = tk.StringVar()
        skill_combo = ttk.Combobox(detail_grid, textvariable=self.skill_var, width=28)
        skill_combo['values'] = [s.name for s in SkillLevel]
        skill_combo.grid(row=2, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        skill_combo.current(1)  # Default to INTERMEDIATE

        # Description
        ttk.Label(detail_grid, text="Description:").grid(row=3, column=0, sticky=tk.NW, padx=5, pady=5)
        self.description_text = tk.Text(detail_grid, height=4, width=30)
        self.description_text.grid(row=3, column=1, sticky=tk.W + tk.E, padx=5, pady=5)
        self.description_text.insert("1.0", self.project_data.get("description", ""))

        # Configure the grid
        detail_grid.columnconfigure(1, weight=1)

        # Project dimensions
        dim_frame = ttk.LabelFrame(frame, text="Project Dimensions")
        dim_frame.pack(fill=tk.X, pady=(0, 10))

        dim_grid = ttk.Frame(dim_frame)
        dim_grid.pack(fill=tk.X, padx=10, pady=10)

        # Width, height, depth
        ttk.Label(dim_grid, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.width_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dim_grid, from_=0, to=1000, increment=0.5, textvariable=self.width_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(dim_grid, text="cm").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(dim_grid, text="Height:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.height_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dim_grid, from_=0, to=1000, increment=0.5, textvariable=self.height_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(dim_grid, text="cm").grid(row=1, column=2, sticky=tk.W)

        ttk.Label(dim_grid, text="Depth:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.depth_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(dim_grid, from_=0, to=1000, increment=0.5, textvariable=self.depth_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(dim_grid, text="cm").grid(row=2, column=2, sticky=tk.W)

        # Add notes frame
        notes_frame = ttk.LabelFrame(frame, text="Notes")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.notes_text = tk.Text(notes_frame, height=6)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Complexity factor
        complexity_frame = ttk.LabelFrame(frame, text="Project Complexity")
        complexity_frame.pack(fill=tk.X, pady=(0, 10))

        complexity_grid = ttk.Frame(complexity_frame)
        complexity_grid.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(complexity_grid, text="Complexity Factor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.complexity_var = tk.DoubleVar(value=1.0)  # 1.0 = normal complexity
        complexity_scale = ttk.Scale(complexity_grid, from_=0.5, to=2.0, orient=tk.HORIZONTAL,
                                     variable=self.complexity_var, length=200)
        complexity_scale.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        # Add labels for the scale
        ttk.Label(complexity_grid, text="Simple").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(complexity_grid, text="Complex").grid(row=1, column=1, sticky=tk.E, padx=5)

        # Show numeric value
        complexity_label = ttk.Label(complexity_grid, textvariable=self.complexity_var)
        complexity_label.grid(row=0, column=2, padx=5, pady=5)

        # Update label when scale changes
        complexity_scale.bind("<Motion>", lambda e: self.complexity_var.set(round(self.complexity_var.get(), 2)))

    def _create_materials_tab(self, parent):
        """
        Create the materials tab.

        Args:
            parent: Parent widget for the tab
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Material input
        input_frame = ttk.LabelFrame(frame, text="Add Material")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        input_grid = ttk.Frame(input_frame)
        input_grid.pack(fill=tk.X, padx=10, pady=10)

        # Material details
        ttk.Label(input_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_name_var = tk.StringVar()
        ttk.Entry(input_grid, textvariable=self.material_name_var, width=20).grid(
            row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        ttk.Label(input_grid, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.material_type_var = tk.StringVar()
        type_combo = ttk.Combobox(input_grid, textvariable=self.material_type_var, width=15)
        type_combo['values'] = [t.name for t in MaterialType]
        type_combo.grid(row=0, column=3, sticky=tk.W + tk.E, padx=5, pady=5)
        type_combo.current(0)  # Default to first type

        ttk.Label(input_grid, text="Quantity:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_quantity_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(input_grid, from_=0, to=1000, increment=0.1, textvariable=self.material_quantity_var,
                    width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(input_grid, text="Unit:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.material_unit_var = tk.StringVar(value="sq ft")
        unit_combo = ttk.Combobox(input_grid, textvariable=self.material_unit_var, width=15)
        unit_combo['values'] = ("sq ft", "sq m", "linear ft", "piece", "oz", "g")
        unit_combo.grid(row=1, column=3, sticky=tk.W + tk.E, padx=5, pady=5)

        ttk.Label(input_grid, text="Unit Price:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_price_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(input_grid, from_=0, to=10000, increment=0.5, textvariable=self.material_price_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(input_grid, text="Currency:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.currency_var = tk.StringVar(value="$")
        currency_combo = ttk.Combobox(input_grid, textvariable=self.currency_var, width=5)
        currency_combo['values'] = ("$", "€", "£", "¥")
        currency_combo.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(input_grid, text="Waste %:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_waste_var = tk.DoubleVar(value=15.0)  # Default 15% waste
        ttk.Spinbox(input_grid, from_=0, to=100, increment=1, textvariable=self.material_waste_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Add button
        ttk.Button(input_grid, text="Add Material", command=self._add_material).grid(
            row=4, column=0, columnspan=4, pady=10)

        # Configure the grid
        for i in range(4):
            input_grid.columnconfigure(i, weight=1)

        # Materials list
        list_frame = ttk.LabelFrame(frame, text="Materials List")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("name", "type", "quantity", "unit", "price", "waste", "total")
        self.materials_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Define headings
        self.materials_tree.heading("name", text="Name")
        self.materials_tree.heading("type", text="Type")
        self.materials_tree.heading("quantity", text="Quantity")
        self.materials_tree.heading("unit", text="Unit")
        self.materials_tree.heading("price", text="Unit Price")
        self.materials_tree.heading("waste", text="Waste %")
        self.materials_tree.heading("total", text="Total")

        # Define columns
        self.materials_tree.column("name", width=150, anchor=tk.W)
        self.materials_tree.column("type", width=100, anchor=tk.W)
        self.materials_tree.column("quantity", width=70, anchor=tk.CENTER)
        self.materials_tree.column("unit", width=70, anchor=tk.CENTER)
        self.materials_tree.column("price", width=80, anchor=tk.E)
        self.materials_tree.column("waste", width=70, anchor=tk.CENTER)
        self.materials_tree.column("total", width=80, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to remove
        self.materials_tree.bind("<Double-1>", lambda e: self._remove_selected_material())

        # Buttons for material list
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="Remove Selected", command=self._remove_selected_material).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear All", command=self._clear_materials).pack(side=tk.LEFT, padx=5)

        # Material totals
        totals_frame = ttk.Frame(list_frame)
        totals_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(totals_frame, text="Total Material Cost:").pack(side=tk.LEFT, padx=5)
        self.total_materials_var = tk.StringVar(value="$0.00")
        ttk.Label(totals_frame, textvariable=self.total_materials_var, font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.LEFT, padx=5)

    def _create_labor_tab(self, parent):
        """
        Create the labor and overhead tab.

        Args:
            parent: Parent widget for the tab
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Labor section
        labor_frame = ttk.LabelFrame(frame, text="Labor")
        labor_frame.pack(fill=tk.X, pady=(0, 10))

        labor_grid = ttk.Frame(labor_frame)
        labor_grid.pack(fill=tk.X, padx=10, pady=10)

        # Labor hours
        ttk.Label(labor_grid, text="Estimated Hours:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.labor_hours_var = tk.DoubleVar(value=self.project_data.get("labor_hours", 0.0))
        ttk.Spinbox(labor_grid, from_=0, to=1000, increment=0.5, textvariable=self.labor_hours_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Labor rate
        ttk.Label(labor_grid, text="Hourly Rate:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.labor_rate_var = tk.DoubleVar(value=self.project_data.get("labor_rate", 15.0))
        ttk.Spinbox(labor_grid, from_=0, to=1000, increment=0.5, textvariable=self.labor_rate_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(labor_grid, text=self.currency_var.get() + "/hour").grid(row=1, column=2, sticky=tk.W)

        # Calculate labor cost button
        ttk.Button(labor_grid, text="Calculate Labor Cost", command=self._calculate_labor_cost).grid(
            row=2, column=0, columnspan=3, pady=10)

        # Labor cost result
        ttk.Label(labor_grid, text="Total Labor Cost:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_labor_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(labor_grid, textvariable=self.total_labor_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Configure the grid
        labor_grid.columnconfigure(1, weight=1)

        # Overhead section
        overhead_frame = ttk.LabelFrame(frame, text="Overhead & Profit")
        overhead_frame.pack(fill=tk.X, pady=(0, 10))

        overhead_grid = ttk.Frame(overhead_frame)
        overhead_grid.pack(fill=tk.X, padx=10, pady=10)

        # Overhead percentage
        ttk.Label(overhead_grid, text="Overhead Percentage:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.overhead_pct_var = tk.DoubleVar(value=self.project_data.get("overhead_percentage", 15.0))
        ttk.Spinbox(overhead_grid, from_=0, to=100, increment=1, textvariable=self.overhead_pct_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(overhead_grid, text="%").grid(row=0, column=2, sticky=tk.W)

        # Profit margin
        ttk.Label(overhead_grid, text="Profit Margin:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.profit_margin_var = tk.DoubleVar(value=self.project_data.get("profit_margin", 30.0))
        ttk.Spinbox(overhead_grid, from_=0, to=100, increment=1, textvariable=self.profit_margin_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(overhead_grid, text="%").grid(row=1, column=2, sticky=tk.W)

        # Configure the grid
        overhead_grid.columnconfigure(1, weight=1)

        # Tools section
        tools_frame = ttk.LabelFrame(frame, text="Tools & Equipment")
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tools_grid = ttk.Frame(tools_frame)
        tools_grid.pack(fill=tk.X, padx=10, pady=10)

        # Tool name
        ttk.Label(tools_grid, text="Tool Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.tool_name_var = tk.StringVar()
        ttk.Entry(tools_grid, textvariable=self.tool_name_var, width=20).grid(
            row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        # Tool cost
        ttk.Label(tools_grid, text="Cost:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.tool_cost_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(tools_grid, from_=0, to=10000, increment=0.5, textvariable=self.tool_cost_var, width=10).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Tool usage
        ttk.Label(tools_grid, text="Usage %:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.tool_usage_var = tk.DoubleVar(value=100.0)  # Default to 100% usage
        ttk.Spinbox(tools_grid, from_=1, to=100, increment=1, textvariable=self.tool_usage_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(tools_grid, text="(% of cost to allocate to this project)").grid(
            row=1, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Add tool button
        ttk.Button(tools_grid, text="Add Tool", command=self._add_tool).grid(
            row=2, column=0, columnspan=4, pady=10)

        # Configure the grid
        for i in range(4):
            tools_grid.columnconfigure(i, weight=1)

        # Tool list
        list_frame = ttk.Frame(tools_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview with scrollbar
        columns = ("name", "cost", "usage", "allocated")
        self.tools_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5)

        # Define headings
        self.tools_tree.heading("name", text="Tool Name")
        self.tools_tree.heading("cost", text="Total Cost")
        self.tools_tree.heading("usage", text="Usage %")
        self.tools_tree.heading("allocated", text="Allocated Cost")

        # Define columns
        self.tools_tree.column("name", width=200, anchor=tk.W)
        self.tools_tree.column("cost", width=100, anchor=tk.E)
        self.tools_tree.column("usage", width=70, anchor=tk.CENTER)
        self.tools_tree.column("allocated", width=100, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tools_tree.yview)
        self.tools_tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.tools_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to remove
        self.tools_tree.bind("<Double-1>", lambda e: self._remove_selected_tool())

        # Buttons for tool list
        button_frame = ttk.Frame(tools_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="Remove Selected", command=self._remove_selected_tool).pack(side=tk.LEFT)

        # Tools total
        ttk.Label(button_frame, text="Total Tool Cost:").pack(side=tk.LEFT, padx=(20, 5))
        self.total_tools_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(button_frame, textvariable=self.total_tools_var, font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.LEFT, padx=5)

        # Calculate button for all costs
        calculate_frame = ttk.Frame(frame)
        calculate_frame.pack(fill=tk.X, pady=10)
        ttk.Button(calculate_frame, text="Calculate All Costs", command=self._calculate_costs).pack(pady=10)

    def _create_summary_tab(self, parent):
        """
        Create the cost summary tab.

        Args:
            parent: Parent widget for the tab
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Cost breakdown
        breakdown_frame = ttk.LabelFrame(frame, text="Cost Breakdown")
        breakdown_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        breakdown_grid = ttk.Frame(breakdown_frame)
        breakdown_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the grid with cost items
        ttk.Label(breakdown_grid, text="Materials Cost:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_materials_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_materials_var).grid(
            row=0, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Label(breakdown_grid, text="Labor Cost:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_labor_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_labor_var).grid(
            row=1, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Label(breakdown_grid, text="Tool Cost:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_tools_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_tools_var).grid(
            row=2, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Label(breakdown_grid, text="Overhead:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_overhead_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_overhead_var).grid(
            row=3, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Separator(breakdown_grid, orient=tk.HORIZONTAL).grid(
            row=4, column=0, columnspan=2, sticky=tk.EW, pady=5)

        ttk.Label(breakdown_grid, text="Total Cost:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_total_cost_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_total_cost_var, font=("TkDefaultFont", 11, "bold")).grid(
            row=5, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Label(breakdown_grid, text="Profit:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_profit_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_profit_var).grid(
            row=6, column=1, sticky=tk.E, padx=5, pady=5)

        ttk.Separator(breakdown_grid, orient=tk.HORIZONTAL).grid(
            row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)

        ttk.Label(breakdown_grid, text="Suggested Price:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.summary_price_var = tk.StringVar(value=f"{self.currency_var.get()}0.00")
        ttk.Label(breakdown_grid, textvariable=self.summary_price_var,
                  font=("TkDefaultFont", 14, "bold")).grid(
            row=8, column=1, sticky=tk.E, padx=5, pady=5)

        # Configure the grid
        breakdown_grid.columnconfigure(0, weight=1)
        breakdown_grid.columnconfigure(1, weight=1)

        # Pricing options
        pricing_frame = ttk.LabelFrame(frame, text="Pricing Options")
        pricing_frame.pack(fill=tk.X, pady=(0, 10))

        pricing_grid = ttk.Frame(pricing_frame)
        pricing_grid.pack(fill=tk.X, padx=10, pady=10)

        # Add price rounding
        ttk.Label(pricing_grid, text="Price Rounding:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.rounding_var = tk.StringVar(value="No rounding")
        rounding_combo = ttk.Combobox(pricing_grid, textvariable=self.rounding_var, width=20)
        rounding_combo['values'] = (
            "No rounding",
            "Round to nearest dollar",
            "Round to nearest 5 dollars",
            "Round to nearest 10 dollars"
        )
        rounding_combo.grid(row=0, column=1, sticky=tk.W + tk.E, padx=5, pady=5)

        # Price adjustments
        ttk.Label(pricing_grid, text="Manual Price Adjustment:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.adjustment_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(pricing_grid, from_=-1000, to=1000, increment=5, textvariable=self.adjustment_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(pricing_grid, text="Apply Adjustment", command=self._apply_price_adjustment).grid(
            row=2, column=0, columnspan=2, pady=10)

        # Configure the grid
        pricing_grid.columnconfigure(1, weight=1)

        # Pricing recommendations
        recommend_frame = ttk.LabelFrame(frame, text="Pricing Recommendations")
        recommend_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.recommend_text = tk.Text(recommend_frame, height=6, wrap=tk.WORD)
        self.recommend_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Set initial recommendation text
        default_recommend = (
            "Calculate project costs to see pricing recommendations. "
            "The analysis will suggest pricing based on your costs, overhead, and profit margin."
        )
        self.recommend_text.insert("1.0", default_recommend)
        self.recommend_text.config(state=tk.DISABLED)  # Make read-only

        # Action buttons
        action_frame = ttk.Frame(frame)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Save Analysis", command=self._save_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Export Analysis", command=self._export_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Reset Form", command=self._reset_form).pack(side=tk.LEFT, padx=5)

    def _add_material(self):
        """Add a material to the project."""
        try:
            # Get values from form
            name = self.material_name_var.get()
            if not name:
                messagebox.showwarning("Input Error", "Please enter a material name.")
                return

            material_type = self.material_type_var.get()
            quantity = self.material_quantity_var.get()
            unit = self.material_unit_var.get()
            price = self.material_price_var.get()
            waste = self.material_waste_var.get()
            currency = self.currency_var.get()

            # Calculate total cost including waste
            total = price * quantity * (1 + waste / 100)

            # Add to tree
            self.materials_tree.insert("", tk.END, values=(
                name,
                material_type,
                f"{quantity:.2f}",
                unit,
                f"{currency}{price:.2f}",
                f"{waste:.1f}%",
                f"{currency}{total:.2f}"
            ))

            # Add to data model
            self.project_data["materials"].append({
                "name": name,
                "type": material_type,
                "quantity": quantity,
                "unit": unit,
                "price": price,
                "waste": waste,
                "total": total
            })

            # Update total
            self._update_material_total()

            # Clear form fields
            self.material_name_var.set("")
            self.material_quantity_var.set(1.0)
            self.material_price_var.set(0.0)

            # Show confirmation
            self.set_status(f"Added material: {name}")

        except Exception as e:
            logging.error(f"Error adding material: {str(e)}")
            messagebox.showerror("Error", f"Failed to add material: {str(e)}")

    def _remove_selected_material(self):
        """Remove selected material from the list."""
        selected = self.materials_tree.selection()
        if not selected:
            return

        # Get the index from tree
        idx = self.materials_tree.index(selected[0])

        # Remove from data model
        if 0 <= idx < len(self.project_data["materials"]):
            material = self.project_data["materials"].pop(idx)
            # Remove from tree
            self.materials_tree.delete(selected[0])
            # Update total
            self._update_material_total()
            self.set_status(f"Removed material: {material['name']}")

    def _clear_materials(self):
        """Clear all materials from the list."""
        if not self.project_data["materials"]:
            return

        confirm = messagebox.askyesno("Confirm", "Clear all materials from the list?")
        if not confirm:
            return

        # Clear data model
        self.project_data["materials"] = []

        # Clear tree
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Update total
        self._update_material_total()
        self.set_status("All materials cleared")

    def _update_material_total(self):
        """Update the total material cost."""
        total = sum(m["total"] for m in self.project_data["materials"])
        self.project_data["total_material_cost"] = total
        self.total_materials_var.set(f"{self.currency_var.get()}{total:.2f}")

    def _add_tool(self):
        """Add a tool to the project."""
        try:
            # Get values from form
            name = self.tool_name_var.get()
            if not name:
                messagebox.showwarning("Input Error", "Please enter a tool name.")
                return

            cost = self.tool_cost_var.get()
            usage = self.tool_usage_var.get()
            currency = self.currency_var.get()

            # Calculate allocated cost
            allocated = cost * (usage / 100)

            # Add to tree
            self.tools_tree.insert("", tk.END, values=(
                name,
                f"{currency}{cost:.2f}",
                f"{usage:.1f}%",
                f"{currency}{allocated:.2f}"
            ))

            # Add to data model
            self.project_data["tools"].append({
                "name": name,
                "cost": cost,
                "usage": usage,
                "allocated": allocated
            })

            # Update total
            self._update_tool_total()

            # Clear form fields
            self.tool_name_var.set("")
            self.tool_cost_var.set(0.0)

            # Show confirmation
            self.set_status(f"Added tool: {name}")

        except Exception as e:
            logging.error(f"Error adding tool: {str(e)}")
            messagebox.showerror("Error", f"Failed to add tool: {str(e)}")

    def _remove_selected_tool(self):
        """Remove selected tool from the list."""
        selected = self.tools_tree.selection()
        if not selected:
            return

        # Get the index from tree
        idx = self.tools_tree.index(selected[0])

        # Remove from data model
        if 0 <= idx < len(self.project_data["tools"]):
            tool = self.project_data["tools"].pop(idx)
            # Remove from tree
            self.tools_tree.delete(selected[0])
            # Update total
            self._update_tool_total()
            self.set_status(f"Removed tool: {tool['name']}")

    def _update_tool_total(self):
        """Update the total tool cost."""
        total = sum(t["allocated"] for t in self.project_data["tools"])
        self.project_data["total_tools_cost"] = total
        self.total_tools_var.set(f"{self.currency_var.get()}{total:.2f}")

    def _calculate_labor_cost(self):
        """Calculate the labor cost."""
        try:
            hours = self.labor_hours_var.get()
            rate = self.labor_rate_var.get()

            # Apply complexity factor to hours
            complexity = self.complexity_var.get()
            adjusted_hours = hours * complexity

            # Calculate total labor cost
            total = adjusted_hours * rate

            # Update data model
            self.project_data["labor_hours"] = hours
            self.project_data["labor_rate"] = rate
            self.project_data["complexity_factor"] = complexity
            self.project_data["total_labor_cost"] = total

            # Update display
            self.total_labor_var.set(f"{self.currency_var.get()}{total:.2f}")

            # Show confirmation with adjusted hours if complexity applied
            if complexity != 1.0:
                self.set_status(
                    f"Labor cost calculated: {hours} hours * {complexity:.2f} complexity = {adjusted_hours:.2f} adjusted hours")
            else:
                self.set_status(f"Labor cost calculated: {hours} hours at {self.currency_var.get()}{rate}/hour")

        except Exception as e:
            logging.error(f"Error calculating labor cost: {str(e)}")
            messagebox.showerror("Error", f"Failed to calculate labor cost: {str(e)}")

    def _calculate_costs(self):
        """Calculate all costs and pricing."""
        try:
            # First, make sure labor is calculated
            self._calculate_labor_cost()

            # Get all cost components
            materials_cost = self.project_data["total_material_cost"]
            labor_cost = self.project_data["total_labor_cost"]
            tool_cost = sum(t["allocated"] for t in self.project_data["tools"])

            # Calculate overhead
            overhead_pct = self.overhead_pct_var.get() / 100
            overhead = (materials_cost + labor_cost + tool_cost) * overhead_pct

            # Total cost
            total_cost = materials_cost + labor_cost + tool_cost + overhead

            # Calculate profit
            profit_pct = self.profit_margin_var.get() / 100
            profit = total_cost * profit_pct

            # Suggested price
            suggested_price = total_cost + profit

            # Update data model
            self.project_data["overhead_percentage"] = self.overhead_pct_var.get()
            self.project_data["profit_margin"] = self.profit_margin_var.get()
            self.project_data["total_overhead"] = overhead
            self.project_data["total_cost"] = total_cost
            self.project_data["profit"] = profit
            self.project_data["suggested_price"] = suggested_price

            # Apply rounding if selected
            rounded_price = suggested_price
            if self.rounding_var.get() == "Round to nearest dollar":
                rounded_price = round(suggested_price)
            elif self.rounding_var.get() == "Round to nearest 5 dollars":
                rounded_price = round(suggested_price / 5) * 5
            elif self.rounding_var.get() == "Round to nearest 10 dollars":
                rounded_price = round(suggested_price / 10) * 10

            # Update summary view
            currency = self.currency_var.get()
            self.summary_materials_var.set(f"{currency}{materials_cost:.2f}")
            self.summary_labor_var.set(f"{currency}{labor_cost:.2f}")
            self.summary_tools_var.set(f"{currency}{tool_cost:.2f}")
            self.summary_overhead_var.set(f"{currency}{overhead:.2f}")
            self.summary_total_cost_var.set(f"{currency}{total_cost:.2f}")
            self.summary_profit_var.set(f"{currency}{profit:.2f}")
            self.summary_price_var.set(f"{currency}{rounded_price:.2f}")

            # Create pricing recommendations
            self._update_price_recommendations(total_cost, profit_pct, rounded_price)

            # Show confirmation
            self.set_status(f"Costs calculated. Suggested price: {currency}{rounded_price:.2f}")

            # Switch to the summary tab
            self.notebook.select(3)  # Select the summary tab (index 3)

        except Exception as e:
            logging.error(f"Error calculating costs: {str(e)}")
            messagebox.showerror("Error", f"Failed to calculate costs: {str(e)}")

    def _update_price_recommendations(self, total_cost, profit_pct, suggested_price):
        """
        Update the price recommendations text.

        Args:
            total_cost: Total project cost
            profit_pct: Profit percentage (as decimal)
            suggested_price: Calculated suggested price
        """
        try:
            currency = self.currency_var.get()
            project_type = self.type_var.get()
            skill_level = self.skill_var.get()

            # Calculate alternative pricing options
            minimum_price = total_cost * 1.1  # Minimum of 10% profit
            premium_price = total_cost * 1.5  # 50% margin for premium pricing

            # Create recommendation text
            recommendations = [
                f"Pricing Recommendations for {self.name_var.get() or 'This Project'}",
                f"{'=' * 60}",
                f"",
                f"Base Cost: {currency}{total_cost:.2f}",
                f"Suggested Retail Price: {currency}{suggested_price:.2f} (including {profit_pct * 100:.1f}% profit margin)",
                f"",
                f"Pricing Options:",
                f"  • Minimum Viable Price: {currency}{minimum_price:.2f}",
                f"  • Standard Price: {currency}{suggested_price:.2f}",
                f"  • Premium Price: {currency}{premium_price:.2f}",
                f"",
                f"Recommendations:"
            ]

            # Add specific recommendations based on project type and skill level
            if skill_level in ["BEGINNER", "INTERMEDIATE"]:
                recommendations.append(
                    f"  • For a {skill_level.lower()} project, consider pricing at the standard level")
                recommendations.append(f"    to remain competitive while ensuring adequate profit.")
            elif skill_level in ["ADVANCED", "EXPERT"]:
                recommendations.append(f"  • For an {skill_level.lower()} project, consider premium pricing to")
                recommendations.append(f"    reflect the craftsmanship and expertise required.")

            if project_type in ["WALLET", "BELT"]:
                recommendations.append(f"  • {project_type.title()} projects have strong market competition.")
                recommendations.append(f"    Focus on unique features to justify pricing above market average.")
            elif project_type in ["BAG", "CUSTOM"]:
                recommendations.append(f"  • {project_type.title()} projects allow for higher margins due to")
                recommendations.append(f"    their custom nature and perceived value.")

            # General advice
            recommendations.extend([
                f"",
                f"Remember to consider:",
                f"  • Market competition and customer price sensitivity",
                f"  • The value of your time and expertise",
                f"  • Uniqueness of the design and materials",
                f"  • Target customer's willingness to pay",
                f""
            ])

            # Update the text widget
            self.recommend_text.config(state=tk.NORMAL)
            self.recommend_text.delete("1.0", tk.END)
            self.recommend_text.insert("1.0", "\n".join(recommendations))
            self.recommend_text.config(state=tk.DISABLED)

        except Exception as e:
            logging.error(f"Error updating price recommendations: {str(e)}")

    def _apply_price_adjustment(self):
        """Apply a manual price adjustment."""
        try:
            adjustment = self.adjustment_var.get()
            current_price = float(self.summary_price_var.get().replace(self.currency_var.get(), ""))

            new_price = current_price + adjustment
            if new_price <= 0:
                messagebox.showwarning("Invalid Adjustment", "Adjusted price must be greater than zero.")
                return

            # Update the display
            self.summary_price_var.set(f"{self.currency_var.get()}{new_price:.2f}")

            # Show confirmation
            if adjustment > 0:
                self.set_status(f"Price increased by {self.currency_var.get()}{adjustment:.2f}")
            else:
                self.set_status(f"Price decreased by {self.currency_var.get()}{abs(adjustment):.2f}")

        except Exception as e:
            logging.error(f"Error applying price adjustment: {str(e)}")
            messagebox.showerror("Error", f"Failed to apply price adjustment: {str(e)}")

    def _save_analysis(self):
        """Save the current analysis to the application storage."""
        try:
            # Update project data from form fields
            self.project_data["name"] = self.name_var.get()
            self.project_data["type"] = self.type_var.get()
            self.project_data["skill_level"] = self.skill_var.get()
            self.project_data["description"] = self.description_text.get("1.0", tk.END).strip()
            self.project_data["width"] = self.width_var.get()
            self.project_data["height"] = self.height_var.get()
            self.project_data["depth"] = self.depth_var.get()
            self.project_data["notes"] = self.notes_text.get("1.0", tk.END).strip()
            self.project_data["complexity_factor"] = self.complexity_var.get()

            # In a full implementation, we would save to a database or file
            # For now, just show a confirmation
            messagebox.showinfo("Save Analysis",
                                f"Analysis for '{self.project_data['name']}' saved successfully.")

            self.set_status(f"Analysis saved: {self.project_data['name']}")

        except Exception as e:
            logging.error(f"Error saving analysis: {str(e)}")
            messagebox.showerror("Error", f"Failed to save analysis: {str(e)}")

    def _export_analysis(self):
        """Export the cost analysis to a file."""
        try:
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
                title="Export Cost Analysis"
            )

            if not file_path:
                return

            # Update project data from form fields
            self.project_data["name"] = self.name_var.get()
            self.project_data["type"] = self.type_var.get()
            self.project_data["skill_level"] = self.skill_var.get()
            self.project_data["description"] = self.description_text.get("1.0", tk.END).strip()

            # Export format depends on file extension
            if file_path.endswith(".json"):
                # Export as JSON
                with open(file_path, "w") as f:
                    json.dump(self.project_data, f, indent=2)
            else:
                # Export as text
                with open(file_path, "w") as f:
                    # Create report content
                    lines = [f"Cost Analysis for {self.project_data['name']}", "=" * 50, ""]

                    # Project details
                    lines.append("PROJECT DETAILS")
                    lines.append("-" * 20)
                    lines.append(f"Name: {self.project_data['name']}")
                    lines.append(f"Type: {self.project_data['type']}")
                    lines.append(f"Skill Level: {self.project_data['skill_level']}")

                    if self.project_data['description']:
                        lines.append(f"\nDescription: {self.project_data['description']}")

                    lines.append("")

                    # Materials
                    lines.append("MATERIALS")
                    lines.append("-" * 20)
                    if self.project_data["materials"]:
                        for mat in self.project_data["materials"]:
                            lines.append(f"{mat['name']} ({mat['type']})")
                            lines.append(
                                f"  {mat['quantity']} {mat['unit']} @ {self.currency_var.get()}{mat['price']:.2f}")
                            lines.append(f"  Waste: {mat['waste']:.1f}%")
                            lines.append(f"  Total: {self.currency_var.get()}{mat['total']:.2f}")
                            lines.append("")
                    else:
                        lines.append("No materials specified.")
                        lines.append("")

                    # Labor
                    lines.append("LABOR")
                    lines.append("-" * 20)
                    lines.append(f"Hours: {self.project_data['labor_hours']:.1f}")
                    lines.append(f"Rate: {self.currency_var.get()}{self.project_data['labor_rate']:.2f}/hour")
                    lines.append(f"Complexity Factor: {self.project_data.get('complexity_factor', 1.0):.2f}")
                    lines.append(
                        f"Total Labor Cost: {self.currency_var.get()}{self.project_data['total_labor_cost']:.2f}")
                    lines.append("")

                    # Tools
                    lines.append("TOOLS & EQUIPMENT")
                    lines.append("-" * 20)
                    if self.project_data["tools"]:
                        for tool in self.project_data["tools"]:
                            lines.append(f"{tool['name']}")
                            lines.append(f"  Cost: {self.currency_var.get()}{tool['cost']:.2f}")
                            lines.append(f"  Usage: {tool['usage']:.1f}%")
                            lines.append(f"  Allocated: {self.currency_var.get()}{tool['allocated']:.2f}")
                            lines.append("")
                    else:
                        lines.append("No tools specified.")
                        lines.append("")

                    # Cost Summary
                    lines.append("COST SUMMARY")
                    lines.append("-" * 20)
                    lines.append(f"Materials: {self.currency_var.get()}{self.project_data['total_material_cost']:.2f}")
                    lines.append(f"Labor: {self.currency_var.get()}{self.project_data['total_labor_cost']:.2f}")
                    tools_cost = sum(t['allocated'] for t in self.project_data['tools'])
                    lines.append(f"Tools: {self.currency_var.get()}{tools_cost:.2f}")
                    lines.append(
                        f"Overhead ({self.project_data['overhead_percentage']:.1f}%): {self.currency_var.get()}{self.project_data['total_overhead']:.2f}")
                    lines.append(f"Total Cost: {self.currency_var.get()}{self.project_data['total_cost']:.2f}")
                    lines.append("")

                    # Pricing
                    lines.append("PRICING")
                    lines.append("-" * 20)
                    lines.append(f"Profit Margin: {self.project_data['profit_margin']:.1f}%")
                    lines.append(
                        f"Suggested Price: {self.currency_var.get()}{self.project_data['suggested_price']:.2f}")
                    lines.append("")

                    # Notes
                    if self.project_data.get('notes'):
                        lines.append("NOTES")
                        lines.append("-" * 20)
                        lines.append(self.project_data['notes'])
                        lines.append("")

                    # Write to file
                    f.write("\n".join(lines))

            self.set_status(f"Analysis exported to {file_path}")
            messagebox.showinfo("Export Successful", f"Cost analysis exported to {file_path}")

        except Exception as e:
            logging.error(f"Error exporting analysis: {str(e)}")
            messagebox.showerror("Error", f"Failed to export analysis: {str(e)}")

    def _load_initial_data(self):
        """Load initial sample data for the analyzer."""
        # If project data already has content, don't overwrite
        if self.project_data.get("name") or len(self.project_data.get("materials", [])) > 0:
            return

        # Set initial project data
        self.name_var.set("Leather Wallet")
        self.type_var.set("WALLET")
        self.skill_var.set("INTERMEDIATE")
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", "Bifold wallet with card slots and cash pocket.")

        # Set dimensions
        self.width_var.set(22.0)
        self.height_var.set(9.0)
        self.depth_var.set(1.5)

        # Add sample materials
        sample_materials = [
            {
                "name": "Veg Tan Leather",
                "type": "LEATHER",
                "quantity": 1.2,
                "unit": "sq ft",
                "price": 10.99,
                "waste": 15.0
            },
            {
                "name": "Thread",
                "type": "THREAD",
                "quantity": 1.0,
                "unit": "piece",
                "price": 5.99,
                "waste": 5.0
            },
            {
                "name": "Edge Paint",
                "type": "OTHER",
                "quantity": 0.1,
                "unit": "oz",
                "price": 12.99,
                "waste": 10.0
            }
        ]

        # Add each material
        for material in sample_materials:
            self.material_name_var.set(material["name"])
            self.material_type_var.set(material["type"])
            self.material_quantity_var.set(material["quantity"])
            self.material_unit_var.set(material["unit"])
            self.material_price_var.set(material["price"])
            self.material_waste_var.set(material["waste"])
            self._add_material()

        # Set labor values
        self.labor_hours_var.set(3.0)
        self.labor_rate_var.set(15.0)

        # Add sample tools
        sample_tools = [
            {
                "name": "Stitching Chisels",
                "cost": 35.0,
                "usage": 5.0
            },
            {
                "name": "Cutting Mat",
                "cost": 25.0,
                "usage": 3.0
            }
        ]

        # Add each tool
        for tool in sample_tools:
            self.tool_name_var.set(tool["name"])
            self.tool_cost_var.set(tool["cost"])
            self.tool_usage_var.set(tool["usage"])
            self._add_tool()

        # Calculate initial values
        self._calculate_costs()

    def _reset_form(self):
        """Reset the form to its initial state."""
        confirm = messagebox.askyesno("Confirm Reset",
                                      "Are you sure you want to reset all data? This cannot be undone.")
        if not confirm:
            return

        # Clear all fields
        self.name_var.set("")
        self.width_var.set(0.0)
        self.height_var.set(0.0)
        self.depth_var.set(0.0)
        self.description_text.delete("1.0", tk.END)
        self.notes_text.delete("1.0", tk.END)
        self.complexity_var.set(1.0)

        # Clear materials
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Clear tools
        for item in self.tools_tree.get_children():
            self.tools_tree.delete(item)

        # Reset labor fields
        self.labor_hours_var.set(0.0)
        self.labor_rate_var.set(15.0)

        # Reset data model
        self.project_data = {
            "name": "",
            "description": "",
            "materials": [],
            "labor_hours": 0.0,
            "labor_rate": 15.0,
            "overhead_percentage": 15.0,
            "profit_margin": 30.0,
            "tools": [],
            "total_material_cost": 0.0,
            "total_labor_cost": 0.0,
            "total_overhead": 0.0,
            "total_cost": 0.0,
            "suggested_price": 0.0
        }

        # Update displays
        self._update_material_total()
        self._update_tool_total()
        self.total_labor_var.set(f"{self.currency_var.get()}0.00")

        # Reset summary values
        self.summary_materials_var.set(f"{self.currency_var.get()}0.00")
        self.summary_labor_var.set(f"{self.currency_var.get()}0.00")
        self.summary_tools_var.set(f"{self.currency_var.get()}0.00")
        self.summary_overhead_var.set(f"{self.currency_var.get()}0.00")
        self.summary_total_cost_var.set(f"{self.currency_var.get()}0.00")
        self.summary_profit_var.set(f"{self.currency_var.get()}0.00")
        self.summary_price_var.set(f"{self.currency_var.get()}0.00")

        # Reset recommendation text
        self.recommend_text.config(state=tk.NORMAL)
        self.recommend_text.delete("1.0", tk.END)
        self.recommend_text.insert("1.0", "Calculate project costs to see pricing recommendations.")
        self.recommend_text.config(state=tk.DISABLED)

        self.set_status("Form reset to initial state")