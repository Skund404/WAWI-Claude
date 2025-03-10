class InventoryReportView(BaseView):
    """View for generating and displaying inventory reports."""

    @inject
    def __init__(self, parent: tk.Widget,
                 analytics_service: IAnalyticsService,
                 inventory_service: IInventoryService):
        """Initialize the inventory report view.

        Args:
            parent: Parent widget
            analytics_service: Analytics service for business metrics
            inventory_service: Inventory service for inventory operations
        """
        self.analytics_service = analytics_service
        self.inventory_service = inventory_service
        super().__init__(parent)

    def initialize_ui(self) -> None:
        """Initialize UI components."""
        # Create main layout
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        # Create title
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        title_label = ttk.Label(title_frame, text="Inventory Reports", font=("Helvetica", 16, "bold"))
        title_label.pack(side=tk.LEFT)

        # Add refresh button
        refresh_btn = ttk.Button(title_frame, text="Refresh", command=self.refresh_reports)
        refresh_btn.pack(side=tk.RIGHT)

        # Create notebook for report sections
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create report sections
        self.value_frame = ttk.Frame(self.notebook)
        self.low_stock_frame = ttk.Frame(self.notebook)
        self.material_usage_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.value_frame, text="Inventory Value")
        self.notebook.add(self.low_stock_frame, text="Low Stock")
        self.notebook.add(self.material_usage_frame, text="Material Usage")

        # Initialize report sections
        self._init_value_section()
        self._init_low_stock_section()
        self._init_material_usage_section()

        # Add export button
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate Orders", command=self.generate_orders).pack(side=tk.LEFT, padx=5)

        # Load data
        self.refresh_reports()

    def _init_value_section(self) -> None:
        """Initialize inventory value section."""
        # Configure grid
        self.value_frame.columnconfigure(0, weight=1)
        self.value_frame.rowconfigure(1, weight=1)

        # Create summary fields
        summary_frame = ttk.Frame(self.value_frame)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        fields = [
            ("Total Inventory Value:", "total_value"),
            ("Material Value:", "material_value"),
            ("Product Value:", "product_value"),
            ("Tool Value:", "tool_value")
        ]

        # Create field variables
        self.value_vars = {}

        # Add fields
        for i, (label_text, key) in enumerate(fields):
            ttk.Label(summary_frame, text=label_text, font=("Helvetica", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=10, pady=5)

            var = tk.StringVar(value="$0.00")
            ttk.Label(summary_frame, textvariable=var).grid(
                row=i, column=1, sticky="w", padx=10, pady=5)

            self.value_vars[key] = var

        # Create material value treeview
        materials_frame = ttk.LabelFrame(self.value_frame, text="Top Materials by Value")
        materials_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        materials_frame.columnconfigure(0, weight=1)
        materials_frame.rowconfigure(0, weight=1)

        columns = ("name", "quantity", "price", "total_value")
        self.materials_tree = ttk.Treeview(materials_frame, columns=columns, show="headings")

        # Configure columns
        self.materials_tree.heading("name", text="Material")
        self.materials_tree.heading("quantity", text="Quantity")
        self.materials_tree.heading("price", text="Price/Unit")
        self.materials_tree.heading("total_value", text="Total Value")

        self.materials_tree.column("name", width=200)
        self.materials_tree.column("quantity", width=100)
        self.materials_tree.column("price", width=100)
        self.materials_tree.column("total_value", width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(materials_frame, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.materials_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _init_low_stock_section(self) -> None:
        """Initialize low stock section."""
        # Configure grid
        self.low_stock_frame.columnconfigure(0, weight=1)
        self.low_stock_frame.rowconfigure(0, weight=1)

        # Create summary frame
        summary_frame = ttk.Frame(self.low_stock_frame)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Create low stock treeview
        treeview_frame = ttk.Frame(self.low_stock_frame)
        treeview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        columns = ("name", "type", "quantity", "status", "supplier")
        self.low_stock_tree = ttk.Treeview(treeview_frame, columns=columns, show="headings")

        # Configure columns
        self.low_stock_tree.heading("name", text="Item")
        self.low_stock_tree.heading("type", text="Type")
        self.low_stock_tree.heading("quantity", text="Quantity")
        self.low_stock_tree.heading("status", text="Status")
        self.low_stock_tree.heading("supplier", text="Supplier")

        self.low_stock_tree.column("name", width=200)
        self.low_stock_tree.column("type", width=100)
        self.low_stock_tree.column("quantity", width=80)
        self.low_stock_tree.column("status", width=100)
        self.low_stock_tree.column("supplier", width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.low_stock_tree.yview)
        self.low_stock_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.low_stock_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _init_material_usage_section(self) -> None:
        """Initialize material usage section."""
        # Configure grid
        self.material_usage_frame.columnconfigure(0, weight=1)
        self.material_usage_frame.rowconfigure(1, weight=1)

        # Create date selection frame
        date_frame = ttk.Frame(self.material_usage_frame)
        date_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Add date selection
        ttk.Label(date_frame, text="Date Range:").pack(side=tk.LEFT, padx=5)

        # Add date range combo
        self.date_range_var = tk.StringVar(value="Last 30 Days")
        date_range_combo = ttk.Combobox(date_frame, textvariable=self.date_range_var, width=15)
        date_range_combo['values'] = ["Last 30 Days", "Last 90 Days", "This Year", "Last Year"]
        date_range_combo.pack(side=tk.LEFT, padx=5)

        # Add generate button
        ttk.Button(date_frame, text="Generate",
                   command=self._generate_material_usage_report).pack(side=tk.LEFT, padx=10)

        # Create material usage treeview
        treeview_frame = ttk.Frame(self.material_usage_frame)
        treeview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        columns = ("material", "total_usage", "projects", "cost")
        self.usage_tree = ttk.Treeview(treeview_frame, columns=columns, show="headings")

        # Configure columns
        self.usage_tree.heading("material", text="Material")
        self.usage_tree.heading("total_usage", text="Total Usage")
        self.usage_tree.heading("projects", text="Projects")
        self.usage_tree.heading("cost", text="Cost")

        self.usage_tree.column("material", width=200)
        self.usage_tree.column("total_usage", width=100)
        self.usage_tree.column("projects", width=100)
        self.usage_tree.column("cost", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.usage_tree.yview)
        self.usage_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.usage_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def refresh_reports(self) -> None:
        """Refresh all report data."""
        # Generate inventory value report
        self._generate_inventory_value_report()

        # Generate low stock report
        self._generate_low_stock_report()

        # Generate material usage report based on current selection
        self._generate_material_usage_report()

    def _generate_inventory_value_report(self) -> None:
        """Generate inventory value report."""
        try:
            # Get inventory value report
            report = self.execute_service_call(
                lambda: self.analytics_service.get_inventory_value_report(),
                error_title="Inventory Report Error"
            )

            if not report:
                return

            # Update summary values
            self.value_vars['total_value'].set(f"${report.get('total_inventory_value', 0):.2f}")
            self.value_vars['material_value'].set(f"${report.get('material_value', 0):.2f}")
            self.value_vars['product_value'].set(f"${report.get('product_value', 0):.2f}")
            self.value_vars['tool_value'].set(f"${report.get('tool_value', 0):.2f}")

            # Clear treeview
            for item in self.materials_tree.get_children():
                self.materials_tree.delete(item)

            # Add material items
            material_items = report.get('material_items', [])
            for item in material_items:
                self.materials_tree.insert('', 'end', values=(
                    item.get('name', 'N/A'),
                    item.get('quantity', 0),
                    f"${item.get('price_per_unit', 0):.2f}",
                    f"${item.get('total_value', 0):.2f}"
                ))

        except Exception as e:
            self.logger.error(f"Error generating inventory value report: {str(e)}")

    def _generate_low_stock_report(self) -> None:
        """Generate low stock report."""
        try:
            # Get low stock report
            report = self.execute_service_call(
                lambda: self.analytics_service.get_low_stock_report(),
                error_title="Low Stock Report Error"
            )

            if not report:
                return

            # Clear treeview
            for item in self.low_stock_tree.get_children():
                self.low_stock_tree.delete(item)

            # Combine low stock and out of stock items
            items = report.get('low_stock_items', []) + report.get('out_of_stock_items', [])

            # Add items to treeview
            for item in items:
                supplier_name = item.get('supplier_name', 'N/A')

                self.low_stock_tree.insert('', 'end', values=(
                    item.get('name', 'N/A'),
                    item.get('material_type', item.get('type', 'N/A')),
                    item.get('quantity', 0),
                    item.get('status', 'N/A'),
                    supplier_name
                ))

        except Exception as e:
            self.logger.error(f"Error generating low stock report: {str(e)}")

    def _generate_material_usage_report(self) -> None:
        """Generate material usage report based on selected date range."""
        try:
            # Determine date range
            range_value = self.date_range_var.get()
            end_date = datetime.now()

            if range_value == "Last 30 Days":
                start_date = end_date - timedelta(days=30)
            elif range_value == "Last 90 Days":
                start_date = end_date - timedelta(days=90)
            elif range_value == "This Year":
                start_date = datetime(end_date.year, 1, 1)
            elif range_value == "Last Year":
                start_date = datetime(end_date.year - 1, 1, 1)
                end_date = datetime(end_date.year - 1, 12, 31, 23, 59, 59)
            else:
                # Default to last 30 days
                start_date = end_date - timedelta(days=30)

            # Get material usage report
            report = self.execute_service_call(
                lambda: self.analytics_service.get_material_usage_report(start_date, end_date),
                error_title="Material Usage Report Error"
            )

            if not report:
                return

            # Clear treeview
            for item in self.usage_tree.get_children():
                self.usage_tree.delete(item)

            # Add material usage data (this is placeholder data until real report is available)
            material_usage = report.get('material_usage', {})
            for material, usage in material_usage.items():
                self.usage_tree.insert('', 'end', values=(
                    material.capitalize(),
                    usage,
                    "N/A",  # Project count (placeholder)
                    "N/A"  # Cost (placeholder)
                ))

        except Exception as e:
            self.logger.error(f"Error generating material usage report: {str(e)}")

    def export_to_csv(self) -> None:
        """Export the current report to CSV."""
        # Determine which report to export based on current tab
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:
            # Inventory value report
            self._export_inventory_value_report()
        elif current_tab == 1:
            # Low stock report
            self._export_low_stock_report()
        elif current_tab == 2:
            # Material usage report
            self._export_material_usage_report()

    def _export_inventory_value_report(self) -> None:
        """Export inventory value report to CSV."""
        try:
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Inventory Value Report"
            )

            if not file_path:
                return

            # Get report data
            report = self.execute_service_call(
                lambda: self.analytics_service.get_inventory_value_report(),
                error_title="Inventory Report Error"
            )

            if not report:
                return

            # Write to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(['Inventory Value Report'])
                writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])

                # Write summary
                writer.writerow(['Summary'])
                writer.writerow(['Total Inventory Value', self.value_vars['total_value'].get()])
                writer.writerow(['Material Value', self.value_vars['material_value'].get()])
                writer.writerow(['Product Value', self.value_vars['product_value'].get()])
                writer.writerow(['Tool Value', self.value_vars['tool_value'].get()])
                writer.writerow([])

                # Write material items
                writer.writerow(['Material Items'])
                writer.writerow(['Name', 'Quantity', 'Price/Unit', 'Total Value'])

                for item in report.get('material_items', []):
                    writer.writerow([
                        item.get('name', 'N/A'),
                        item.get('quantity', 0),
                        f"${item.get('price_per_unit', 0):.2f}",
                        f"${item.get('total_value', 0):.2f}"
                    ])

            messagebox.showinfo("Export Successful", f"Report exported to {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.error(f"Error exporting inventory value report: {str(e)}")
            messagebox.showerror("Export Error", f"Error exporting report: {str(e)}")

    def _export_low_stock_report(self) -> None:
        """Export low stock report to CSV."""
        # Similar implementation to _export_inventory_value_report
        messagebox.showinfo("Export", "Low stock report export would be implemented here")

    def _export_material_usage_report(self) -> None:
        """Export material usage report to CSV."""
        # Similar implementation to _export_inventory_value_report
        messagebox.showinfo("Export", "Material usage report export would be implemented here")

    def generate_orders(self) -> None:
        """Generate purchase orders for low stock items."""
        messagebox.showinfo("Generate Orders",
                            "This would navigate to the generate orders functionality")