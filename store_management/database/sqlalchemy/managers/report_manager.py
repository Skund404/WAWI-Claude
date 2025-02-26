# Path: database/sqlalchemy/managers/report_manager.py

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import pdfkit

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models import Storage, Product, Project
from sqlalchemy import func


class ReportManager:
    """
    Manager class for generating and exporting various types of reports.

    This class provides methods to generate different types of reports,
    such as inventory, products, low stock, and recipe usage reports.
    """

    def __init__(self, session: Session):
        """
        Initialize the ReportManager with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session
        self.report_types = {
            'inventory': self.generate_inventory_report,
            'products': self.generate_products_report,
            'low_stock': self.generate_low_stock_report,
            'recipe_usage': self.generate_recipe_usage_report
        }
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_report(self, report_type: str, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Generate a report based on type and optional filters.

        Args:
            report_type (str): Type of report to generate
            filters (Dict[str, Any], optional): Filters to apply to the report

        Returns:
            pd.DataFrame: DataFrame containing the report data

        Raises:
            ValueError: If an unsupported report type is requested
        """
        if report_type not in self.report_types:
            raise ValueError(f'Unsupported report type: {report_type}')
        return self.report_types[report_type](filters)

    def generate_inventory_report(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Generate inventory report with current stock levels.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filters to apply to the report

        Returns:
            pd.DataFrame: DataFrame with inventory details
        """
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
        """
        Generate products report with pattern relationships.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filters to apply to the report

        Returns:
            pd.DataFrame: DataFrame with product details
        """
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
        """
        Generate report for items with stock below warning threshold.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filters to apply to the report

        Returns:
            pd.DataFrame: DataFrame with low stock items
        """
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
        """
        Generate report showing pattern usage in products.

        Args:
            filters (Optional[Dict[str, Any]], optional): Filters to apply to the report

        Returns:
            pd.DataFrame: DataFrame with recipe usage details
        """
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
        """
        Export report to CSV format.

        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Base filename for the export

        Returns:
            str: Full path to the exported CSV file
        """
        os.makedirs('reports', exist_ok=True)
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_path, index=False)
        self.logger.info(f"Exported report to {output_path}")
        return output_path

    def export_to_excel(self, df: pd.DataFrame, filename: str) -> str:
        """
        Export report to Excel format with formatting.

        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Base filename for the export

        Returns:
            str: Full path to the exported Excel file
        """
        os.makedirs('reports', exist_ok=True)
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook = writer.book
            worksheet = writer.sheets['Report']

            # Apply formatting to header
            for col in range(len(df.columns)):
                cell = worksheet.cell(row=1, column=col + 1)
                cell.font = workbook.add_format({'bold': True})
                cell.fill = workbook.add_format({'bg_color': 'D3D3D3'})
                cell.border = workbook.add_format({'border': 1})

            # Auto-adjust column widths
            for col in range(len(df.columns)):
                worksheet.column_dimensions[chr(65 + col)].auto_size = True

        self.logger.info(f"Exported report to {output_path}")
        return output_path

    def export_to_pdf(self, df: pd.DataFrame, filename: str) -> str:
        """
        Export report to PDF format via HTML conversion.

        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Base filename for the export

        Returns:
            str: Full path to the exported PDF file
        """
        os.makedirs('reports', exist_ok=True)
        output_path = f"reports/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

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
        pdfkit.from_string(html_content, output_path)
        self.logger.info(f"Exported report to {output_path}")
        return output_path


class ReportDialog:
    """
    Dialog for generating and exporting reports with user-friendly interface.
    """

    def __init__(self, parent, session, title='Generate Report', **kwargs):
        """
        Initialize the ReportDialog.

        Args:
            parent: Parent window or widget
            session: Database session
            title (str, optional): Dialog title. Defaults to 'Generate Report'.
        """
        self.parent = parent
        self.session = session
        self.title = title
        self.report_manager = ReportManager(self.session)
        self.setup_ui()

    def setup_ui(self):
        """Setup the report dialog UI components."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)

        # Report Type Selection
        report_frame = ttk.LabelFrame(self.dialog, text='Report Options')
        report_frame.pack(padx=5, pady=5, fill=tk.X)

        ttk.Label(report_frame, text='Report Type:').pack(pady=5)
        self.report_type = ttk.Combobox(
            report_frame,
            values=list(self.report_manager.report_types.keys()),
            state='readonly'
        )
        self.report_type.pack(pady=5)
        self.report_type.bind('<<ComboboxSelected>>', self.on_report_type_change)

        # Filters Frame
        self.filters_frame = ttk.LabelFrame(self.dialog, text='Filters')
        self.filters_frame.pack(padx=5, pady=5, fill=tk.X)

        # Export Options
        export_frame = ttk.LabelFrame(self.dialog, text='Export Options')
        export_frame.pack(padx=5, pady=5, fill=tk.X)

        self.export_format = ttk.Combobox(
            export_frame,
            values=['CSV', 'Excel', 'PDF'],
            state='readonly'
        )
        self.export_format.set('Excel')
        self.export_format.pack(pady=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text='Generate', command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Close', command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

        self.filter_widgets = {}

    def on_report_type_change(self, event=None):
        """
        Update filters based on selected report type.
        """
        # Clear existing filter widgets
        for widget in self.filters_frame.winfo_children():
            widget.destroy()

        report_type = self.report_type.get()
        self.filter_widgets = {}

        # Add specific filters for each report type
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

    def _add_filter(self, name: str, label: str, widget_type: str = 'entry', **kwargs):
        """
        Add a filter widget to the filters frame.

        Args:
            name (str): Name/key of the filter
            label (str): Label text for the filter
            widget_type (str, optional): Type of widget. Defaults to 'entry'.
        """
        frame = ttk.Frame(self.filters_frame)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=5)

        if widget_type == 'entry':
            widget = ttk.Entry(frame)
        elif widget_type == 'combobox':
            widget = ttk.Combobox(
                frame,
                values=kwargs.get('values', []),
                state='readonly'
            )

        widget.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.filter_widgets[name] = widget

        def get_filters(self) -> Optional[Dict[str, Any]]:
            """
            Get current filter values.

            Returns:
                Optional[Dict[str, Any]]: Dictionary of filter values or None
            """
            filters = {}
            for name, widget in self.filter_widgets.items():
                value = widget.get().strip()
                if value:
                    # Convert numeric filter values
                    if name in ('min_amount', 'max_amount', 'min_threshold'):
                        try:
                            filters[name] = int(value)
                        except ValueError:
                            messagebox.showerror(
                                'Error',
                                f'Invalid value for {name}. Please enter a number.'
                            )
                            return None
                    else:
                        filters[name] = value
            return filters if filters else None

        def generate_report(self):
            """
            Generate and export the selected report.

            This method validates the report type and filters, generates the report,
            and exports it to the selected format.
            """
            try:
                # Validate report type
                report_type = self.report_type.get()
                if not report_type:
                    messagebox.showerror('Error', 'Please select a report type.')
                    return

                # Get filters (may be None)
                filters = self.get_filters()

                # Generate report
                df = self.report_manager.generate_report(report_type, filters)

                # Determine export format
                export_format = self.export_format.get()
                filename = f'{report_type}_report'

                # Export based on selected format
                if export_format == 'CSV':
                    output_path = self.report_manager.export_to_csv(df, filename)
                elif export_format == 'Excel':
                    output_path = self.report_manager.export_to_excel(df, filename)
                else:  # PDF
                    output_path = self.report_manager.export_to_pdf(df, filename)

                # Show success message
                messagebox.showinfo(
                    'Success',
                    f"""Report generated successfully!
    Saved to: {output_path}"""
                )

                # Close the dialog after successful export
                self.dialog.destroy()

            except Exception as e:
                # Log the full error for debugging
                logging.exception("Report generation failed")

                # Show user-friendly error message
                messagebox.showerror(
                    'Error',
                    f'Failed to generate report: {str(e)}'
                )

    # Additional imports needed for the entire file
    import logging
    import tkinter as tk
    from tkinter import ttk, messagebox
    import pdfkit
    import os
    from datetime import datetime
    import pandas as pd
    from sqlalchemy import func

    # Ensure logging is configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='reports.log'
    )