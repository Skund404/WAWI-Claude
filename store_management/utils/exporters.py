

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class OrderExporter:
    """Handler for exporting order data"""

        @staticmethod
    def export_to_csv(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to CSV"""
        try:
            order_header = filepath.with_suffix('.order.csv')
            with open(order_header, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data['order'].keys())
                writer.writeheader()
                writer.writerow(data['order'])
            details_file = filepath.with_suffix('.details.csv')
            if data['details']:
                with open(details_file, 'w', newline='', encoding='utf-8'
                    ) as f:
                    writer = csv.DictWriter(f, fieldnames=data['details'][0
                        ].keys())
                    writer.writeheader()
                    writer.writerows(data['details'])
            return True
        except Exception as e:
            print(f'CSV export error: {str(e)}')
            return False

        @staticmethod
    def export_to_excel(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to Excel"""
        try:
            filepath = filepath.with_suffix('.xlsx')
            workbook = xlsxwriter.Workbook(str(filepath))
            header_format = workbook.add_format({'bold': True, 'bg_color':
                '#D3D3D3', 'border': 1})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            number_format = workbook.add_format({'num_format': '#,##0.00'})
            order_sheet = workbook.add_worksheet('Order')
            for col, field in enumerate(data['order'].keys()):
                order_sheet.write(0, col, field.replace('_', ' ').title(),
                    header_format)
                value = data['order'][field]
                if field == 'date_of_order':
                    order_sheet.write(1, col, datetime.strptime(value,
                        '%Y-%m-%d'), date_format)
                else:
                    order_sheet.write(1, col, value)
            if data['details']:
                details_sheet = workbook.add_worksheet('Details')
                for col, field in enumerate(data['details'][0].keys()):
                    details_sheet.write(0, col, field.replace('_', ' ').
                        title(), header_format)
                for row, detail in enumerate(data['details'], 1):
                    for col, (field, value) in enumerate(detail.items()):
                        if field in ['price', 'total']:
                            details_sheet.write(row, col, float(value),
                                number_format)
                        else:
                            details_sheet.write(row, col, value)
            workbook.close()
            return True
        except Exception as e:
            print(f'Excel export error: {str(e)}')
            return False

        @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to JSON (backup)"""
        try:
            filepath = filepath.with_suffix('.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f'JSON export error: {str(e)}')
            return False


class OrderImporter:
    """Handler for importing order data"""

        @staticmethod
    def import_from_csv(order_file: Path, details_file: Optional[Path]=None
        ) ->Dict[str, Any]:
        """Import order data from CSV files"""
        try:
            with open(order_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                order_data = next(reader)
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
    def import_from_excel(filepath: Path) ->Dict[str, Any]:
        """Import order data from Excel file"""
        try:
            xl = pd.ExcelFile(filepath)
            order_df = pd.read_excel(xl, 'Order')
            order_data = order_df.iloc[0].to_dict()
            details_data = []
            if 'Details' in xl.sheet_names:
                details_df = pd.read_excel(xl, 'Details')
                details_data = details_df.to_dict('records')
            return {'order': order_data, 'details': details_data}
        except Exception as e:
            print(f'Excel import error: {str(e)}')
            return {}

        @staticmethod
    def import_from_json(filepath: Path) ->Dict[str, Any]:
        """Import order data from JSON backup"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f'JSON import error: {str(e)}')
            return {}
