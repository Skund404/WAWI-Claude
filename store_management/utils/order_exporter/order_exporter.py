# utils/exporters/order_exporter.py
import pandas as pd
from typing import Dict, Any
from pathlib import Path
import json

class OrderExporter:
    @staticmethod
    def export_to_excel(data: Dict[str, Any], filepath: Path) -> bool:
        """Export order data to Excel"""
        try:
            with pd.ExcelWriter(filepath) as writer:
                # Export order info
                order_df = pd.DataFrame([data['order']])
                order_df.to_excel(writer, sheet_name='Order', index=False)

                # Export details
                details_df = pd.DataFrame(data['details'])
                details_df.to_excel(writer, sheet_name='Details', index=False)

                # Apply formatting
                workbook = writer.book
                for sheet in writer.sheets.values():
                    for col in range(len(sheet.dimensions)):
                        sheet.column_dimensions[chr(65 + col)].auto_size = True

            return True
        except Exception:
            return False

    @staticmethod
    def export_to_csv(data: Dict[str, Any], filepath: Path) -> bool:
        """Export order data to CSV"""
        try:
            # Export order info
            order_df = pd.DataFrame([data['order']])
            order_df.to_csv(filepath.with_suffix('.order.csv'), index=False)

            # Export details
            details_df = pd.DataFrame(data['details'])
            details_df.to_csv(filepath.with_suffix('.details.csv'), index=False)

            return True
        except Exception:
            return False

    @staticmethod
    def export_to_json(data: Dict[str, Any], filepath: Path) -> bool:
        """Export order data to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception:
            return False