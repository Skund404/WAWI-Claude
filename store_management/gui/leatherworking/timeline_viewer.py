# Path: gui/leatherworking/timeline_viewer.py
"""
Timeline Viewer for tracking and visualizing leatherworking project progress.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Any, Optional


class TimelineViewer(tk.Frame):
    """
    A comprehensive timeline visualization tool for leatherworking projects.
    """

    def __init__(self, parent, controller=None):
        """
        Initialize the timeline viewer.

        Args:
            parent (tk.Tk or tk.Frame): Parent widget
            controller (object, optional): Application controller for navigation
        """
        super().__init__(parent)
        self.controller = controller

        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Project timeline data
        self.projects: List[Dict[str, Any]] = []

        # Setup UI components
        self._setup_layout()
        self._create_project_input()
        self._create_timeline_chart()
        self._create_project_list()

        # Load initial data
        self.load_initial_projects()

    def _setup_layout(self):
        """
        Configure grid layout for timeline viewer.
        """
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Create main sections
        self.input_frame = ttk.LabelFrame(self, text="Project Timeline Input", padding=(10, 10))
        self.input_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.chart_frame = ttk.LabelFrame(self, text="Project Timeline", padding=(10, 10))
        self.chart_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        self.list_frame = ttk.LabelFrame(self, text="Project List", padding=(10, 10))
        self.list_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

    def _create_project_input(self):
        """
        Create input fields for project timeline tracking.
        """
        # Project Name
        ttk.Label(self.input_frame, text="Project Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.project_name_var = tk.StringVar()
        project_name_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.project_name_var,
            width=30
        )
        project_name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Project Type
        ttk.Label(self.input_frame, text="Project Type:").grid(row=1, column=0, sticky='w', pady=5)
        self.project_type_var = tk.StringVar()
        project_types = [
            "Wallet",
            "Bag",
            "Accessory",
            "Custom Project"
        ]
        project_type_dropdown = ttk.Combobox(
            self.input_frame,
            textvariable=self.project_type_var,
            values=project_types,
            state="readonly",
            width=27
        )
        project_type_dropdown.grid(row=1, column=1, sticky='ew', pady=5)

        # Start Date
        ttk.Label(self.input_frame, text="Start Date:").grid(row=2, column=0, sticky='w', pady=5)
        self.start_date_var = tk.StringVar()
        start_date_entry = DateEntry(
            self.input_frame,
            textvariable=self.start_date_var,
            width=27,
            date_pattern='y-mm-dd'
        )
        start_date_entry.grid(row=2, column=1, sticky='ew', pady=5)

        # Estimated Duration (Days)
        ttk.Label(self.input_frame, text="Est. Duration (Days):").grid(row=3, column=0, sticky='w', pady=5)
        self.duration_var = tk.StringVar()
        duration_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.duration_var,
            width=30
        )
        duration_entry.grid(row=3, column=1, sticky='ew', pady=5)

        # Status
        ttk.Label(self.input_frame, text="Status:").grid(row=4, column=0, sticky='w', pady=5)
        self.status_var = tk.StringVar(value="Not Started")
        status_options = [
            "Not Started",
            "In Progress",
            "On Hold",
            "Completed"
        ]
        status_dropdown = ttk.Combobox(
            self.input_frame,
            textvariable=self.status_var,
            values=status_options,
            state="readonly",
            width=27
        )
        status_dropdown.grid(row=4, column=1, sticky='ew', pady=5)

        # Add Project Button
        add_btn = ttk.Button(
            self.input_frame,
            text="Add Project",
            command=self.add_project
        )
        add_btn.grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

    def _create_timeline_chart(self):
        """
        Create matplotlib timeline chart in Tkinter.
        """
        # Create matplotlib figure
        self.figure, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.ax.set_title("Project Timeline")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Projects")

        # Embed matplotlib figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True)

    def _create_project_list(self):
        """
        Create a treeview to display project timelines.
        """
        columns = ('Project Name', 'Type', 'Start Date', 'Duration', 'Status')
        self.project_tree = ttk.Treeview(
            self.list_frame,
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
            self.list_frame,
            orient='vertical',
            command=self.project_tree.yview
        )
        self.project_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Context menu
        self.project_tree_context_menu = tk.Menu(self, tearoff=0)
        self.project_tree_context_menu.add_command(
            label="Delete",
            command=self.delete_selected_project
        )
        self.project_tree.bind('<Button-3>', self.show_context_menu)

    def add_project(self):
        """
        Add a new project to the timeline.
        """
        try:
            # Validate inputs
            project_name = self.project_name_var.get().strip()
            if not project_name:
                raise ValueError("Project name cannot be empty")

            project_type = self.project_type_var.get()
            if not project_type:
                raise ValueError("Please select a project type")

            start_date = datetime.datetime.strptime(
                self.start_date_var.get(),
                '%Y-%m-%d'
            ).date()

            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError("Duration must be a positive number")

            status = self.status_var.get()

            # Create project entry
            project = {
                'name': project_name,
                'type': project_type,
                'start_date': start_date,
                'duration': duration,
                'status': status
            }

            # Add to projects list
            self.projects.append(project)

            # Add to treeview
            self.project_tree.insert('', 'end', values=(
                project['name'],
                project['type'],
                project['start_date'].strftime('%Y-%m-%d'),
                f"{project['duration']} days",
                project['status']
            ))

            # Update timeline chart
            self.update_timeline_chart()

            # Clear input fields
            self.project_name_var.set('')
            self.project_type_var.set('')
            self.duration_var.set('')
            self.status_var.set('Not Started')

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def update_timeline_chart(self):
        """
        Update the timeline visualization.
        """
        # Clear previous plot
        self.ax.clear()
        self.ax.set_title("Project Timeline")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Projects")

        # Sort projects by start date
        sorted_projects = sorted(self.projects, key=lambda x: x['start_date'])

        # Color mapping for project status
        status_colors = {
            'Not Started': 'lightgray',
            'In Progress': 'blue',
            'On Hold': 'orange',
            'Completed': 'green'
        }

        # Plot each project as a horizontal bar
        for idx, project in enumerate(sorted_projects):
            end_date = project['start_date'] + datetime.timedelta(days=project['duration'])

            self.ax.barh(
                project['name'],
                project['duration'],
                left=project['start_date'].toordinal(),
                color=status_colors.get(project['status'], 'lightgray'),
                alpha=0.7
            )

        # Adjust layout
        plt.tight_layout()

        # Redraw canvas
        self.canvas.draw()

    def delete_selected_project(self):
        """
        Delete the selected project from the timeline.
        """
        selected_item = self.project_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection", "Please select a project to delete.")
            return

        # Remove from treeview
        self.project_tree.delete(selected_item[0])

        # Remove from projects list
        del self.projects[self.project_tree.index(selected_item[0])]

        # Update timeline chart
        self.update_timeline_chart()

    def show_context_menu(self, event):
        """
        Show context menu for project list.
        """
        # Select the row under the cursor
        iid = self.project_tree.identify_row(event.y)
        if iid:
            self.project_tree.selection_set(iid)
            self.project_tree_context_menu.post(event.x_root, event.y_root)

    def load_initial_projects(self):
        """
        Load some initial projects for demonstration.
        """
        initial_projects = [
            {
                'name': 'Leather Messenger Bag',
                'type': 'Bag',
                'start_date': datetime.date(2024, 3, 1),
                'duration': 45,
                'status': 'In Progress'
            },
            {
                'name': 'Classic Wallet',
                'type': 'Wallet',
                'start_date': datetime.date(2024, 2, 15),
                'duration': 30,
                'status': 'Completed'
            }
        ]

        for project in initial_projects:
            self.projects.append(project)
            self.project_tree.insert('', 'end', values=(
                project['name'],
                project['type'],
                project['start_date'].strftime('%Y-%m-%d'),
                f"{project['duration']} days",
                project['status']
            ))

        # Update timeline chart with initial projects
        self.update_timeline_chart()


def main():
    """
    Standalone testing of the TimelineViewer.
    """
    root = tk.Tk()
    root.title("Leatherworking Project Timeline")
    root.geometry("1000x700")

    timeline_viewer = TimelineViewer(root)
    timeline_viewer.pack(fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()