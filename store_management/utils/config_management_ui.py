from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
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

    @inject(MaterialService)
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

        @inject(MaterialService)
            def _create_main_layout(self):
        """
        Create the main layout for the configuration management UI.
        """
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        env_frame = ttk.Frame(main_frame)
        env_frame.pack(fill=tk.X, pady=5)
        ttk.Label(env_frame, text='Environment:').pack(side=tk.LEFT)
        env_selector = ttk.Combobox(env_frame, textvariable=self.
                                    current_environment, values=['development', 'production',
                                                                 'testing'], state='readonly')
        env_selector.pack(side=tk.LEFT, padx=5)
        env_selector.bind('<<ComboboxSelected>>', self._on_environment_change)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text='Configuration')
        self._create_config_editor(config_frame)
        metrics_frame = ttk.Frame(notebook)
        notebook.add(metrics_frame, text='Performance Metrics')
        self._create_performance_metrics(metrics_frame)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_frame, text='Save Configuration', command=self.
                   _save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text='Import Configuration', command=self.
                   _import_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text='Export Configuration', command=self.
                   _export_configuration).pack(side=tk.LEFT, padx=5)

        @inject(MaterialService)
            def _create_config_editor(self, parent):
        """
        Create the configuration editor section.

        Args:
            parent (tk.Frame): Parent frame for the configuration editor
        """
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas
                                  .yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.config_entries.clear()
        for key, value in self.current_config.items():
            entry_frame = ttk.Frame(scrollable_frame)
            entry_frame.pack(fill=tk.X, pady=2)
            ttk.Label(entry_frame, text=key, width=30).pack(side=tk.LEFT,
                                                            padx=5)
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                entry = ttk.Checkbutton(
                    entry_frame, variable=var, onvalue=True, offvalue=False)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, (int, float)):
                var = tk.StringVar(value=str(value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=20)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, str):
                var = tk.StringVar(value=value)
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = var
            elif isinstance(value, dict):
                entry = ttk.Button(entry_frame, text='Edit Nested Config',
                                   command=lambda k=key: self._open_nested_config_editor(k,
                                                                                         value))
                entry.pack(side=tk.LEFT, padx=5)
                self.config_entries[key] = entry

        @inject(MaterialService)
            def _create_performance_metrics(self, parent):
        """
        Create the performance metrics display section.

        Args:
            parent (tk.Frame): Parent frame for performance metrics
        """
        metrics_text = tk.Text(parent, wrap=tk.WORD, height=20)
        metrics_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        report = PERFORMANCE_TRACKER.generate_performance_report()
        metrics_text.insert(tk.END, report)
        metrics_text.config(state=tk.DISABLED)
        refresh_btn = ttk.Button(parent, text='Refresh Metrics',
                                 command=lambda: self._update_performance_metrics(metrics_text))
        refresh_btn.pack(pady=5)

        @inject(MaterialService)
            def _load_initial_configuration(self):
        """
        Load initial configuration for the selected environment.
        """
        try:
            self.current_config = CONFIG_TRACKER.load_environment_config(self
                                                                         .current_environment.get())
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    for child in config_frame.winfo_children():
                        child.destroy()
                    self._create_config_editor(config_frame)
        except Exception as e:
            messagebox.showerror('Configuration Load Error', str(e))

        @inject(MaterialService)
            def _on_environment_change(self, event=None):
        """
        Handle environment selection change.
        """
        self._load_initial_configuration()

        @inject(MaterialService)
            def _save_configuration(self):
        """
        Save the current configuration.
        """
        try:
            updated_config = {}
            for key, var in self.config_entries.items():
                if isinstance(var, tk.BooleanVar):
                    updated_config[key] = var.get()
                elif isinstance(var, tk.StringVar):
                    try:
                        value = var.get()
                        updated_config[key] = int(value) if value.isdigit(
                        ) else float(value) if '.' in value else value
                    except ValueError:
                        updated_config[key] = var.get()
            env = self.current_environment.get()
            config_filename = f'config.{env}.json'
            config_path = os.path.join(CONFIG_TRACKER.base_config_dir,
                                       config_filename)
            with open(config_path, 'w') as config_file:
                json.dump(updated_config, config_file, indent=4)
            CONFIG_TRACKER.save_config_snapshot(updated_config, env)
            messagebox.showinfo('Configuration',
                                'Configuration saved successfully!')
        except Exception as e:
            messagebox.showerror('Save Error', str(e))

        @inject(MaterialService)
            def _import_configuration(self):
        """
        Import configuration from a JSON file.
        """
        try:
            file_path = filedialog.askopenfilename(
                title='Import Configuration', filetypes=[('JSON files', '*.json')])
            if not file_path:
                return
            with open(file_path, 'r') as config_file:
                imported_config = json.load(config_file)
            self.current_config.update(imported_config)
            for widget in self.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    config_frame = widget.winfo_children()[0]
                    for child in config_frame.winfo_children():
                        child.destroy()
                    self._create_config_editor(config_frame)
            messagebox.showinfo('Import',
                                'Configuration imported successfully!')
        except Exception as e:
            messagebox.showerror('Import Error', str(e))

        @inject(MaterialService)
            def _export_configuration(self):
        """
        Export current configuration to a JSON file.
        """
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension='.json', filetypes=[('JSON files', '*.json')])
            if not file_path:
                return
            export_config = {}
            for key, var in self.config_entries.items():
                if isinstance(var, tk.BooleanVar):
                    export_config[key] = var.get()
                elif isinstance(var, tk.StringVar):
                    try:
                        value = var.get()
                        export_config[key] = int(value) if value.isdigit(
                        ) else float(value) if '.' in value else value
                    except ValueError:
                        export_config[key] = var.get()
            with open(file_path, 'w') as config_file:
                json.dump(export_config, config_file, indent=4)
            messagebox.showinfo('Export',
                                'Configuration exported successfully!')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

        @inject(MaterialService)
            def _update_performance_metrics(self, text_widget):
        """
        Update performance metrics display.

        Args:
            text_widget (tk.Text): Text widget to update with metrics
        """
        try:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete('1.0', tk.END)
            report = PERFORMANCE_TRACKER.generate_performance_report()
            text_widget.insert(tk.END, report)
            text_widget.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror('Metrics Update Error', str(e))

        @inject(MaterialService)
            def _open_nested_config_editor(self, key, nested_config):
        """
        Open a nested configuration editor.

        Args:
            key (str): Key for the nested configuration
            nested_config (dict): Nested configuration dictionary
        """
        nested_window = tk.Toplevel(self)
        nested_window.title(f'Nested Configuration: {key}')
        nested_window.geometry('500x400')
        nested_entries = {}
        for nested_key, nested_value in nested_config.items():
            entry_frame = ttk.Frame(nested_window)
            entry_frame.pack(fill=tk.X, pady=2)
            ttk.Label(entry_frame, text=nested_key, width=30).pack(side=tk.
                                                                   LEFT, padx=5)
            if isinstance(nested_value, (int, float, str)):
                var = tk.StringVar(value=str(nested_value))
                entry = ttk.Entry(entry_frame, textvariable=var, width=40)
                entry.pack(side=tk.LEFT, padx=5)
                nested_entries[nested_key] = var

        def save_nested_config():
            updated_nested_config = {}
            for nested_key, var in nested_entries.items():
                try:
                    value = var.get()
                    updated_nested_config[nested_key] = int(value
                                                            ) if value.isdigit() else float(value
                                                                                            ) if '.' in value else value
                except ValueError:
                    updated_nested_config[nested_key] = var.get()
            self.current_config[key].update(updated_nested_config)
            nested_window.destroy()
        save_btn = ttk.Button(
            nested_window, text='Save Nested Configuration', command=save_nested_config)
        save_btn.pack(pady=10)


def run_config_management():
    """
    Run the configuration management application.
    """
    app = ConfigManagementUI()
    app.mainloop()


if __name__ == '__main__':
    run_config_management()
