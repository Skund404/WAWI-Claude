# Path: gui/leatherworking/project_view.py

from typing import Optional, Dict, List, Any
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from gui.base_view import BaseView
from services.interfaces.project_service import IProjectService
from services.interfaces.material_service import IMaterialService
from services.interfaces.hardware_service import IHardwareService
from database.models.project import ProjectType, ProductionStatus
from database.models.material import MaterialType, LeatherType
from utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class LeatherworkingProjectView(BaseView):
    """
    Specialized view for managing leatherworking projects.
    Handles project creation, tracking, and material management specific to leatherworking.
    """

    def __init__(self, parent: tk.Widget, app: Any) -> None:
        """
        Initialize the leatherworking project view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        # Get required services
        self.project_service = self.get_service(IProjectService)
        self.material_service = self.get_service(IMaterialService)
        self.hardware_service = self.get_service(IHardwareService)

        # Initialize UI components
        self.selected_project_id: Optional[int] = None
        self.current_materials: Dict[int, Dict] = {}
        self.error_handler = ErrorHandler()

        self.setup_ui()
        self.load_data()

    def setup_ui(self) -> None:
        """Create and configure the UI components."""
        # Create main frames
        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=5)

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create toolbar buttons
        self.create_toolbar()

        # Create project list and details sections
        self.create_project_list()
        self.create_project_details()

        # Create material tracking section
        self.create_material_tracking()

    def create_toolbar(self) -> None:
        """Create toolbar buttons and controls."""
        buttons = [
            ("New Project", self.show_new_project_dialog),
            ("Delete Project", self.delete_selected_project),
            ("Export Report", self.export_project_report),
        ]

        for text, command in buttons:
            btn = ttk.Button(self.toolbar_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=2)

        # Add search box
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_projects())
        search_entry = ttk.Entry(self.toolbar_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.RIGHT, padx=5)
        ttk.Label(self.toolbar_frame, text="Search:").pack(side=tk.RIGHT)

    def create_project_list(self) -> None:
        """Create the project list treeview."""
        frame = ttk.Frame(self.content_frame)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("name", "type", "status", "complexity")
        self.project_tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Configure columns
        headings = {
            "name": "Project Name",
            "type": "Type",
            "status": "Status",
            "complexity": "Complexity"
        }

        for col, heading in headings.items():
            self.project_tree.heading(col, text=heading)
            self.project_tree.column(col, width=100)

        self.project_tree.bind("<<TreeviewSelect>>", self.on_project_select)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar.set)

        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_project_details(self) -> None:
        """Create the project details section."""
        self.details_frame = ttk.LabelFrame(self.content_frame, text="Project Details")
        self.details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Create details fields
        fields = [
            ("Name:", "name"),
            ("Type:", "type"),
            ("Status:", "status"),
            ("Start Date:", "start_date"),
            ("Complexity:", "complexity")
        ]

        self.detail_vars = {}
        for label_text, field_name in fields:
            frame = ttk.Frame(self.details_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)

            ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
            var = tk.StringVar()
            self.detail_vars[field_name] = var
            ttk.Entry(frame, textvariable=var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_material_tracking(self) -> None:
        """Create the material tracking section."""
        frame = ttk.LabelFrame(self.details_frame, text="Materials")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create materials treeview
        columns = ("type", "name", "quantity", "area", "status")
        self.materials_tree = ttk.Treeview(frame, columns=columns, show="headings")

        headings = {
            "type": "Material Type",
            "name": "Name",
            "quantity": "Quantity",
            "area": "Area (sq ft)",
            "status": "Status"
        }

        for col, heading in headings.items():
            self.materials_tree.heading(col, text=heading)
            self.materials_tree.column(col, width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add material buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Material", command=self.show_add_material_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Material", command=self.remove_selected_material).pack(side=tk.LEFT, padx=2)

    def load_data(self) -> None:
        """Load and display project data."""
        try:
            projects = self.project_service.get_all_projects()
            self.project_tree.delete(*self.project_tree.get_children())

            for project in projects:
                values = (
                    project.name,
                    project.project_type.name,
                    project.status.name,
                    f"{project.complexity:.1f}" if project.complexity else "N/A"
                )
                self.project_tree.insert("", tk.END, values=values, tags=(str(project.id),))

        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            self.show_error("Error", "Failed to load projects")

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
            project_id = int(self.project_tree.item(selection[0], "tags")[0])
            project = self.project_service.get_project(project_id, include_components=True)

            # Update details
            self.selected_project_id = project_id
            self.update_project_details(project)
            self.update_materials_list(project)

        except Exception as e:
            logger.error(f"Error loading project details: {str(e)}")
            self.show_error("Error", "Failed to load project details")

    def update_project_details(self, project: Any) -> None:
        """
        Update project details display.

        Args:
            project: Project data object
        """
        details = {
            "name": project.name,
            "type": project.project_type.name,
            "status": project.status.name,
            "start_date": project.start_date.strftime("%Y-%m-%d") if project.start_date else "Not started",
            "complexity": f"{project.complexity:.1f}" if project.complexity else "N/A"
        }

        for field, value in details.items():
            self.detail_vars[field].set(value)

    def update_materials_list(self, project: Any) -> None:
        """
        Update materials list for the selected project.

        Args:
            project: Project data object
        """
        self.materials_tree.delete(*self.materials_tree.get_children())
        self.current_materials.clear()

        for component in project.components:
            material_type = "Leather" if component.material_type == MaterialType.LEATHER else "Hardware"

            values = (
                material_type,
                component.name,
                component.quantity,
                component.area if hasattr(component, 'area') else "N/A",
                component.status.name
            )

            self.materials_tree.insert("", tk.END, values=values, tags=(str(component.id),))
            self.current_materials[component.id] = component.to_dict()

    def show_new_project_dialog(self) -> None:
        """Show dialog for creating a new project."""
        dialog = tk.Toplevel(self)
        dialog.title("New Leatherworking Project")
        dialog.grab_set()

        # Create input fields
        fields = {}
        for label, var_name in [
            ("Project Name:", "name"),
            ("Project Type:", "type"),
            ("Description:", "description")
        ]:
            frame = ttk.Frame(dialog)
            frame.pack(fill=tk.X, padx=5, pady=2)

            ttk.Label(frame, text=label).pack(side=tk.LEFT)
            if var_name == "type":
                var = ttk.Combobox(frame, values=[t.name for t in ProjectType])
                var.set(ProjectType.LEATHER_BAG.name)
            else:
                var = ttk.Entry(frame)
            var.pack(side=tk.LEFT, fill=tk.X, expand=True)
            fields[var_name] = var

        def save_project():
            try:
                project_data = {
                    "name": fields["name"].get(),
                    "project_type": ProjectType[fields["type"].get()],
                    "description": fields["description"].get(),
                    "status": ProductionStatus.NEW,
                    "start_date": datetime.now()
                }

                self.project_service.create_project(project_data)
                dialog.destroy()
                self.load_data()

            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                messagebox.showerror("Error", "Failed to create project")

        ttk.Button(dialog, text="Create", command=save_project).pack(pady=10)

    def show_add_material_dialog(self) -> None:
        """Show dialog for adding materials to the project."""
        if not self.selected_project_id:
            self.show_error("Error", "Please select a project first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Material")
        dialog.grab_set()

        # Create input fields
        fields = {}

        # Material type selection
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(type_frame, text="Material Type:").pack(side=tk.LEFT)
        type_var = tk.StringVar(value="LEATHER")
        fields["type"] = type_var

        for val in ["LEATHER", "HARDWARE"]:
            ttk.Radiobutton(type_frame, text=val, variable=type_var, value=val).pack(side=tk.LEFT)

        # Dynamic fields based on type
        details_frame = ttk.Frame(dialog)
        details_frame.pack(fill=tk.X, padx=5, pady=2)

        def update_fields(*args):
            for widget in details_frame.winfo_children():
                widget.destroy()

            if type_var.get() == "LEATHER":
                labels = [("Leather Type:", "leather_type"), ("Area (sq ft):", "area")]
            else:
                labels = [("Hardware Type:", "hardware_type"), ("Quantity:", "quantity")]

            for label, field_name in labels:
                frame = ttk.Frame(details_frame)
                frame.pack(fill=tk.X, pady=2)
                ttk.Label(frame, text=label).pack(side=tk.LEFT)
                var = ttk.Entry(frame)
                var.pack(side=tk.LEFT, fill=tk.X, expand=True)
                fields[field_name] = var

        type_var.trace("w", update_fields)
        update_fields()

        def add_material():
            try:
                material_data = {
                    "project_id": self.selected_project_id,
                    "type": MaterialType[type_var.get()],
                }

                if type_var.get() == "LEATHER":
                    material_data.update({
                        "leather_type": LeatherType[fields["leather_type"].get()],
                        "area": float(fields["area"].get())
                    })
                else:
                    material_data.update({
                        "hardware_type": fields["hardware_type"].get(),
                        "quantity": int(fields["quantity"].get())
                    })

                self.project_service.add_project_component(self.selected_project_id, material_data)
                dialog.destroy()
                self.on_project_select(None)  # Refresh materials list

            except ValueError as ve:
                logger.error(f"Validation error adding material: {str(ve)}")
                messagebox.showerror("Error", "Invalid input values. Please check your entries.")
            except Exception as e:
                logger.error(f"Error adding material: {str(e)}")
                messagebox.showerror("Error", "Failed to add material")

        ttk.Button(dialog, text="Add", command=add_material).pack(pady=10)

    def remove_selected_material(self) -> None:
        """Remove the selected material from the project."""
        selection = self.materials_tree.selection()
        if not selection or not self.selected_project_id:
            return

        if messagebox.askyesno("Confirm", "Remove selected material from project?"):
            try:
                component_id = int(self.materials_tree.item(selection[0], "tags")[0])
                self.project_service.remove_project_component(self.selected_project_id, component_id)
                self.on_project_select(None)  # Refresh materials list

            except Exception as e:
                logger.error(f"Error removing material: {str(e)}")
                self.show_error("Error", "Failed to remove material")

    def delete_selected_project(self) -> None:
        """Delete the selected project."""
        if not self.selected_project_id:
            return

        if messagebox.askyesno("Confirm", "Delete selected project? This cannot be undone."):
            try:
                self.project_service.delete_project(self.selected_project_id)
                self.selected_project_id = None
                self.load_data()

                # Clear details
                for var in self.detail_vars.values():
                    var.set("")
                self.materials_tree.delete(*self.materials_tree.get_children())

            except Exception as e:
                logger.error(f"Error deleting project: {str(e)}")
                self.show_error("Error", "Failed to delete project")

    def export_project_report(self) -> None:
        """Export a detailed report of the selected project."""
        if not self.selected_project_id:
            self.show_error("Error", "Please select a project to export")
            return

        try:
            # Get file path for saving
            file_path = tk.filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )

            if not file_path:
                return

            # Generate and save report
            self.project_service.generate_project_report(self.selected_project_id, file_path)
            messagebox.showinfo("Success", "Project report exported successfully")

        except Exception as e:
            logger.error(f"Error exporting project report: {str(e)}")
            self.show_error("Error", "Failed to export project report")

    def filter_projects(self) -> None:
        """Filter projects based on search text."""
        search_term = self.search_var.get().lower()

        try:
            self.project_tree.delete(*self.project_tree.get_children())
            projects = self.project_service.search_projects({"search_term": search_term})

            for project in projects:
                values = (
                    project.name,
                    project.project_type.name,
                    project.status.name,
                    f"{project.complexity:.1f}" if project.complexity else "N/A"
                )
                self.project_tree.insert("", tk.END, values=values, tags=(str(project.id),))

        except Exception as e:
            logger.error(f"Error filtering projects: {str(e)}")
            # Don't show error dialog for search issues

    def show_error(self, title: str, message: str) -> None:
        """
        Show error message dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)

    def cleanup(self) -> None:
        """Perform cleanup before view is destroyed."""
        # Clear any temporary data or resources
        self.selected_project_id = None
        self.current_materials.clear()