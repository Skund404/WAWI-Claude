

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class OrderExporter:

        @staticmethod
    def export_to_excel(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to Excel"""
        try:
            with pd.ExcelWriter(filepath) as writer:
                order_df = pd.DataFrame([data['order']])
                order_df.to_excel(writer, sheet_name='Order', index=False)
                details_df = pd.DataFrame(data['details'])
                details_df.to_excel(writer, sheet_name='Details', index=False)
                workbook = writer.book
                for sheet in writer.sheets.values():
                    for col in range(len(sheet.dimensions)):
                        sheet.column_dimensions[chr(65 + col)].auto_size = True
            return True
        except Exception:
            return False

        @staticmethod
    def export_to_csv(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to CSV"""
        try:
            order_df = pd.DataFrame([data['order']])
            order_df.to_csv(filepath.with_suffix('.order.csv'), index=False)
            details_df = pd.DataFrame(data['details'])
            details_df.to_csv(filepath.with_suffix('.details.csv'), index=False
                )
            return True
        except Exception:
            return False

        @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: Path) ->bool:
        """Export order data to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception:
            return False
