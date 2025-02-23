# Path: gui/leatherworking/project_dashboard.py
"""
Project Dashboard for leatherworking project management.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List


class ProjectDashboard(tk.Frame):
    """
    A comprehensive dashboard for managing leatherworking projects.
    """

    def __init__(self, parent, controller=None):
        """
        Initialize the project dashboard.

        Args:
            parent (tk.Tk or tk.Frame): Parent widget
            controller (object, optional): Application controller for navigation
        """
        super().__init__(parent)
        self.controller = controller

        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Modern, clean theme

        # Setup UI components
        self._setup_layout()
        self._create_overview_section()
        self._create_project_list()
        self._create_quick_actions()

        # Load initial data
        self.load_data()

    def _setup_layout(self):
        """
        Set up the dashboard layout with grid configuration.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # Create main sections
        self.overview_frame = ttk.Frame(self, padding=(10, 10))
        self.overview_frame.grid(row=0, column=0, sticky='nsew')

        self.project_list_frame = ttk.Frame(self, padding=(10, 10))
        self.project_list_frame.grid(row=0, column=1, sticky='nsew')

        self.quick_actions_frame = ttk.Frame(self, padding=(10, 10))
        self.quick_actions_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')

    def _create_overview_section(self):
        """
        Create project overview section with key metrics.
        """
        # Overview title
        ttk.Label(
            self.overview_frame,
            text="Project Overview",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))

        # Metrics display
        self.metrics_frame = ttk.Frame(self.overview_frame)
        self.metrics_frame.pack(fill='x')

        metrics = [
            ("Total Projects", "total_projects"),
            ("In Progress", "in_progress"),
            ("Completed", "completed"),
            ("Avg. Complexity", "avg_complexity")
        ]

        for label, metric_key in metrics:
            metric_frame = ttk.Frame(self.metrics_frame)
            metric_frame.pack(fill='x', pady=5)

            ttk.Label(metric_frame, text=label, width=15).pack(side='left')
            metric_label = ttk.Label(metric_frame, text="0", width=10)
            metric_label.pack(side='right')
            setattr(self, f"{metric_key}_label", metric_label)

    def _create_project_list(self):
        """
        Create a treeview to display project list.
        """
        # Project list title
        ttk.Label(
            self.project_list_frame,
            text="Recent Projects",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))

        # Treeview for projects
        columns = ('Name', 'Type', 'Complexity', 'Status')
        self.project_tree = ttk.Treeview(
            self.project_list_frame,
            columns=columns,
            show='headings'
        )

        # Configure columns
        for col in columns:
            self.project_tree.heading(col, text=col)
            self.project_tree.column(col, width=100, anchor='center')

        self.project_tree.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.project_list_frame,
            orient='vertical',
            command=self.project_tree.yview
        )
        self.project_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def _create_quick_actions(self):
        """
        Create quick action buttons.
        """
        ttk.Label(
            self.quick_actions_frame,
            text="Quick Actions",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))

        actions = [
            ("New Project", self.new_project),
            ("Import Project", self.import_project),
            ("Generate Report", self.generate_report)
        ]

        action_frame = ttk.Frame(self.quick_actions_frame)
        action_frame.pack(fill='x')

        for label, command in actions:
            btn = ttk.Button(action_frame, text=label, command=command)
            btn.pack(side='left', padx=5, expand=True, fill='x')

    def load_data(self, projects: List[Dict[str, Any]] = None):
        """
        Load project data into the dashboard.

        Args:
            projects (List[Dict[str, Any]], optional): List of project data
        """
        # Clear existing data
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)

        # Mock data if not provided
        if projects is None:
            projects = [
                {
                    'name': 'Leather Messenger Bag',
                    'type': 'Bag',
                    'complexity': 7,
                    'status': 'In Progress'
                }
            ]

        # Populate treeview
        for project in projects:
            self.project_tree.insert('', 'end', values=(
                project['name'],
                project['type'],
                project['complexity'],
                project['status']
            ))

        # Update metrics (mock data)
        metrics = {
            'total_projects': len(projects),
            'in_progress': sum(1 for p in projects if p['status'] == 'In Progress'),
            'completed': sum(1 for p in projects if p['status'] == 'Completed'),
            'avg_complexity': sum(p['complexity'] for p in projects) / len(projects) if projects else 0
        }

        for key, value in metrics.items():
            label = getattr(self, f"{key}_label", None)
            if label:
                label.config(text=f"{value:.1f}" if isinstance(value, float) else str(value))

    def new_project(self):
        """
        Open dialog to create a new project.
        """
        # TODO: Implement new project dialog
        print("Opening new project dialog")

    def import_project(self):
        """
        Open dialog to import an existing project.
        """
        # TODO: Implement project import functionality
        print("Opening project import dialog")

    def generate_report(self):
        """
        Generate a project report.
        """
        # TODO: Implement report generation
        print("Generating project report")


def main():
    """
    Standalone testing of the ProjectDashboard.
    """
    root = tk.Tk()
    root.title("Leatherworking Project Dashboard")
    root.geometry("800x600")

    dashboard = ProjectDashboard(root)
    dashboard.pack(fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()