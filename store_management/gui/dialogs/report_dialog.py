from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = get_logger(__name__)


class ReportDialog(BaseDialog):

        @inject(MaterialService)
            def __init__(self, parent):
        super().__init__(parent, title='Generate Reports', size=(800, 600),
            modal=True)
        self.report_manager = ReportManager(get_session)
        self.current_report = None
        self.create_ui()

        @inject(MaterialService)
            def create_ui(self):
        """Create the report dialog UI"""
        left_panel = ttk.Frame(self.main_frame)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        ttk.Label(left_panel, text='Report Type:').pack(fill='x', pady=(0, 5))
        self.report_type = tk.StringVar(value='inventory')
        report_types = [('Inventory Report', 'inventory'), ('Orders Report',
            'orders'), ('Suppliers Report', 'suppliers')]
        for text, value in report_types:
            ttk.Radiobutton(left_panel, text=text, value=value, variable=self.report_type,
                            command=self.on_report_type_change).pack(fill='x', pady=2)
        ttk.Separator(left_panel, orient='horizontal').pack(fill='x', pady=10)
        self.options_frame = ttk.LabelFrame(left_panel, text='Options')
        self.options_frame.pack(fill='x', pady=5)
        self.date_range = tk.StringVar(value='last_30_days')
        self.date_range_frame = ttk.Frame(self.options_frame)
        ttk.Label(self.date_range_frame, text='Date Range:').pack(fill='x')
        date_ranges = [('Last 30 days', 'last_30_days'), ('Last 90 days',
            'last_90_days'), ('Last year', 'last_year'), ('All time',
            'all_time')]
        for text, value in date_ranges:
            ttk.Radiobutton(self.date_range_frame, text=text, value=value,
                variable=self.date_range).pack(fill='x', pady=2)
        self.detail_level = tk.StringVar(value='summary')
        self.detail_frame = ttk.Frame(self.options_frame)
        ttk.Label(self.detail_frame, text='Detail Level:').pack(fill='x')
        detail_levels = [('Summary', 'summary'), ('Detailed', 'detailed'),
            ('Full', 'full')]
        for text, value in detail_levels:
            ttk.Radiobutton(self.detail_frame, text=text, value=value,
                variable=self.detail_level).pack(fill='x', pady=2)
        self.update_options()
        ttk.Button(left_panel, text='Generate Report', command=self.
            generate_report).pack(fill='x', pady=10)
        export_frame = ttk.LabelFrame(left_panel, text='Export')
        export_frame.pack(fill='x', pady=5)
        ttk.Button(export_frame, text='Export as CSV', command=self.export_csv
            ).pack(fill='x', pady=2)
        ttk.Button(export_frame, text='Export as Excel', command=self.
            export_excel).pack(fill='x', pady=2)
        ttk.Button(export_frame, text='Export as PDF', command=self.export_pdf
            ).pack(fill='x', pady=2)
        right_panel = ttk.Frame(self.main_frame)
        right_panel.pack(side='left', fill='both', expand=True)
        self.create_report_display(right_panel)

        @inject(MaterialService)
            def create_report_display(self, parent):
        """Create the report display area"""
        display_frame = ttk.LabelFrame(parent, text='Report')
        display_frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(display_frame)
        scrollbar = ttk.Scrollbar(
            display_frame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.report_frame = ttk.Frame(self.canvas)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.
            report_frame, anchor='nw')
        self.canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        display_frame.grid_columnconfigure(0, weight=1)
        display_frame.grid_rowconfigure(0, weight=1)
        self.report_frame.bind('<Configure>', lambda e: self.canvas.
            configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(
            self.canvas_frame, width=e.width))

        @inject(MaterialService)
            def update_options(self):
        """Update visible options based on report type"""
        for widget in self.options_frame.winfo_children():
            widget.pack_forget()
        if self.report_type.get() == 'orders':
            self.date_range_frame.pack(fill='x', pady=5)
            self.detail_frame.pack(fill='x', pady=5)
        else:
            self.detail_frame.pack(fill='x', pady=5)

        @inject(MaterialService)
            def on_report_type_change(self):
        """Handle report type change"""
        self.update_options()
        if self.current_report:
            self.generate_report()

        @inject(MaterialService)
            def generate_report(self):
        """Generate the selected report"""
        try:
            for widget in self.report_frame.winfo_children():
                widget.destroy()
            params = {'report_type': self.report_type.get(), 'detail_level':
                self.detail_level.get()}
            if self.report_type.get() == 'orders':
                params['date_range'] = self.date_range.get()
            self.current_report = self.report_manager.generate_report(params)
            ttk.Label(self.report_frame, text=f"{params['report_type'].title()} Report", font=('', 14,
                'bold')).pack(fill='x', pady=10)
            ttk.Label(self.report_frame, text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ).pack(fill='x')
            ttk.Separator(self.report_frame, orient='horizontal').pack(
                fill='x', pady=10)
            if params['report_type'] == 'inventory':
                self.display_inventory_report()
            elif params['report_type'] == 'orders':
                self.display_orders_report()
            elif params['report_type'] == 'suppliers':
                self.display_suppliers_report()
        except Exception as e:
            logger.error(f'Failed to generate report: {str(e)}')
            messagebox.showerror('Error',
                f'Failed to generate report: {str(e)}')

        @inject(MaterialService)
            def display_inventory_report(self):
        """Display inventory report"""
        report = self.current_report
        shelf_frame = ttk.LabelFrame(self.report_frame, text='Shelf Inventory')
        shelf_frame.pack(fill='x', pady=5)
        columns = ['Type', 'Count', 'Total Area', 'Color Count']
        tree = self.create_treeview(shelf_frame, columns, report['sections'
            ]['shelf']['summary'])
        tree.pack(fill='x', pady=5)
        if report['sections']['shelf']['low_stock']:
            ttk.Label(shelf_frame, text='Low Stock Items:', font=('', 10,
                'bold')).pack(fill='x', pady=5)
            columns = ['Name', 'Type', 'Color', 'Amount']
            tree = self.create_treeview(shelf_frame, columns, report[
                'sections']['shelf']['low_stock'])
            tree.pack(fill='x', pady=5)
        parts_frame = ttk.LabelFrame(self.report_frame, text='Parts Inventory')
        parts_frame.pack(fill='x', pady=5)
        columns = ['Bin', 'Count', 'Total Stock']
        tree = self.create_treeview(parts_frame, columns, report['sections'
            ]['parts']['summary'])
        tree.pack(fill='x', pady=5)
        if report['sections']['parts']['low_stock']:
            ttk.Label(parts_frame, text='Low Stock Parts:', font=('', 10,
                'bold')).pack(fill='x', pady=5)
            columns = ['Name', 'Color', 'In Storage', 'Bin']
            tree = self.create_treeview(parts_frame, columns, report[
                'sections']['parts']['low_stock'])
            tree.pack(fill='x', pady=5)

        @inject(MaterialService)
            def display_orders_report(self):
        """Display orders report"""
        report = self.current_report
        summary_frame = ttk.LabelFrame(
            self.report_frame, text='Order Status Summary')
        summary_frame.pack(fill='x', pady=5)
        columns = ['Status', 'Count', 'Paid Count']
        tree = self.create_treeview(summary_frame, columns, report[
            'sections']['status_summary'])
        tree.pack(fill='x', pady=5)
        recent_frame = ttk.LabelFrame(self.report_frame, text='Recent Orders')
        recent_frame.pack(fill='x', pady=5)
        columns = ['Supplier', 'Date', 'Status', 'Order Number', 'Paid']
        tree = self.create_treeview(recent_frame, columns, report[
            'sections']['recent_orders'])
        tree.pack(fill='x', pady=5)
        if report['sections']['pending_payments']:
            pending_frame = ttk.LabelFrame(
                self.report_frame, text='Pending Payments')
            pending_frame.pack(fill='x', pady=5)
            columns = ['Supplier', 'Date', 'Order Number']
            tree = self.create_treeview(pending_frame, columns, report[
                'sections']['pending_payments'])
            tree.pack(fill='x', pady=5)

        @inject(MaterialService)
            def display_suppliers_report(self):
        """Display suppliers report"""
        report = self.current_report
        summary_frame = ttk.LabelFrame(
            self.report_frame, text='Supplier Summary')
        summary_frame.pack(fill='x', pady=5)
        summary = report['sections']['summary']
        ttk.Label(summary_frame, text=f"Total Suppliers: {summary['total']}"
            ).pack(fill='x')
        ttk.Label(summary_frame, text=f"Countries: {summary['countries']}"
            ).pack(fill='x')
        ttk.Label(summary_frame, text=f"Currencies: {summary['currencies']}"
            ).pack(fill='x')
        orders_frame = ttk.LabelFrame(
            self.report_frame, text='Orders by Supplier')
        orders_frame.pack(fill='x', pady=5)
        columns = ['Company Name', 'Order Count', 'Last Order']
        tree = self.create_treeview(orders_frame, columns, report[
            'sections']['supplier_orders'])
        tree.pack(fill='x', pady=5)
        terms_frame = ttk.LabelFrame(
            self.report_frame, text='Payment Terms Analysis')
        terms_frame.pack(fill='x', pady=5)
        columns = ['Payment Terms', 'Supplier Count']
        tree = self.create_treeview(terms_frame, columns, report['sections'
            ]['payment_terms'])
        tree.pack(fill='x', pady=5)

        @inject(MaterialService)
            def create_treeview(self, parent, columns: List[str], data: List[tuple]
        ) -> ttk.Treeview:
        """Create a treeview with given columns and data"""
        tree = ttk.Treeview(parent, columns=columns, show='headings',
            height=min(len(data), 10))
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        for row in data:
            tree.insert('', 'end', values=row)
        return tree

        @inject(MaterialService)
            def export_csv(self):
            """Export current report as CSV"""
            if not self.current_report:
                messagebox.showwarning('Warning',
                    'Please generate a report first')
                return
            try:
                file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv'), ('All files',
                    '*.*')], initialfile=f"{self.report_type.get()}_report_{datetime.now().strftime('%Y%m%d')}"
                    )
                if not file_path:
                    return
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    report_type = self.report_type.get()
                    writer.writerow(['Report Type:', report_type.title()])
                    writer.writerow(['Generated:', datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S')])
                    writer.writerow([])
                    if report_type == 'inventory':
                        self._export_inventory_csv(writer)
                    elif report_type == 'orders':
                        self._export_orders_csv(writer)
                    elif report_type == 'suppliers':
                        self._export_suppliers_csv(writer)
                messagebox.showinfo('Success', 'Report exported successfully')
            except Exception as e:
                logger.error(f'Failed to export report as CSV: {str(e)}')
                messagebox.showerror('Error',
                    f'Failed to export report: {str(e)}')

        @inject(MaterialService)
            def _export_inventory_csv(self, writer):
            """Export inventory report to CSV"""
            writer.writerow(['Shelf Inventory'])
            writer.writerow(['Type', 'Count', 'Total Area', 'Color Count'])
            for row in self.current_report['sections']['shelf']['summary']:
                writer.writerow(row)
            writer.writerow([])
            if self.current_report['sections']['shelf']['low_stock']:
                writer.writerow(['Low Stock Shelf Items'])
                writer.writerow(['Name', 'Type', 'Color', 'Amount'])
                for row in self.current_report['sections']['shelf']['low_stock'
                    ]:
                    writer.writerow(row)
                writer.writerow([])
            writer.writerow(['Parts Inventory'])
            writer.writerow(['Bin', 'Count', 'Total Stock'])
            for row in self.current_report['sections']['parts']['summary']:
                writer.writerow(row)
            writer.writerow([])
            if self.current_report['sections']['parts']['low_stock']:
                writer.writerow(['Low Stock Parts'])
                writer.writerow(['Name', 'Color', 'In Storage', 'Bin'])
                for row in self.current_report['sections']['parts']['low_stock'
                    ]:
                    writer.writerow(row)

        @inject(MaterialService)
            def _export_orders_csv(self, writer):
            """Export orders report to CSV"""
            writer.writerow(['Order Status Summary'])
            writer.writerow(['Status', 'Count', 'Paid Count'])
            for row in self.current_report['sections']['status_summary']:
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(['Recent Orders'])
            writer.writerow(['Supplier', 'Date', 'Status', 'Order Number',
                'Paid'])
            for row in self.current_report['sections']['recent_orders']:
                writer.writerow(row)
            writer.writerow([])
            if self.current_report['sections']['pending_payments']:
                writer.writerow(['Pending Payments'])
                writer.writerow(['Supplier', 'Date', 'Order Number'])
                for row in self.current_report['sections']['pending_payments']:
                    writer.writerow(row)

        @inject(MaterialService)
            def _export_suppliers_csv(self, writer):
            """Export suppliers report to CSV"""
            summary = self.current_report['sections']['summary']
            writer.writerow(['Supplier Summary'])
            writer.writerow(['Total Suppliers', summary['total']])
            writer.writerow(['Countries', summary['countries']])
            writer.writerow(['Currencies', summary['currencies']])
            writer.writerow([])
            writer.writerow(['Orders by Supplier'])
            writer.writerow(['Company Name', 'Order Count', 'Last Order'])
            for row in self.current_report['sections']['supplier_orders']:
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(['Payment Terms Analysis'])
            writer.writerow(['Payment Terms', 'Supplier Count'])
            for row in self.current_report['sections']['payment_terms']:
                writer.writerow(row)

        @inject(MaterialService)
            def export_excel(self):
            """Export current report as Excel"""
            if not self.current_report:
                messagebox.showwarning('Warning',
                    'Please generate a report first')
                return
            try:
                file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), (
                    'All files', '*.*')], initialfile=f"{self.report_type.get()}_report_{datetime.now().strftime('%Y%m%d')}"
                    )
                if not file_path:
                    return
                self.report_manager.export_to_excel(self.current_report,
                    file_path)
                messagebox.showinfo('Success', 'Report exported successfully')
            except Exception as e:
                logger.error(f'Failed to export report as Excel: {str(e)}')
                messagebox.showerror('Error',
                    f'Failed to export report: {str(e)}')

        @inject(MaterialService)
            def export_pdf(self):
            """Export current report as PDF"""
            if not self.current_report:
                messagebox.showwarning('Warning',
                    'Please generate a report first')
                return
            try:
                file_path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF files', '*.pdf'), ('All files',
                    '*.*')], initialfile=f"{self.report_type.get()}_report_{datetime.now().strftime('%Y%m%d')}"
                    )
                if not file_path:
                    return
                self.report_manager.export_to_pdf(self.current_report,
                    file_path)
                messagebox.showinfo('Success', 'Report exported successfully')
            except Exception as e:
                logger.error(f'Failed to export report as PDF: {str(e)}')
                messagebox.showerror('Error',
                    f'Failed to export report: {str(e)}')

        @inject(MaterialService)
            def print_report(self):
            """Print current report"""
            if not self.current_report:
                messagebox.showwarning('Warning',
                    'Please generate a report first')
                return
            try:
                dialog = PrintDialog(self, self.current_report)
                self.wait_window(dialog)
            except Exception as e:
                logger.error(f'Failed to print report: {str(e)}')
                messagebox.showerror('Error',
                    f'Failed to print report: {str(e)}')


    class PrintDialog(BaseDialog):
        """Dialog for print preview and printing"""

                @inject(MaterialService)
                    def __init__(self, parent, report_data: Dict):
            super().__init__(parent, title='Print Report', size=(600, 800),
                modal=True)
            self.report_data = report_data
            self.create_ui()

                @inject(MaterialService)
                    def create_ui(self):
            """Create print dialog UI"""
            options_frame = ttk.LabelFrame(self.main_frame, text=
                'Print Options')
            options_frame.pack(fill='x', pady=(0, 10))
            ttk.Label(options_frame, text='Page Size:').grid(row=0, column=
                0, sticky='w')
            self.page_size = tk.StringVar(value='A4')
            ttk.Combobox(options_frame, textvariable=self.page_size, values
                =['A4', 'Letter', 'Legal'], state='readonly').grid(row=0,
                column=1, padx=5)
            ttk.Label(options_frame, text='Orientation:').grid(row=1,
                column=0, sticky='w')
            self.orientation = tk.StringVar(value='portrait')
            ttk.Combobox(options_frame, textvariable=self.orientation,
                values=['Portrait', 'Landscape'], state='readonly').grid(row
                =1, column=1, padx=5)
            ttk.Label(options_frame, text='Include:').grid(row=2, column=0,
                sticky='w')
            self.include_charts = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text='Charts and Graphs',
                variable=self.include_charts).grid(row=2, column=1, sticky='w')
            self.include_details = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text='Detailed Information',
                variable=self.include_details).grid(row=3, column=1, sticky='w'
                )
            options_frame.columnconfigure(1, weight=1)
            preview_frame = ttk.LabelFrame(self.main_frame, text=
                'Print Preview')
            preview_frame.pack(fill='both', expand=True, pady=(0, 10))
            self.preview_canvas = tk.Canvas(preview_frame, bg='white',
                relief='sunken', bd=1)
            self.preview_canvas.pack(fill='both', expand=True, padx=5, pady=5)
            self.add_ok_cancel_buttons('Print', 'Cancel', self.print_report)
            self.page_size.trace('w', lambda *args: self.update_preview())
            self.orientation.trace('w', lambda *args: self.update_preview())
            self.include_charts.trace('w', lambda *args: self.update_preview())
            self.include_details.trace('w', lambda *args: self.update_preview()
                )
            self.update_preview()

                @inject(MaterialService)
                    def update_preview(self):
            """Update print preview"""
            self.preview_canvas.delete('all')
            width = 500
            height = 707 if self.page_size.get() == 'A4' else 647
            if self.orientation.get().lower() == 'landscape':
                width, height = height, width
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            scale = min(canvas_width / width, canvas_height / height)
            self.preview_canvas.create_rectangle(10, 10, width * scale, 
                height * scale, fill='white', outline='gray')

                @inject(MaterialService)
                    def print_report(self):
            """Send report to printer"""
            logger.info('Print functionality to be implemented')
            messagebox.showinfo('Info',
                'Printing will be implemented in a future version')
            self.destroy()
