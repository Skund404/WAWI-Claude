# utils/config_management_ui.py
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Import performance tracker
from utils.performance_tracker import PERFORMANCE_TRACKER
from utils.config_tracker import CONFIG_TRACKER

"""
Configuration Management User Interface for Store Management System.

Provides a comprehensive GUI for managing system configurations
across different environments.
"""


class ConfigManagementUI(tk.Tk):
    """
    Advanced configuration management user interface.

    Provides features for:
    - Viewing current configurations
    - Editing configuration parameters
    - Switching between environments
    - Exporting/importing configurations
    """

    def __init__(self):
        """
        Initialize the Configuration Management UI.
        """
        super().__init__()
        self.title('Store Management Configuration')
        self.geometry('800x600')
        self.current_config = {}
        self.current_environment = tk.StringVar(value='development')
        self.config_entries = {}
        self._create_main_layout()
        self._load_initial_configuration()

    def _create_main_layout(self):
        """
        Create the main layout for the configuration management UI.
        """
        # Main container frame
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Environment selector section
        env_frame = ttk.Frame(main_frame)
        env_frame.pack(fill=tk.X, pady=5)
        ttk.Label(env_frame, text='Environment:').pack(side=tk.LEFT)

        env_selector = ttk.Combobox(
            env_frame,
            textvariable=self.current_environment,
            values=['development', 'production', 'testing'],
            state='readonly'
        )
        env_selector.pack(side=tk.LEFT, padx=5)
        env_selector.bind('<<ComboboxSelected>>', self._on_environment_change)

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text='Configuration')
        self._create_config_editor(config_frame)

        # Performance metrics tab
        metrics_frame = ttk.Frame(notebook)
        notebook.add(metrics_frame, text='Performance Metrics')
        self._create_performance_metrics(metrics_frame)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            action_frame,
            text='Save Configuration',
            command=self._save_configuration
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text='Import Configuration',
            command=self._import_configuration
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text='Export Configuration',
            command=self._export_configuration
        ).pack(side=tk.LEFT, padx=5)

    def _create_config_editor(self, parent):
        """
        Create the configuration editor section.

        Args:
            parent: Parent frame for the configuration editor
        """
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure scrolling
        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Clear existing entries
        self.config_entries.clear()

        # Create entries for each config item
        for key, value in self.current_config.items():
            entry_frame = ttk.Frame(scrollable_frame)
            entry_frame.pack(fill=tk.X, pady=2)
            ttk.Label(entry_frame, text=key, width=30).pack(side=tk.LEFT, padx=5)

            if isinstance(value, bool):
                # Boolean config (checkbox)
                var = tk.BooleanVar(value=value)
                entry = ttk.Checkbutton(
                    entry_frame, variable=var, onvalue=True, offvalue=False
                )
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var

            elif isinstance(value, (int, float)):
                # Numeric config (entry field)
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=20)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var

            elif isinstance(value, str):
                # String config (entry field)
                var = tk.StringVar(value=value)
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var

            elif isinstance(value, dict):
                # Nested config (button to edit)
                entry = ttk.Button(
                    entry_frame,
                    text='Edit Nested Config',
                    command=lambda k=key, v=value: self._open_nested_config_editor(k, v)
                )
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = entry

    def _create_performance_metrics(self, parent):
        """
        Create the performance metrics display section.

        Args:
            parent: Parent frame for performance metrics
        """
        # Text widget for displaying metrics
        metrics_text = tk.Text(parent, wrap=tk.WORD, height=20)
        metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Get and display report
        report = PERFORMANCE_TRACKER.generate_performance_report()
        metrics_text.insert(tk.END, report)
        metrics_text.config(state=tk.DISABLED)

        # Refresh button
        refresh_btn = ttk.Button(
            parent,
            text='Refresh Metrics',
            command=lambda: self._update_performance_metrics(metrics_text)
        )
        refresh_btn.pack(pady=5)

    def _load_initial_configuration(self):
        """
        Load initial configuration for the selected environment.
        """
        try:
            # Load configuration
            self.current_config = CONFIG_TRACKER.load_environment_config(
                self.current_environment.get()
            )

            # Clear and rebuild the configuration editor
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    for child in config_frame.winfo_children():
                        child.destroy()
                    self._create_config_editor(config_frame)

        except Exception as e:
            messagebox.showerror('Configuration Load Error', str(e))

    def _on_environment_change(self, event=None):
        """
        Handle environment selection change.

        Args:
            event: ComboboxSelected event (not used)
        """
        self._load_initial_configuration()

    def _save_configuration(self):
        """
        Save the current configuration.
        """
        try:
            # Collect updated configuration values
            updated_config = {}
            for key, var in self.config_entries.items():
                if isinstance(var, tk.BooleanVar):
                    updated_config[key] = var.get()
                elif isinstance(var, tk.StringVar):
                    try:
                        value = var.get()
                        # Try to convert to appropriate type
                        if value.isdigit():
                            updated_config[key] = int(value)
                        elif '.' in value:
                            updated_config[key] = float(value)
                        else:
                            updated_config[key] = value
                    except ValueError:
                        updated_config[key] = var.get()

            # Save to file
            env = self.current_environment.get()
            config_filename = f'config.{env}.json'
            config_path = os.path.join(CONFIG_TRACKER.base_config_dir, config_filename)

            with open(config_path, 'w') as config_file:
                json.dump(updated_config, config_file, indent=4)

            # Save snapshot
            CONFIG_TRACKER.save_config_snapshot(updated_config, env)

            messagebox.showinfo('Configuration', 'Configuration saved successfully!')

        except Exception as e:
            messagebox.showerror('Save Error', str(e))

    def _import_configuration(self):
        """
        Import configuration from a JSON file.
        """
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title='Import Configuration',
                filetypes=[('JSON files', '*.json')]
            )

            if not file_path:
                return

            # Load configuration from file
            with open(file_path, 'r') as config_file:
                imported_config = json.load(config_file)

            # Update current configuration
            self.current_config.update(imported_config)

            # Rebuild configuration editor
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    for child in config_frame.winfo_children():
                        child.destroy()
                    self._create_config_editor(config_frame)

            messagebox.showinfo('Import', 'Configuration imported successfully!')

        except Exception as e:
            messagebox.showerror('Import Error', str(e))

    def _export_configuration(self):
        """
        Export current configuration to a JSON file.
        """
        try:
            # Open save dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension='.json',
                filetypes=[('JSON files', '*.json')]
            )

            if not file_path:
                return

            # Collect current configuration values
            export_config = {}
            for key, var in self.config_entries.items():
                if isinstance(var, tk.BooleanVar):
                    export_config[key] = var.get()
                elif isinstance(var, tk.StringVar):
                    try:
                        value = var.get()
                        # Try to convert to appropriate type
                        if value.isdigit():
                            export_config[key] = int(value)
                        elif '.' in value:
                            export_config[key] = float(value)
                        else:
                            export_config[key] = value
                    except ValueError:
                        export_config[key] = var.get()

            # Save to file
            with open(file_path, 'w') as config_file:
                json.dump(export_config, config_file, indent=4)

            messagebox.showinfo('Export', 'Configuration exported successfully!')

        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def _update_performance_metrics(self, text_widget):
        """
        Update performance metrics display.

        Args:
            text_widget: Text widget to update with metrics
        """
        try:
            # Enable editing, clear content
            text_widget.config(state=tk.NORMAL)
            text_widget.delete('1.0', tk.END)

            # Get updated report and display
            report = PERFORMANCE_TRACKER.generate_performance_report()
            text_widget.insert(tk.END, report)

            # Disable editing
            text_widget.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror('Metrics Update Error', str(e))

    def _open_nested_config_editor(self, key, nested_config):
        """
        Open a nested configuration editor.

        Args:
            key: Key for the nested configuration
            nested_config: Nested configuration dictionary
        """
        # Create new window
        nested_window = tk.Toplevel(self)
        nested_window.title(f'Nested Configuration: {key}')
        nested_window.geometry('500x400')

        nested_entries = {}

        # Create entries for each nested config item
        for nested_key, nested_value in nested_config.items():
            entry_frame = ttk.Frame(nested_window)
            entry_frame.pack(fill=tk.X, pady=2)
            ttk.Label(entry_frame, text=nested_key, width=30).pack(side=tk.LEFT, padx=5)

            if isinstance(nested_value, (int, float, str)):
                var = tk.StringVar(value=str(nested_value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                nested_entries[nested_key] = var

        # Define save function for nested config
        def save_nested_config():
            updated_nested_config = {}
            for nested_key, var in nested_entries.items():
                try:
                    value = var.get()
                    # Try to convert to appropriate type
                    if value.isdigit():
                        updated_nested_config[nested_key] = int(value)
                    elif '.' in value:
                        updated_nested_config[nested_key] = float(value)
                    else:
                        updated_nested_config[nested_key] = value
                except ValueError:
                    updated_nested_config[nested_key] = var.get()

            self.current_config[key].update(updated_nested_config)
            nested_window.destroy()

        # Add save button
        save_btn = ttk.Button(
            nested_window,
            text='Save Nested Configuration',
            command=save_nested_config
        )
        save_btn.pack(pady=10)


def run_config_management():
    """
    Run the configuration management application.
    """
    app = ConfigManagementUI()
    app.mainloop()


if __name__ == '__main__':
    run_config_management()