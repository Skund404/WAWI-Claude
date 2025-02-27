# gui/product/project_view.py
"""
View for managing leatherworking projects.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple

from utils.circular_import_resolver import CircularImportResolver

# Use the circular import resolver to avoid import errors
Project = CircularImportResolver.lazy_import("database.models.project", "Project")
ProjectComponent = CircularImportResolver.lazy_import("database.models.project", "ProjectComponent")

# Import services through the container/app
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel


class ProjectView(ttk.Frame):
    """View for managing leatherworking projects."""

    def __init__(self, parent: ttk.Frame, app: Any):
        """Initialize the ProjectView.

        Args:
            parent: Parent frame for the view
            app: Application instance providing access to services
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.app = app

        # Try to get the project service
        self.project_service = self.app.get_service(IProjectService)

        if not self.project_service:
            self.logger.error("Failed to retrieve ProjectService")
            messagebox.showerror(
                "Service Error",
                "Project service not available. Some functionality may be limited."
            )

        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Split into left (list) and right (details) panes
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left pane - Project list
        self.list_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.list_frame, weight=1)

        # Toolbar for list actions
        self.list_toolbar = ttk.Frame(self.list_frame)
        self.list_toolbar.pack(fill=tk.X, pady=5)

        # Add buttons to toolbar
        self.add_btn = ttk.Button(self.list_toolbar, text="New Project", command=self._on_add_project)
        self.add_btn.pack(side=tk.LEFT, padx=2)

        self.delete_btn = ttk.Button(self.list_toolbar, text="Delete", command=self._on_delete_project)
        self.delete_btn.pack(side=tk.LEFT, padx=2)

        self.refresh_btn = ttk.Button(self.list_toolbar, text="Refresh", command=self._refresh_projects)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        # Search and filter frame
        self.search_frame = ttk.Frame(self.list_frame)
        self.search_frame.pack(fill=tk.X, pady=5)

        # Search entry
        ttk.Label(self.search_frame, text="Search:").pack(side=tk.LEFT, padx=2)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.search_entry.bind("<Return>", self._on_search)

        # Type filter
        ttk.Label(self.search_frame, text="Type:").pack(side=tk.LEFT, padx=(10, 2))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(self.search_frame, textvariable=self.type_var, width=12)
        self.type_combo['values'] = ['All'] + [t.name for t in ProjectType]
        self.type_combo.current(0)
        self.type_combo.pack(side=tk.LEFT, padx=2)
        self.type_combo.bind("<<ComboboxSelected>>", self._apply_filters)

        # Project list
        self.project_tree = ttk.Treeview(
            self.list_frame,
            columns=("name", "type", "status", "progress"),
            show="headings",
            selectmode="browse"
        )
        self.project_tree.heading("name", text="Name")
        self.project_tree.heading("type", text="Type")
        self.project_tree.heading("status", text="Status")
        self.project_tree.heading("progress", text="Progress")

        self.project_tree.column("name", width=150)
        self.project_tree.column("type", width=100)
        self.project_tree.column("status", width=100)
        self.project_tree.column("progress", width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.project_tree.bind("<<TreeviewSelect>>", self._on_project_select)
        self.project_tree.bind("<Double-1>", self._on_project_double_click)

        # Right pane - Project details
        self.details_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.details_frame, weight=2)

        # Details title
        self.details_title = ttk.Label(self.details_frame, text="Project Details", font=("Arial", 12, "bold"))
        self.details_title.pack(fill=tk.X, pady=5)

        # Form frame
        self.form_frame = ttk.Frame(self.details_frame)
        self.form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Form fields
        # Name
        ttk.Label(self.form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.form_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        # Type
        ttk.Label(self.form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.project_type_var = tk.StringVar()
        self.project_type_combo = ttk.Combobox(self.form_frame, textvariable=self.project_type_var, width=20)
        self.project_type_combo['values'] = [t.name for t in ProjectType]
        self.project_type_combo.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Description
        ttk.Label(self.form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.description_text = tk.Text(self.form_frame, height=4, width=40)
        self.description_text.grid(row=2, column=1, sticky=tk.W + tk.E, pady=5)

        # Skill level
        ttk.Label(self.form_frame, text="Skill Level:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.skill_level_var = tk.StringVar()
        self.skill_level_combo = ttk.Combobox(self.form_frame, textvariable=self.skill_level_var, width=15)
        self.skill_level_combo['values'] = [s.name for s in SkillLevel]
        self.skill_level_combo.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Status
        ttk.Label(self.form_frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar()
        self.status_entry = ttk.Entry(self.form_frame, textvariable=self.status_var, width=15)
        self.status_entry.grid(row=4, column=1, sticky=tk.W, pady=5)

        # Progress
        ttk.Label(self.form_frame, text="Progress:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.IntVar()
        self.progress_scale = ttk.Scale(
            self.form_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self._on_progress_change
        )
        self.progress_scale.grid(row=5, column=1, sticky=tk.W + tk.E, pady=5)
        self.progress_label = ttk.Label(self.form_frame, text="0%")
        self.progress_label.grid(row=5, column=2, sticky=tk.W, pady=5)

        # Components section
        ttk.Label(self.form_frame, text="Components:", font=("Arial", 10, "bold")).grid(
            row=6, column=0, sticky=tk.W, pady=10
        )

        # Components tree
        self.components_frame = ttk.Frame(self.form_frame)
        self.components_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W + tk.E + tk.N + tk.S, pady=5)

        self.components_tree = ttk.Treeview(
            self.components_frame,
            columns=("name", "material", "quantity"),
            show="headings",
            height=6
        )
        self.components_tree.heading("name", text="Component")
        self.components_tree.heading("material", text="Material")
        self.components_tree.heading("quantity", text="Quantity")

        self.components_tree.column("name", width=150)
        self.components_tree.column("material", width=150)
        self.components_tree.column("quantity", width=100)

        # Add scrollbar
        comp_scrollbar = ttk.Scrollbar(self.components_frame, orient="vertical", command=self.components_tree.yview)
        self.components_tree.configure(yscrollcommand=comp_scrollbar.set)

        comp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.components_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Component buttons
        self.comp_buttons_frame = ttk.Frame(self.form_frame)
        self.comp_buttons_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)

        self.add_comp_btn = ttk.Button(
            self.comp_buttons_frame,
            text="Add Component",
            command=self._on_add_component
        )
        self.add_comp_btn.pack(side=tk.LEFT, padx=2)

        self.remove_comp_btn = ttk.Button(
            self.comp_buttons_frame,
            text="Remove Component",
            command=self._on_remove_component
        )
        self.remove_comp_btn.pack(side=tk.LEFT, padx=2)

        # Action buttons
        self.actions_frame = ttk.Frame(self.form_frame)
        self.actions_frame.grid(row=9, column=0, columnspan=3, sticky=tk.E, pady=15)

        self.cancel_btn = ttk.Button(self.actions_frame, text="Cancel", command=self._on_cancel)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        self.save_btn = ttk.Button(self.actions_frame, text="Save", command=self._on_save)
        self.save_btn.pack(side=tk.RIGHT, padx=5)

        # Make the form resizable
        self.form_frame.columnconfigure(1, weight=1)

        # Initial state
        self._clear_form()
        self._disable_form()

    def _load_initial_data(self):
        """Load initial project data."""
        self._refresh_projects()

    def _refresh_projects(self):
        """Refresh the projects list."""
        # Clear existing items
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)

        if not self.project_service:
            return

        # Get all projects
        try:
            # Filter by type if selected
            project_type = None
            if self.type_var.get() != 'All':
                try:
                    project_type = ProjectType[self.type_var.get()]
                except (KeyError, ValueError):
                    pass

            projects = self.project_service.list_projects(project_type=project_type)

            # Apply search filter if needed
            search_text = self.search_var.get().strip().lower()
            if search_text:
                projects = [p for p in projects if
                            search_text in p['name'].lower() or
                            (p['description'] and search_text in p['description'].lower())]

            # Add to tree
            for project in projects:
                self.project_tree.insert(
                    "",
                    "end",
                    iid=project['id'],
                    values=(
                        project['name'],
                        project['project_type'].name if hasattr(project['project_type'], 'name') else project[
                            'project_type'],
                        project['status'],
                        f"{project['progress']}%"
                    )
                )

        except Exception as e:
            self.logger.error(f"Error loading projects: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load projects: {str(e)}")

    def _on_search(self, event=None):
        """Handle search."""
        self._refresh_projects()

    def _apply_filters(self, event=None):
        """Apply filters to the project list."""
        self._refresh_projects()

    def _on_project_select(self, event=None):
        """Handle project selection."""
        selected_id = self._get_selected_project_id()
        if not selected_id:
            return

        if not self.project_service:
            return

        try:
            project = self.project_service.get_project(selected_id)
            if project:
                self._populate_form(project)
                self._enable_form()
        except Exception as e:
            self.logger.error(f"Error loading project details: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load project details: {str(e)}")

    def _on_project_double_click(self, event=None):
        """Handle double-click on a project (same as select)."""
        self._on_project_select(event)

    def _on_add_project(self):
        """Handle adding a new project."""
        self._clear_form()
        self._enable_form()
        self.project_tree.selection_remove(self.project_tree.selection())

    def _on_delete_project(self):
        """Handle deleting a project."""
        selected_id = self._get_selected_project_id()
        if not selected_id:
            messagebox.showinfo("Information", "Please select a project to delete.")
            return

        if not self.project_service:
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this project?"):
            return

        try:
            result = self.project_service.delete_project(selected_id)
            if result:
                self._clear_form()
                self._disable_form()
                self._refresh_projects()
                messagebox.showinfo("Success", "Project deleted successfully.")
            else:
                messagebox.showerror("Error", "Failed to delete project.")
        except Exception as e:
            self.logger.error(f"Error deleting project: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to delete project: {str(e)}")

    def _on_save(self):
        """Handle saving a project."""
        if not self.project_service:
            return

        # Validate form
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Project name is required.")
            return

        # Get project type
        project_type_str = self.project_type_var.get()
        try:
            project_type = ProjectType[project_type_str]
        except (KeyError, ValueError):
            messagebox.showwarning("Validation Error", "Invalid project type.")
            return

        # Get skill level
        skill_level_str = self.skill_level_var.get()
        try:
            skill_level = SkillLevel[skill_level_str]
        except (KeyError, ValueError):
            messagebox.showwarning("Validation Error", "Invalid skill level.")
            return

        # Get description
        description = self.description_text.get("1.0", tk.END).strip()

        # Get progress
        progress = self.progress_var.get()

        # Get status
        status = self.status_var.get().strip()

        # Check if this is a new project or an update
        selected_id = self._get_selected_project_id()

        try:
            if selected_id:
                # Update existing project
                updates = {
                    "name": name,
                    "project_type": project_type,
                    "description": description,
                    "skill_level": skill_level,
                    "status": status,
                    "progress": progress
                }
                project = self.project_service.update_project(selected_id, updates)
                if project:
                    self._refresh_projects()
                    self._populate_form(project)
                    messagebox.showinfo("Success", "Project updated successfully.")
                else:
                    messagebox.showerror("Error", "Failed to update project.")
            else:
                # Create new project
                project = self.project_service.create_project(
                    name=name,
                    project_type=project_type,
                    description=description,
                    skill_level=skill_level
                )

                if project:
                    # Update the progress and status
                    updates = {
                        "status": status,
                        "progress": progress
                    }
                    project = self.project_service.update_project(project["id"], updates)

                    self._refresh_projects()

                    # Select the new project
                    self.project_tree.selection_set(project["id"])
                    self.project_tree.see(project["id"])
                    self._on_project_select()

                    messagebox.showinfo("Success", "Project created successfully.")
                else:
                    messagebox.showerror("Error", "Failed to create project.")

        except Exception as e:
            self.logger.error(f"Error saving project: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def _on_cancel(self):
        """Handle canceling edits."""
        selected_id = self._get_selected_project_id()
        if selected_id:
            # Revert to saved data
            self._on_project_select()
        else:
            # Clear the form
            self._clear_form()
            self._disable_form()

    def _on_add_component(self):
        """Handle adding a component to the project."""
        selected_id = self._get_selected_project_id()
        if not selected_id:
            messagebox.showinfo("Information", "Please save the project before adding components.")
            return

        if not self.project_service:
            return

        # Create a simple dialog for adding a component
        dialog = tk.Toplevel(self)
        dialog.title("Add Component")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        # Form frame
        form_frame = ttk.Frame(dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Component name
        ttk.Label(form_frame, text="Component Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        comp_name_var = tk.StringVar()
        comp_name_entry = ttk.Entry(form_frame, textvariable=comp_name_var, width=30)
        comp_name_entry.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        # Material type
        ttk.Label(form_frame, text="Material Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        material_type_var = tk.StringVar()
        material_type_entry = ttk.Entry(form_frame, textvariable=material_type_var, width=20)
        material_type_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Quantity
        ttk.Label(form_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=5)
        quantity_var = tk.DoubleVar(value=1.0)
        quantity_entry = ttk.Spinbox(form_frame, from_=0.1, to=1000.0, increment=0.1, textvariable=quantity_var)
        quantity_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Notes
        ttk.Label(form_frame, text="Notes:").grid(row=3, column=0, sticky=tk.W, pady=5)
        notes_text = tk.Text(form_frame, height=3, width=30)
        notes_text.grid(row=3, column=1, sticky=tk.W + tk.E, pady=5)

        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=10)

        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        def add_component():
            name = comp_name_var.get().strip()
            if not name:
                messagebox.showwarning("Validation Error", "Component name is required.", parent=dialog)
                return

            material_type = material_type_var.get().strip()
            quantity = quantity_var.get()
            notes = notes_text.get("1.0", tk.END).strip()

            try:
                result = self.project_service.add_component_to_project(
                    project_id=selected_id,
                    component_name=name,
                    material_type=material_type,
                    quantity=quantity,
                    notes=notes
                )

                if result:
                    dialog.destroy()
                    self._on_project_select()  # Refresh form
                    messagebox.showinfo("Success", "Component added successfully.")
                else:
                    messagebox.showerror("Error", "Failed to add component.")
            except Exception as e:
                self.logger.error(f"Error adding component: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Failed to add component: {str(e)}")

        add_btn = ttk.Button(buttons_frame, text="Add", command=add_component)
        add_btn.pack(side=tk.RIGHT, padx=5)

        # Make the form resizable
        form_frame.columnconfigure(1, weight=1)

        # Focus on the name field
        comp_name_entry.focus_set()

        # Make the dialog modal
        dialog.wait_window()

    def _on_remove_component(self):
        """Handle removing a component from the project."""
        selected_id = self._get_selected_project_id()
        if not selected_id:
            return

        # Get selected component
        selection = self.components_tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a component to remove.")
            return

        component_id = selection[0]

        if not self.project_service:
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Remove", "Are you sure you want to remove this component?"):
            return

        try:
            result = self.project_service.remove_component_from_project(selected_id, component_id)
            if result:
                self._on_project_select()  # Refresh form
                messagebox.showinfo("Success", "Component removed successfully.")
            else:
                messagebox.showerror("Error", "Failed to remove component.")
        except Exception as e:
            self.logger.error(f"Error removing component: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to remove component: {str(e)}")

    def _on_progress_change(self, value):
        """Handle progress slider change."""
        progress = int(float(value))
        self.progress_label.config(text=f"{progress}%")

    def _get_selected_project_id(self) -> Optional[str]:
        """Get the ID of the selected project or None."""
        selection = self.project_tree.selection()
        if selection:
            return selection[0]
        return None

    def _populate_form(self, project: Dict[str, Any]):
        """Populate the form with project data."""
        # Basic fields
        self.name_var.set(project.get('name', ''))

        project_type = project.get('project_type')
        if hasattr(project_type, 'name'):
            self.project_type_var.set(project_type.name)
        else:
            self.project_type_var.set(str(project_type))

        skill_level = project.get('skill_level')
        if hasattr(skill_level, 'name'):
            self.skill_level_var.set(skill_level.name)
        else:
            self.skill_level_var.set(str(skill_level))

        # Description (clear and insert)
        self.description_text.delete("1.0", tk.END)
        description = project.get('description', '')
        if description:
            self.description_text.insert("1.0", description)

        # Status and progress
        self.status_var.set(project.get('status', 'PLANNING'))
        self.progress_var.set(project.get('progress', 0))
        self.progress_label.config(text=f"{project.get('progress', 0)}%")

        # Update components tree
        self._populate_components(project.get('components', []))

    def _populate_components(self, components: List[Dict[str, Any]]):
        """Populate the components tree."""
        # Clear existing items
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)

        # Add components
        for component in components:
            material_info = component.get('material_type', '')
            if component.get('material_id'):
                material_info += f" ({component.get('material_id')})"

            self.components_tree.insert(
                "",
                "end",
                iid=component.get('id'),
                values=(
                    component.get('name', ''),
                    material_info,
                    component.get('quantity', 0)
                )
            )

    def _clear_form(self):
        """Clear all form fields."""
        self.name_var.set('')
        self.project_type_var.set('')
        self.skill_level_var.set('')
        self.status_var.set('PLANNING')
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.description_text.delete("1.0", tk.END)

        # Clear components
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)

    def _enable_form(self):
        """Enable form fields."""
        for widget in [
            self.name_entry,
            self.project_type_combo,
            self.description_text,
            self.skill_level_combo,
            self.status_entry,
            self.progress_scale,
            self.save_btn,
            self.cancel_btn,
            self.add_comp_btn,
            self.remove_comp_btn
        ]:
            widget.configure(state="normal")

    def _disable_form(self):
        """Disable form fields."""
        for widget in [
            self.name_entry,
            self.project_type_combo,
            self.description_text,
            self.skill_level_combo,
            self.status_entry,
            self.progress_scale,
            self.save_btn,
            self.cancel_btn,
            self.add_comp_btn,
            self.remove_comp_btn
        ]:
            widget.configure(state="disabled")