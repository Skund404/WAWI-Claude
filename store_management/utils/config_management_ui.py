# gui/config_management_ui.py
"""
Configuration Management User Interface for Store Management System.

Provides a comprehensive GUI for managing system configurations
across different environments.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys

from utils.config_tracker import CONFIG_TRACKER
from utils.performance_tracker import PERFORMANCE_TRACKER


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
        self.title("Store Management Configuration")
        self.geometry("800x600")

        # Current configuration storage
        self.current_config = {}
        self.current_environment = tk.StringVar(value="development")

        # Configuration entry tracking
        self.config_entries = {}

        # Setup UI components
        self._create_main_layout()
        self._load_initial_configuration()

    def _create_main_layout(self):
        """
        Create the main layout for the configuration management UI.
        """
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Environment selection
        env_frame = ttk.Frame(main_frame)
        env_frame.pack(fill=tk.X, pady=5)

        ttk.Label(env_frame, text="Environment:").pack(side=tk.LEFT)
        env_selector = ttk.Combobox(
            env_frame,
            textvariable=self.current_environment,
            values=["development", "production", "testing"],
            state="readonly"
        )
        env_selector.pack(side=tk.LEFT, padx=5)
        env_selector.bind("<<ComboboxSelected>>", self._on_environment_change)

        # Notebook for different config sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Configuration editor tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self._create_config_editor(config_frame)

        # Performance metrics tab
        metrics_frame = ttk.Frame(notebook)
        notebook.add(metrics_frame, text="Performance Metrics")
        self._create_performance_metrics(metrics_frame)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            action_frame,
            text="Save Configuration",
            command=self._save_configuration
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Import Configuration",
            command=self._import_configuration
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Export Configuration",
            command=self._export_configuration
        ).pack(side=tk.LEFT, padx=5)

    def _create_config_editor(self, parent):
        """
        Create the configuration editor section.

        Args:
            parent (tk.Frame): Parent frame for the configuration editor
        """
        # Scrollable frame for configuration entries
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Clear existing entries
        self.config_entries.clear()

        # Dynamically create configuration entries
        for key, value in self.current_config.items():
            # Create a frame for each configuration entry
            entry_frame = ttk.Frame(scrollable_frame)
            entry_frame.pack(fill=tk.X, pady=2)

            # Label for configuration key
            ttk.Label(entry_frame, text=key, width=30).pack(side=tk.LEFT, padx=5)

            # Input for configuration value
            if isinstance(value, bool):
                # Boolean values use checkbutton
                var = tk.BooleanVar(value=value)
                entry = ttk.Checkbutton(
                    entry_frame,
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, (int, float)):
                # Numeric values use spinbox
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=20)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, str):
                # String values use entry
                var = tk.StringVar(value=value)
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, dict):
                # Nested dictionaries use a button to open a nested editor
                entry = ttk.Button(
                    entry_frame,
                    text="Edit Nested Config",
                    command=lambda k=key: self._open_nested_config_editor(k, value)
                )
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = entry

    def _create_performance_metrics(self, parent):
        """
        Create the performance metrics display section.

        Args:
            parent (tk.Frame): Parent frame for performance metrics
        """
        # Performance report text widget
        metrics_text = tk.Text(parent, wrap=tk.WORD, height=20)
        metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Generate and display performance report
        report = PERFORMANCE_TRACKER.generate_performance_report()
        metrics_text.insert(tk.END, report)
        metrics_text.config(state=tk.DISABLED)

        # Refresh button
        refresh_btn = ttk.Button(
            parent,
            text="Refresh Metrics",
            command=lambda: self._update_performance_metrics(metrics_text)
        )
        refresh_btn.pack(pady=5)

    def _load_initial_configuration(self):
        """
        Load initial configuration for the selected environment.
        """
        try:
            # Load configuration using CONFIG_TRACKER
            self.current_config = CONFIG_TRACKER.load_environment_config(
                self.current_environment.get()
            )

            # Recreate configuration editor with new config
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    # Clear existing widgets
                    for child in config_frame.winfo_children():
                        child.destroy()

                    # Recreate configuration editor
                    self._create_config_editor(config_frame)
        except Exception as e:
            messagebox.showerror("Configuration Load Error", str(e))

    def _on_environment_change(self, event=None):
        """
        Handle environment selection change.
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
                    # Convert to appropriate type
                    try:
                        # Try converting to int or float
                        value = var.get()
                        updated_config[key] = (
                            int(value) if value.isdigit()
                            else float(value) if '.' in value
                            else value
                        )
                    except ValueError:
                        updated_config[key] = var.get()

            # Save configuration
            env = self.current_environment.get()
            config_filename = f'config.{env}.json'
            config_path = os.path.join(
                CONFIG_TRACKER.base_config_dir,
                config_filename
            )

            with open(config_path, 'w') as config_file:
                json.dump(updated_config, config_file, indent=4)

            # Log configuration changes
            CONFIG_TRACKER.save_config_snapshot(updated_config, env)

            messagebox.showinfo("Configuration", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _import_configuration(self):
        """
        Import configuration from a JSON file.
        """
        try:
            # Open file dialog to select configuration file
            file_path = filedialog.askopenfilename(
                title="Import Configuration",
                filetypes=[("JSON files", "*.json")]
            )

            if not file_path:
                return

            # Read and load configuration
            with open(file_path, 'r') as config_file:
                imported_config = json.load(config_file)

            # Update current configuration
            self.current_config.update(imported_config)

            # Recreate configuration editor
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    # Clear existing widgets
                    for child in config_frame.winfo_children():
                        child.destroy()

                    # Recreate configuration editor
                    self._create_config_editor(config_frame)

            messagebox.showinfo("Import", "Configuration imported successfully!")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _export_configuration(self):
        """
        Export current configuration to a JSON file.
        """
        try:
            # Open file dialog to choose export location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")]
            )

            if not file_path:
                return

            # Collect current configuration
            export_config = {}
            for key, var in self.config_entries.items():
                if isinstance(var, tk.BooleanVar):
                    export_config[key] = var.get()
                elif isinstance(var, tk.StringVar):
                    # Convert to appropriate type
                    try:
                        # Try converting to int or float
                        value = var.get()
                        export_config[key] = (
                            int(value) if value.isdigit()
                            else float(value) if '.' in value
                            else value
                        )
                    except ValueError:
                        export_config[key] = var.get()

            # Write to file
            with open(file_path, 'w') as config_file:
                json.dump(export_config, config_file, indent=4)

            messagebox.showinfo("Export", "Configuration exported successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _update_performance_metrics(self, text_widget):
        """
        Update performance metrics display.

        Args:
            text_widget (tk.Text): Text widget to update with metrics
        """
        try:
            # Clear existing text
            text_widget.config(state=tk.NORMAL)
            text_widget.delete('1.0', tk.END)

            # Generate and display new performance report
            report = PERFORMANCE_TRACKER.generate_performance_report()
            text_widget.insert(tk.END, report)
            text_widget.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Metrics Update Error", str(e))

    def _open_nested_config_editor(self, key, nested_config):
        """
        Open a nested configuration editor.

        Args:
            key (str): Key for the nested configuration
            nested_config (dict): Nested configuration dictionary
        """
        # Create a top-level window for nested configuration
        nested_window = tk.Toplevel(self)
        nested_window.title(f"Nested Configuration: {key}")
        nested_window.geometry("500x400")

        # Nested configuration entries
        nested_entries = {}

        for nested_key, nested_value in nested_config.items():
            # Create a frame for each nested configuration entry
            entry_frame = ttk.Frame(nested_window)
            entry_frame.pack(fill=tk.X, pady=2)

            # Label for nested configuration key
            ttk.Label(entry_frame, text=nested_key, width=30).pack(side=tk.LEFT, padx=5)

            # Input for nested configuration value
            if isinstance(nested_value, (int, float, str)):
                var = tk.StringVar(value=str(nested_value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                nested_entries[nested_key] = var

        # Save button for nested configuration
        def save_nested_config():
            updated_nested_config = {}
            for nested_key, var in nested_entries.items():
                try:
                    # Convert to appropriate type
                    value = var.get()
                    updated_nested_config[nested_key] = (
                        int(value) if value.isdigit()
                        else float(value) if '.' in value
                        else value
                    )
                except ValueError:
                    updated_nested_config[nested_key] = var.get()

            # Update main configuration
            self.current_config[key].update(updated_nested_config)
            nested_window.destroy()

        save_btn = ttk.Button(
            nested_window,
            text="Save Nested Configuration",
            command=save_nested_config
        )
        save_btn.pack(pady=10)


def run_config_management():
    """
    Run the configuration management application.
    """
    app = ConfigManagementUI()
    app.mainloop()


if __name__ == "__main__":
    run_config_management()