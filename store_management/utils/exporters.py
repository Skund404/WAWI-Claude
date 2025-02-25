# utils/exporters.py
import csv
import json
import pandas as pd
import xlsxwriter
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class OrderExporter:
    """
    Handler for exporting order data in various formats.

    This class provides static methods to export order data to different
    file formats like CSV, Excel, and JSON.
    """

    @staticmethod
    def export_to_csv(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to CSV format.

        Args:
            data: Dictionary containing order and details data
            filepath: Base path for export files

        Returns:
            Boolean indicating success or failure
        """
        try:
            # Export order header
            order_header = filepath.with_suffix('.order.csv')
            with open(order_header, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data['order'].keys())
                writer.writeheader()
                writer.writerow(data['order'])

            # Export order details if present
            details_file = filepath.with_suffix('.details.csv')
            if data['details']:
                with open(details_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data['details'][0].keys())
                    writer.writeheader()
                    writer.writerows(data['details'])

            return True

        except Exception as e:
            print(f'CSV export error: {str(e)}')
            return False

    @staticmethod
    def export_to_excel(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to Excel format.

        Args:
            data: Dictionary containing order and details data
            filepath: Path for the Excel file

        Returns:
            Boolean indicating success or failure
        """
        try:
            filepath = filepath.with_suffix('.xlsx')
            workbook = xlsxwriter.Workbook(str(filepath))

            # Define formats
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            number_format = workbook.add_format({'num_format': '#,##0.00'})

            # Create order sheet
            order_sheet = workbook.add_worksheet('Order')
            for col, field in enumerate(data['order'].keys()):
                order_sheet.write(0, col, field.replace('_', ' ').title(), header_format)
                value = data['order'][field]

                if field == 'date_of_order':
                    order_sheet.write(1, col, datetime.strptime(value, '%Y-%m-%d'), date_format)
                else:
                    order_sheet.write(1, col, value)

            # Create details sheet if details exist
            if data['details']:
                details_sheet = workbook.add_worksheet('Details')

                # Write headers
                for col, field in enumerate(data['details'][0].keys()):
                    details_sheet.write(0, col, field.replace('_', ' ').title(), header_format)

                # Write data rows
                for row, detail in enumerate(data['details'], 1):
                    for col, (field, value) in enumerate(detail.items()):
                        if field in ['price', 'total']:
                            details_sheet.write(row, col, float(value), number_format)
                        else:
                            details_sheet.write(row, col, value)

            workbook.close()
            return True

        except Exception as e:
            print(f'Excel export error: {str(e)}')
            return False

    @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: Path) -> bool:
        """
        Export order data to JSON format (backup).

        Args:
            data: Dictionary containing order and details data
            filepath: Path for the JSON file

        Returns:
            Boolean indicating success or failure
        """
        try:
            filepath = filepath.with_suffix('.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True

        except Exception as e:
            print(f'JSON export error: {str(e)}')
            return False


class OrderImporter:
    """
    Handler for importing order data from various formats.

    This class provides static methods to import order data from different
    file formats like CSV, Excel, and JSON.
    """

    @staticmethod
    def import_from_csv(order_file: Path, details_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Import order data from CSV files.

        Args:
            order_file: Path to the order CSV file
            details_file: Optional path to the details CSV file

        Returns:
            Dictionary containing imported order and details data
        """
        try:
            # Import order data
            with open(order_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                order_data = next(reader)

            # Import details data if available
            details_data = []
            if details_file and details_file.exists():
                with open(details_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    details_data = list(reader)

            return {'order': order_data, 'details': details_data}

        except Exception as e:
            print(f'CSV import error: {str(e)}')
            return {}

    @staticmethod
    def import_from_excel(filepath: Path) -> Dict[str, Any]:
        """
        Import order data from Excel file.

        Args:
            filepath: Path to the Excel file

        Returns:
            Dictionary containing imported order and details data
        """
        try:
            xl = pd.ExcelFile(filepath)

            # Import order data
            order_df = pd.read_excel(xl, 'Order')
            order_data = order_df.iloc[0].to_dict()

            # Import details data if available
            details_data = []
            if 'Details' in xl.sheet_names:
                details_df = pd.read_excel(xl, 'Details')
                details_data = details_df.to_dict('records')

            return {'order': order_data, 'details': details_data}

        except Exception as e:
            print(f'Excel import error: {str(e)}')
            return {}

    @staticmethod
    def import_from_json(filepath: Path) -> Dict[str, Any]:
        """
        Import order data from JSON backup.

        Args:
            filepath: Path to the JSON file

        Returns:
            Dictionary containing imported order and details data
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data

        except Exception as e:
            print(f'JSON import error: {str(e)}')
            return {}