# utils/exporters.py
"""
Utility classes for exporting data to various formats.
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import xlsxwriter

    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False


class OrderExporter:
    """
    Utility class for exporting sale and inventory data.
    """

    @classmethod
    def export_to_csv(cls, data: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Export data to a CSV file.

        Args:
            data (List[Dict[str, Any]]): Data to export
            filepath (Optional[str]): Path to save the CSV file.
                                      If None, generates a timestamped filename.

        Returns:
            str: Path to the exported file
        """
        # Generate filename if not provided
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"export_{timestamp}.csv"

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if not data:
                    return filepath

                # Get fieldnames from first dictionary
                fieldnames = list(data[0].keys())

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            return filepath

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            raise

    @classmethod
    def export_to_excel(cls, data: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Export data to an Excel file.

        Args:
            data (List[Dict[str, Any]]): Data to export
            filepath (Optional[str]): Path to save the Excel file.
                                      If None, generates a timestamped filename.

        Returns:
            str: Path to the exported file
        """
        # Check if xlsxwriter is available
        if not XLSX_AVAILABLE:
            print("xlsxwriter not installed. Falling back to CSV export.")
            return cls.export_to_csv(data, filepath)

        # Generate filename if not provided
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"export_{timestamp}.xlsx"

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Convert to DataFrame for easy Excel export
            df = pd.DataFrame(data)

            # Write to Excel
            df.to_excel(filepath, index=False, engine='xlsxwriter')

            return filepath

        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            # Fallback to CSV if Excel export fails
            return cls.export_to_csv(data, filepath)

    @classmethod
    def export_to_json(cls, data: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Export data to a JSON file.

        Args:
            data (List[Dict[str, Any]]): Data to export
            filepath (Optional[str]): Path to save the JSON file.
                                      If None, generates a timestamped filename.

        Returns:
            str: Path to the exported file
        """
        # Generate filename if not provided
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"export_{timestamp}.json"

        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Write to JSON
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=4, ensure_ascii=False)

            return filepath

        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            raise