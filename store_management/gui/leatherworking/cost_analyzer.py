# gui/leatherworking/cost_analyzer.py
"""
Project Cost Analyzer for Leatherworking Projects.

This module provides a comprehensive cost analysis tool for leatherworking projects,
offering detailed insights into project expenses, profitability, and pricing strategies.
"""

import json
import logging
import tkinter as tk
from decimal import Decimal
from typing import Any, Dict, Optional, List

import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import tkinter.filedialog

from di.core import inject
from services.interfaces import (
    get_IProjectService,
    get_IMaterialService,
    ProjectType,
    MaterialType,
)
from utils.circular_import_resolver import lazy_import
from utils.error_handler import ErrorHandler

# Lazy import to avoid circular dependencies
Project = lazy_import('database.models.project', 'Project')

from gui.base_view import BaseView

logger = logging.getLogger(__name__)


class ProjectCostAnalyzer(BaseView):
    """
    Analyze and track costs for leatherworking projects.

    Provides detailed cost breakdowns, profitability analysis,
    and pricing recommendations based on materials and labor.

    Attributes:
        project_service: Service for project-related operations
        material_service: Service for material-related operations
        error_handler: Handles error logging and reporting
        current_project: Currently selected project
        cost_data: Dictionary storing cost breakdown
        labor_rate: Hourly labor rate for cost calculations
    """

    @inject
    def __init__(
            self,
            parent: tk.Widget,
            app: Any,
            project_service: get_IProjectService = None,
            material_service: get_IMaterialService = None
    ) -> None:
        """
        Initialize the project cost analyzer.

        Args:
            parent: Parent widget
            app: Application instance
            project_service: Project service for data retrieval (optional)
            material_service: Material service for cost calculations (optional)
        """
        super().__init__(parent, app)

        self.project_service = project_service
        self.material_service = material_service

        # Error handling
        self.error_handler = ErrorHandler()

        # Project and cost tracking
        self.current_project: Optional[Project] = None
        self.cost_data: Dict[str, Decimal] = {}
        self.labor_rate = Decimal('25.00')

        # UI Setup
        self.setup_ui()
        self.load_settings()

    def setup_ui(self) -> None:
        """
        Create and configure the UI components for the cost analyzer.

        Sets up toolbar, project list, and cost analysis sections.
        """
        try:
            # Main layout
            self.toolbar = ttk.Frame(self)
            self.toolbar.pack(fill=tk.X, padx=5, pady=5)

            self.content = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            self.content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Create UI sections
            self.create_toolbar()
            self.create_project_section()
            self.create_cost_section()

            # Status bar
            self.status_var = tk.StringVar()
            ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, pady=(5, 0))

        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            messagebox.showerror("UI Setup Error", str(e))

    def create_toolbar(self) -> None:
        """
        Create toolbar controls for project type filtering and labor rate adjustment.
        """
        try:
            # Project Type Selector
            ttk.Label(self.toolbar, text='Project Type:').pack(side=tk.LEFT, padx=5)
            self.type_var = tk.StringVar(value='ALL')
            project_types = ['ALL'] + [t.name for t in ProjectType]
            type_combo = ttk.Combobox(
                self.toolbar,
                textvariable=self.type_var,
                values=project_types,
                state='readonly',
                width=15
            )
            type_combo.pack(side=tk.LEFT, padx=5)
            type_combo.bind('<<ComboboxSelected>>', lambda _: self.load_projects())

            # Labor Rate Input
            ttk.Label(self.toolbar, text='Labor Rate ($/hr):').pack(side=tk.LEFT, padx=5)
            self.labor_var = tk.StringVar(value=str(self.labor_rate))
            labor_entry = ttk.Entry(self.toolbar, textvariable=self.labor_var, width=8)
            labor_entry.pack(side=tk.LEFT)
            labor_entry.bind('<FocusOut>', self.update_labor_rate)

            # Toolbar Buttons
            ttk.Button(self.toolbar, text='Settings', command=self.show_settings_dialog).pack(side=tk.RIGHT, padx=5)
            ttk.Button(self.toolbar, text='Export Analysis', command=self.export_analysis).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            logger.error(f"Error creating toolbar: {e}")
            messagebox.showerror("Toolbar Error", str(e))

    def show_settings_dialog(self) -> None:
        """
        Display a dialog for additional project cost analyzer settings.
        """
        # Placeholder for future settings dialog implementation
        messagebox.showinfo("Settings", "Settings dialog not yet implemented")

    def export_analysis(self) -> None:
        """
        Export the current project's cost analysis to a file.
        """
        if not self.current_project or not self.cost_data:
            messagebox.showwarning("Export Error", "No project selected for export")
            return

        try:
            # TODO: Implement comprehensive export functionality
            export_data = {
                'project_name': self.current_project.name,
                'cost_breakdown': {k: float(v) for k, v in self.cost_data.items()}
            }

            # Prompt user for file save location
            file_path = tkinter.filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=4)
                messagebox.showinfo("Export Successful", f"Analysis exported to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting analysis: {e}")
            messagebox.showerror("Export Error", str(e))

    def create_project_section(self) -> None:
        """Create the project list section."""
        frame = ttk.LabelFrame(self.content, text='Projects')
        self.content.add(frame, weight=1)
        columns = 'name', 'type', 'status', 'materials_cost', 'total_cost'
        self.project_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        headings = {'name': 'Project Name', 'type': 'Type', 'status': 'Status',
                    'materials_cost': 'Materials Cost', 'total_cost': 'Total Cost'}
        for col, heading in headings.items():
            self.project_tree.heading(col, text=heading)
            self.project_tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar.set)
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.project_tree.bind('<<TreeviewSelect>>', self.on_project_select)

    def create_cost_section(self) -> None:
        """Create the cost analysis section."""
        frame = ttk.LabelFrame(self.content, text='Cost Analysis')
        self.content.add(frame, weight=1)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        breakdown_frame = ttk.Frame(notebook)
        notebook.add(breakdown_frame, text='Cost Breakdown')
        self.create_cost_breakdown(breakdown_frame)
        profit_frame = ttk.Frame(notebook)
        notebook.add(profit_frame, text='Profitability')
        self.create_profitability_analysis(profit_frame)
        pricing_frame = ttk.Frame(notebook)
        notebook.add(pricing_frame, text='Pricing')
        self.create_pricing_recommendations(pricing_frame)

    def create_cost_breakdown(self, parent: ttk.Frame) -> None:
        """
        Create the cost breakdown display.

        Args:
            parent: Parent frame
        """
        sections = [('Materials', 'materials_frame'), ('Labor', 'labor_frame'),
                    ('Hardware', 'hardware_frame'), ('Overhead', 'overhead_frame')]
        self.cost_frames = {}
        for title, frame_name in sections:
            frame = ttk.LabelFrame(parent, text=title)
            frame.pack(fill=tk.X, padx=5, pady=5)
            self.cost_frames[frame_name] = frame
        total_frame = ttk.Frame(parent)
        total_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Label(total_frame, text='Total Cost:', font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT)
        self.total_var = tk.StringVar()
        ttk.Label(total_frame, textvariable=self.total_var, font=('TkDefaultFont', 12, 'bold')).pack(side=tk.LEFT, padx=5)

    def create_profitability_analysis(self, parent: ttk.Frame) -> None:
        """
        Create the profitability analysis display.

        Args:
            parent: Parent frame
        """
        metrics_frame = ttk.Frame(parent)
        metrics_frame.pack(fill=tk.X, pady=5)
        self.profit_vars = {}
        row = 0
        col = 0
        metrics = [('Target Price', 'target_price'), ('Actual Cost', 'actual_cost'),
                   ('Gross Profit', 'gross_profit'), ('Profit Margin', 'profit_margin'),
                   ('Break-Even Point', 'break_even'), ('ROI', 'roi')]
        for label, var_name in metrics:
            metric_frame = ttk.Frame(metrics_frame)
            metric_frame.grid(row=row, column=col, padx=5, pady=2, sticky='nsew')
            ttk.Label(metric_frame, text=label + ':', font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
            var = tk.StringVar()
            self.profit_vars[var_name] = var
            ttk.Label(metric_frame, textvariable=var, font=('TkDefaultFont', 12)).pack(anchor=tk.W)
            col += 1
            if col > 2:
                col = 0
                row += 1
        for i in range(3):
            metrics_frame.grid_columnconfigure(i, weight=1)
        margin_frame = ttk.Frame(parent)
        margin_frame.pack(fill=tk.X, pady=10)
        ttk.Label(margin_frame, text='Target Margin (%):').pack(side=tk.LEFT)
        self.margin_var = tk.StringVar(value='40')
        margin_scale = ttk.Scale(margin_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  variable=self.margin_var, command=self.update_profitability)
        margin_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.profit_canvas = tk.Canvas(parent, bg='white', height=200)
        self.profit_canvas.pack(fill=tk.BOTH, expand=True, pady=10)

    def create_pricing_recommendations(self, parent: ttk.Frame) -> None:
        """
        Create the pricing recommendations display.

        Args:
            parent: Parent frame
        """
        points_frame = ttk.LabelFrame(parent, text='Recommended Price Points')
        points_frame.pack(fill=tk.X, padx=5, pady=5)
        self.price_vars = {}
        for label, var_name in [('Economy', 'economy_price'), ('Standard', 'standard_price'),
                                ('Premium', 'premium_price')]:
            frame = ttk.Frame(points_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f'{label}:').pack(side=tk.LEFT)
            var = tk.StringVar()
            self.price_vars[var_name] = var
            ttk.Label(frame, textvariable=var, font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        analysis_frame = ttk.LabelFrame(parent, text='Market Analysis')
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.market_text = tk.Text(analysis_frame, wrap=tk.WORD, height=8, state=tk.DISABLED)
        self.market_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        comp_frame = ttk.LabelFrame(parent, text='Competitor Comparison')
        comp_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.comp_canvas = tk.Canvas(comp_frame, bg='white', height=150)
        self.comp_canvas.pack(fill=tk.BOTH, expand=True, pady=5)

    def load_projects(self) -> None:
        """Load and display project list."""
        try:
            project_type = None if self.type_var.get() == 'ALL' else ProjectType[self.type_var.get()]
            projects = self.project_service.search_projects({'project_type': project_type})
            self.project_tree.delete(*self.project_tree.get_children())
            for project in projects:
                materials_cost = self.calculate_materials_cost(project)
                total_cost = self.calculate_total_cost(project)
                values = (project.name, project.project_type.name, project.status.name,
                          f'${materials_cost:.2f}', f'${total_cost:.2f}')
                self.project_tree.insert('', tk.END, values=values, tags=(str(project.id),))
        except Exception as e:
            logger.error(f'Error loading projects: {str(e)}')
            self.status_var.set('Error loading projects')

    def calculate_materials_cost(self, project: Project) -> Decimal:
        """
        Calculate total materials cost for a project.

        Args:
            project: Project to calculate for

        Returns:
            Total materials cost
        """
        total = Decimal('0')
        try:
            for component in project.components:
                if component.material_type == MaterialType.LEATHER:
                    material = self.material_service.get_material(component.material_id)
                    total += material.unit_cost * component.area
                else:
                    material = self.material_service.get_material(component.material_id)
                    total += material.unit_cost * component.quantity
        except Exception as e:
            logger.error(f'Error calculating materials cost: {str(e)}')
        return total

    def calculate_component_cost(self, component: Any) -> Decimal:
        """
        Calculate cost for a specific component.

        Args:
            component: Project component

        Returns:
            Component cost
        """
        try:
            material = self.material_service.get_material(component.material_id)
            if component.material_type == MaterialType.LEATHER:
                return material.unit_cost * component.area
            else:
                return material.unit_cost * component.quantity
        except Exception as e:
            logger.error(f'Error calculating component cost: {str(e)}')
        return Decimal('0')

    def calculate_total_cost(self, project: Project) -> Decimal:
        """
        Calculate total project cost including labor and overhead.

        Args:
            project: Project to calculate for

        Returns:
            Total project cost
        """
        try:
            materials_cost = self.calculate_materials_cost(project)
            labor_hours = project.estimated_hours or Decimal('0')
            labor_cost = labor_hours * self.labor_rate
            base_cost = materials_cost + labor_cost
            overhead_rate = Decimal('0.15')
            overhead_cost = base_cost * overhead_rate
            return materials_cost + labor_cost + overhead_cost
        except Exception as e:
            logger.error(f'Error calculating total cost: {str(e)}')
        return Decimal('0')

    def update_cost_breakdown(self) -> None:
        """Update the cost breakdown display."""
        if not self.current_project:
            return
        try:
            materials_cost = self.calculate_materials_cost(self.current_project)
            labor_hours = self.current_project.estimated_hours or Decimal('0')
            labor_cost = labor_hours * self.labor_rate
            base_cost = materials_cost + labor_cost
            overhead_cost = base_cost * Decimal('0.15')

            materials_frame = self.cost_frames['materials_frame']
            for widget in materials_frame.winfo_children():
                widget.destroy()
            for component in self.current_project.components:
                cost = self.calculate_component_cost(component)
                frame = ttk.Frame(materials_frame)
                frame.pack(fill=tk.X, pady=1)
                ttk.Label(frame, text=component.name).pack(side=tk.LEFT)
                ttk.Label(frame, text=f'${cost:.2f}').pack(side=tk.RIGHT)

            labor_frame = self.cost_frames['labor_frame']
            for widget in labor_frame.winfo_children():
                widget.destroy()
            ttk.Label(labor_frame, text=f'Hours: {labor_hours}').pack(side=tk.LEFT)
            ttk.Label(labor_frame, text=f'Rate: ${self.labor_rate}/hr').pack(side=tk.LEFT, padx=10)
            ttk.Label(labor_frame, text=f'Total: ${labor_cost:.2f}').pack(side=tk.RIGHT)

            overhead_frame = self.cost_frames['overhead_frame']
            for widget in overhead_frame.winfo_children():
                widget.destroy()
            ttk.Label(overhead_frame, text='15% of base cost').pack(side=tk.LEFT)
            ttk.Label(overhead_frame, text=f'${overhead_cost:.2f}').pack(side=tk.RIGHT)

            total_cost = materials_cost + labor_cost + overhead_cost
            self.total_var.set(f'${total_cost:.2f}')
            self.cost_data = {'materials': materials_cost, 'labor': labor_cost, 'overhead': overhead_cost,
                              'total': total_cost}
            self.update_profitability()
            self.update_pricing_recommendations()
        except Exception as e:
            logger.error(f'Error updating cost breakdown: {str(e)}')
            self.status_var.set('Error updating cost breakdown')

    def on_project_select(self, event: Any) -> None:
        """
        Handle project selection in the treeview.

        Args:
            event: Event data
        """
        selection = self.project_tree.selection()
        if not selection:
            return
        try:
            project_id = int(self.project_tree.item(selection[0], 'tags')[0])
            self.current_project = self.project_service.get_project(project_id, include_components=True)
            self.update_cost_breakdown()
        except Exception as e:
            logger.error(f'Error loading project details: {str(e)}')
            self.status_var.set('Error loading project details')

    def cleanup(self) -> None:
        """Perform cleanup before view is destroyed."""
        try:
            self.save_settings()
        except Exception as e:
            logger.error(f'Error during cleanup: {str(e)}')

    def load_settings(self) -> None:
        """Load saved settings."""
        try:
            with open('cost_analyzer_settings.json', 'r') as f:
                settings = json.load(f)
            self.labor_rate = Decimal(str(settings.get('labor_rate', '25.00')))
            self.labor_var.set(str(self.labor_rate))
        except Exception as e:
            logger.error(f'Error loading settings: {str(e)}')

    def save_settings(self) -> None:
        """Save current settings."""
        try:
            settings = {'labor_rate': str(self.labor_rate)}
            with open('cost_analyzer_settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logger.error(f'Error saving settings: {str(e)}')

    def update_labor_rate(self, *args) -> None:
        """Update the labor rate when changed."""
        try:
            new_rate = Decimal(self.labor_var.get())
            if new_rate <= 0:
                raise ValueError('Labor rate must be positive')
            self.labor_rate = new_rate
            self.save_settings()
            if self.current_project:
                self.update_cost_breakdown()
        except ValueError:
            self.labor_var.set(str(self.labor_rate))

    def update_profitability(self, *args) -> None:
        """Update the profitability analysis display."""
        if not self.current_project or not self.cost_data:
            return
        try:
            target_margin = Decimal(self.margin_var.get()) / 100
            total_cost = self.cost_data['total']
            target_price = total_cost / (1 - target_margin)
            gross_profit = target_price - total_cost
            metrics = {
                'target_price': f'${target_price:.2f}',
                'actual_cost': f'${total_cost:.2f}',
                'gross_profit': f'${gross_profit:.2f}',
                'profit_margin': f'{target_margin * 100:.1f}%',
                'break_even': f'{total_cost / target_price * 100:.1f}% of price',
                'roi': f'{gross_profit / total_cost * 100:.1f}%'
            }
            for name, value in metrics.items():
                self.profit_vars[name].set(value)
        except Exception as e:
            logger.error(f'Error updating profitability: {str(e)}')
            self.status_var.set('Error updating profitability analysis')

    def update_pricing_recommendations(self) -> None:
        """Update the pricing recommendations display."""
        if not self.current_project or not self.cost_data:
            return
        try:
            total_cost = self.cost_data['total']
            price_points = {
                'economy_price': total_cost * Decimal('1.5'),
                'standard_price': total_cost * Decimal('2.0'),
                'premium_price': total_cost * Decimal('3.0')
            }
            for name, value in price_points.items():
                self.price_vars[name].set(f'${value:.2f}')

            # TODO: Implement market analysis and competitor comparison
            market_analysis = "Market analysis not yet implemented"
            self.market_text.configure(state=tk.NORMAL)
            self.market_text.delete('1.0', tk.END)
            self.market_text.insert(tk.END, market_analysis)
            self.market_text.configure(state=tk.DISABLED)

        except Exception as e:
            logger.error(f'Error updating pricing: {str(e)}')
            self.status_var.set('Error updating pricing recommendations')

def main():
    """
    Standalone entry point for testing the ProjectCostAnalyzer.
    This function creates a basic Tkinter window and demonstrates
    the ProjectCostAnalyzer view in isolation.
    """
    import tkinter as tk
    from di.container import DependencyContainer
    from services.implementations.project_service import ProjectServiceImpl
    from services.implementations.material_service import MaterialServiceImpl
    from database.models.enums import ProjectType, MaterialType, ProjectStatus

    # Create root window
    root = tk.Tk()
    root.title("Leatherworking Project Cost Analyzer")
    root.geometry("1200x800")

    # Setup dependency container (mock implementation for testing)
    container = DependencyContainer()
    container.register('IProjectService', ProjectServiceImpl())
    container.register('IMaterialService', MaterialServiceImpl())

    # Create the ProjectCostAnalyzer
    cost_analyzer = ProjectCostAnalyzer(root, container)
    cost_analyzer.pack(fill=tk.BOTH, expand=True)

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()