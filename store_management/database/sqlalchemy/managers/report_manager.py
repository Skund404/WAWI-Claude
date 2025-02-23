# report_manager.py
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import pdfkit
from typing import List, Dict, Any, Optional


class ReportManager(BaseManager):
    def __init__(self, session: Session):
        super().__init__(session)
        self.report_types = {
            'inventory': self.generate_inventory_report,
            'products': self.generate_products_report,
            'low_stock': self.generate_low_stock_report,
            'recipe_usage': self.generate_recipe_usage_report
        }

    def generate_report(self, report_type: str, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Generate a report based on type and optional filters."""
        if report_type not in self.report_types:
            raise ValueError(f"Unsupported report type: {report_type}")

        return self.report_types[report_type](filters)

    def generate_inventory_report(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Generate inventory report with current stock levels."""
        query = self.session.query(
            Storage.id,
            Storage.bin,
            Product.name.label('product_name'),
            Product.unique_id.label('product_id'),
            Storage.amount,
            Storage.warning_threshold,
            Storage.notes
        ).join(Product)

        if filters:
            if 'bin' in filters:
                query = query.filter(Storage.bin.ilike(f"%{filters['bin']}%"))
            if 'min_amount' in filters:
                query = query.filter(Storage.amount >= filters['min_amount'])
            if 'max_amount' in filters:
                query = query.filter(Storage.amount <= filters['max_amount'])
            if 'product_name' in filters:
                query = query.filter(Product.name.ilike(f"%{filters['product_name']}%"))

        result = query.all()
        return pd.DataFrame([dict(row) for row in result])

    def generate_products_report(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Generate products report with recipe relationships."""
        query = self.session.query(
            Product.id,
            Product.unique_id,
            Product.name,
            Project.name.label('recipe_name'),
            Storage.amount.label('current_stock'),
            Storage.warning_threshold
        ).outerjoin(Project).outerjoin(Storage)

        if filters:
            if 'product_name' in filters:
                query = query.filter(Product.name.ilike(f"%{filters['product_name']}%"))
            if 'recipe_name' in filters:
                query = query.filter(Project.name.ilike(f"%{filters['recipe_name']}%"))

        result = query.all()
        return pd.DataFrame([dict(row) for row in result])

    def generate_low_stock_report(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Generate report for items with stock below warning threshold."""
        query = self.session.query(
            Storage.id,
            Product.name.label('product_name'),
            Product.unique_id.label('product_id'),
            Storage.amount,
            Storage.warning_threshold,
            Storage.bin,
            Storage.notes
        ).join(Product).filter(Storage.amount <= Storage.warning_threshold)

        if filters:
            if 'min_threshold' in filters:
                query = query.filter(Storage.warning_threshold >= filters['min_threshold'])

        result = query.all()
        return pd.DataFrame([dict(row) for row in result])

    def generate_recipe_usage_report(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Generate report showing recipe usage in products."""
        query = self.session.query(
            Project.id,
            Project.name.label('recipe_name'),
            func.count(Product.id).label('product_count'),
            func.sum(Storage.amount).label('total_stock')
        ).outerjoin(Product).outerjoin(Storage).group_by(Project.id)

        if filters:
            if 'recipe_name' in filters:
                query = query.filter(Project.name.ilike(f"%{filters['recipe_name']}%"))

        result = query.all()
        return pd.DataFrame([dict(row) for row in result])

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """Export report to CSV format."""
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_path, index=False)
        return output_path

    def export_to_excel(self, df: pd.DataFrame, filename: str) -> str:
        """Export report to Excel format with formatting."""
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')

            workbook = writer.book
            worksheet = writer.sheets['Report']

            # Apply formatting
            header_format = {
                'font': {'bold': True},
                'fill': {'fgColor': 'D3D3D3'},
                'border': {'outline': True}
            }

            for col in range(len(df.columns)):
                cell = worksheet.cell(row=1, column=col + 1)
                cell.font = workbook.add_format(header_format['font'])
                cell.fill = workbook.add_format(header_format['fill'])
                cell.border = workbook.add_format(header_format['border'])

                # Auto-adjust column width
                worksheet.column_dimensions[chr(65 + col)].auto_size = True

        return output_path

    def export_to_pdf(self, df: pd.DataFrame, filename: str) -> str:
        """Export report to PDF format via HTML conversion."""
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Convert DataFrame to HTML with styling
        html_content = f"""
        <html>
            <head>
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th {{ background-color: #f2f2f2; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h1>{filename} Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {df.to_html(index=False)}
            </body>
        </html>
        """

        # Convert HTML to PDF
        pdfkit.from_string(html_content, output_path)
        return output_path


# report_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, Any


class ReportDialog(BaseDialog):
    def __init__(self, parent, title="Generate Report", **kwargs):
        super().__init__(parent, title, **kwargs)
        self.report_manager = ReportManager(self.session)
        self.setup_ui()

    def setup_ui(self):
        """Setup the report dialog UI components."""
        # Report Type Selection
        report_frame = ttk.LabelFrame(self, text="Report Options")
        report_frame.pack(padx=5, pady=5, fill=tk.X)

        ttk.Label(report_frame, text="Report Type:").pack(pady=5)
        self.report_type = ttk.Combobox(
            report_frame,
            values=list(self.report_manager.report_types.keys()),
            state="readonly"
        )
        self.report_type.pack(pady=5)
        self.report_type.bind('<<ComboboxSelected>>', self.on_report_type_change)

        # Filters Frame
        self.filters_frame = ttk.LabelFrame(self, text="Filters")
        self.filters_frame.pack(padx=5, pady=5, fill=tk.X)

        # Export Options
        export_frame = ttk.LabelFrame(self, text="Export Options")
        export_frame.pack(padx=5, pady=5, fill=tk.X)

        self.export_format = ttk.Combobox(
            export_frame,
            values=['CSV', 'Excel', 'PDF'],
            state="readonly"
        )
        self.export_format.set('Excel')
        self.export_format.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Generate",
            command=self.generate_report
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_report_type_change(self, event=None):
        """Update filters based on selected report type."""
        # Clear existing filters
        for widget in self.filters_frame.winfo_children():
            widget.destroy()

        report_type = self.report_type.get()
        self.filter_widgets = {}

        if report_type == 'inventory':
            self._add_filter('bin', 'Storage Bin:', widget_type='entry')
            self._add_filter('product_name', 'Product Name:', widget_type='entry')
            self._add_filter('min_amount', 'Min Amount:', widget_type='entry')
            self._add_filter('max_amount', 'Max Amount:', widget_type='entry')

        elif report_type == 'products':
            self._add_filter('product_name', 'Product Name:', widget_type='entry')
            self._add_filter('recipe_name', 'Project Name:', widget_type='entry')

        elif report_type == 'low_stock':
            self._add_filter('min_threshold', 'Min Threshold:', widget_type='entry')

        elif report_type == 'recipe_usage':
            self._add_filter('recipe_name', 'Project Name:', widget_type='entry')

    def _add_filter(self, name: str, label: str, widget_type: str, **kwargs):
        """Add a filter widget to the filters frame."""
        frame = ttk.Frame(self.filters_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=5)

        if widget_type == 'entry':
            widget = ttk.Entry(frame)
        elif widget_type == 'combobox':
            widget = ttk.Combobox(frame, values=kwargs.get('values', []), state='readonly')

        widget.pack(side=tk.LEFT, padx=5)
        self.filter_widgets[name] = widget

    def get_filters(self) -> Dict[str, Any]:
        """Get current filter values."""
        filters = {}
        for name, widget in self.filter_widgets.items():
            value = widget.get()
            if value:
                if name in ('min_amount', 'max_amount', 'min_threshold'):
                    try:
                        filters[name] = int(value)
                    except ValueError:
                        messagebox.showerror(
                            "Error",
                            f"Invalid value for {name}. Please enter a number."
                        )
                        return None
                else:
                    filters[name] = value
        return filters

    def generate_report(self):
        """Generate and export the selected report."""
        try:
            report_type = self.report_type.get()
            filters = self.get_filters()

            if filters is None:  # Validation failed
                return

            # Generate report data
            df = self.report_manager.generate_report(report_type, filters)

            # Export based on selected format
            export_format = self.export_format.get()
            filename = f"{report_type}_report"

            if export_format == 'CSV':
                output_path = self.report_manager.export_to_csv(df, filename)
            elif export_format == 'Excel':
                output_path = self.report_manager.export_to_excel(df, filename)
            else:  # PDF
                output_path = self.report_manager.export_to_pdf(df, filename)

            messagebox.showinfo(
                "Success",
                f"Report generated successfully!\nSaved to: {output_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to generate report: {str(e)}"
            )