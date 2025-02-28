# gui/leatherworking/cost_analyzer.py
import logging
import tkinter as tk
from tkinter import messagebox as messagebox, ttk
import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

from gui.base_view import BaseView
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel
from services.interfaces.material_service import IMaterialService, MaterialType
from utils.circular_import_resolver import lazy_import
from utils.error_handler import ErrorHandler

# Use lazy imports to avoid circular dependencies
MaterialServiceImpl = lazy_import('services.implementations.material_service.MaterialServiceImpl')
ProjectServiceImpl = lazy_import('services.implementations.project_service.ProjectServiceImpl')

from database.models.enums import MaterialType, ProjectStatus, ProjectType


class ProjectCostAnalyzer(BaseView):
    """
    Cost analysis tool for leatherworking projects.

    Provides functionality to:
    - Calculate material costs for a project
    - Estimate labor costs based on time and skill level
    - Add tools and overhead costs
    - Generate detailed cost breakdowns and pricing recommendations
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the project cost analyzer.

        Args:
            parent: Parent widget
            app: Application instance with dependency container
        """
        super().__init__(parent, app)

        # Initialize state
        self.project_data = {
            "name": "",
            "description": "",
            "materials": [],
            "labor_hours": 0.0,
            "labor_rate": 15.0,  # Default hourly rate
            "overhead_percentage": 15.0,  # Default overhead percentage
            "profit_margin": 30.0,  # Default profit margin
            "tools": [],
            "total_material_cost": 0.0,
            "total_labor_cost": 0.0,
            "total_overhead": 0.0,
            "total_cost": 0.0,
            "suggested_price": 0.0
        }

        self._create_ui()
        self._load_initial_data()

    def _create_ui(self):
        """Create the user interface."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="Project Cost Analyzer",
                  font=("TkDefaultFont", 14, "bold")).pack(side=tk.LEFT)

        # Create notebook for tabbed sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Project Info
        info_frame = ttk.Frame(notebook)
        self._create_project_info_tab(info_frame)
        notebook.add(info_frame, text="Project Info")

        # Tab 2: Materials
        materials_frame = ttk.Frame(notebook)
        self._create_materials_tab(materials_frame)
        notebook.add(materials_frame, text="Materials")

        # Tab 3: Labor & Overhead
        labor_frame = ttk.Frame(notebook)
        self._create_labor_tab(labor_frame)
        notebook.add(labor_frame, text="Labor & Overhead")

        # Tab 4: Summary
        summary_frame = ttk.Frame(notebook)
        self._create_summary_tab(summary_frame)
        notebook.add(summary_frame, text="Cost Summary")

        # Bottom action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(action_frame, text="Calculate", command=self._calculate_costs).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Save", command=self._save_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Export", command=self._export_analysis).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Reset", command=self._reset_form).pack(side=tk.RIGHT)

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
        self.name_var = tk.StringVar(value=self.project_data["name"])
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
        ttk.Label(pricing_grid, text="Price Rounding:").grid(row