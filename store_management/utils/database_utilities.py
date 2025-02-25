# utils/database_utilities.py
import io
import csv
import json
import sqlite3
import zipfile
import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Optional


class DatabaseUtilities:
    """
    Database utility functions for exporting, importing and managing database.

    This class provides comprehensive functionality for database management
    including export/import to various formats, optimization, and report generation.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the database utilities.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    def export_database(self, export_path: Path) -> bool:
        """
        Export database to a zip file containing JSON and CSV formats.

        Args:
            export_path: Path where the zip file will be created

        Returns:
            Boolean indicating success or failure
        """
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Export schema
                schema = self.export_schema()
                zipf.writestr('schema.json', json.dumps(schema, indent=2))

                # Connect to database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()

                # Export each table
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f'SELECT * FROM {table_name}')
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()

                    # Export as JSON
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    zipf.writestr(f'json/{table_name}.json', json.dumps(
                        data, indent=2, default=str))

                    # Export as CSV
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(columns)
                    writer.writerows(rows)
                    zipf.writestr(f'csv/{table_name}.csv', output.getvalue())
                    output.close()

                conn.close()
                return True

        except Exception as e:
            print(f'Export error: {str(e)}')
            return False

    def import_database(self, import_path: Path) -> bool:
        """
        Import database from a zip file.

        Args:
            import_path: Path to the zip file containing database backup

        Returns:
            Boolean indicating success or failure
        """
        try:
            # Create a backup of current database
            backup_path = self.db_path.with_suffix('.backup')
            with open(self.db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())

            # Import from zip file
            with zipfile.ZipFile(import_path, 'r') as zipf:
                # Get schema
                schema = json.loads(zipf.read('schema.json'))

                # Connect to database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Drop existing tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f'DROP TABLE IF EXISTS {table[0]}')

                # Create tables from schema
                for table_name, table_schema in schema.items():
                    cursor.execute(table_schema)

                # Import data
                for filename in zipf.namelist():
                    if filename.startswith('json/') and filename.endswith('.json'):
                        table_name = Path(filename).stem
                        data = json.loads(zipf.read(filename))

                        if not data:
                            continue

                        columns = list(data[0].keys())
                        placeholders = ','.join(['?' for _ in columns])
                        insert_sql = f"""
                            INSERT INTO {table_name} 
                            ({','.join(columns)}) 
                            VALUES ({placeholders})
                        """

                        for row in data:
                            values = [row[col] for col in columns]
                            cursor.execute(insert_sql, values)

                conn.commit()
                conn.close()
                return True

        except Exception as e:
            print(f'Import error: {str(e)}')
            # Restore from backup if import fails
            if backup_path.exists():
                with open(backup_path, 'rb') as src, open(self.db_path, 'wb') as dst:
                    dst.write(src.read())
            return False

        finally:
            # Clean up backup file
            if backup_path.exists():
                backup_path.unlink()

    def export_schema(self) -> Dict[str, str]:
        """
        Export database schema.

        Returns:
            Dictionary mapping table names to their CREATE TABLE statements
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        schema = {}

        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)

        for table_name, table_sql in cursor.fetchall():
            schema[table_name] = table_sql

        conn.close()
        return schema

    def optimize_database(self) -> bool:
        """
        Optimize database (vacuum, analyze, etc.).

        Returns:
            Boolean indicating success or failure
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # VACUUM to reclaim space and defragment
            cursor.execute('VACUUM')

            # ANALYZE to update statistics
            cursor.execute('ANALYZE')

            # Analyze individual tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(f'ANALYZE {table[0]}')

            conn.close()
            return True

        except Exception as e:
            print(f'Optimization error: {str(e)}')
            return False

    def verify_database(self) -> Dict[str, Any]:
        """
        Verify database integrity and return status report.

        Returns:
            Dictionary with verification status and details
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            report = {
                'status': 'ok',
                'errors': [],
                'warnings': [],
                'statistics': {}
            }

            # Check integrity
            cursor.execute('PRAGMA integrity_check')
            integrity = cursor.fetchone()[0]
            if integrity != 'ok':
                report['status'] = 'error'
                report['errors'].append(f'Integrity check failed: {integrity}')

            # Check foreign keys
            cursor.execute('PRAGMA foreign_key_check')
            fk_violations = cursor.fetchall()
            if fk_violations:
                report['status'] = 'error'
                report['errors'].append(f'Foreign key violations found: {len(fk_violations)}')

            # Gather statistics
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cursor.fetchone()[0]
                report['statistics'][table_name] = {'row_count': count}

            conn.close()
            return report

        except Exception as e:
            return {'status': 'error', 'errors': [str(e)], 'warnings': [], 'statistics': {}}

    def generate_report(self, report_type: str) -> Dict[str, Any]:
        """
        Generate various types of reports.

        Args:
            report_type: Type of report to generate (inventory, orders, suppliers)

        Returns:
            Dictionary containing the report data

        Raises:
            ValueError: If an unknown report type is requested
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if report_type == 'inventory':
                return self._generate_inventory_report(cursor)
            elif report_type == 'orders':
                return self._generate_orders_report(cursor)
            elif report_type == 'suppliers':
                return self._generate_suppliers_report(cursor)
            else:
                raise ValueError(f'Unknown report type: {report_type}')
        finally:
            conn.close()

    def _generate_inventory_report(self, cursor) -> Dict[str, Any]:
        """
        Generate inventory report.

        Args:
            cursor: SQLite cursor for executing queries

        Returns:
            Dictionary containing the inventory report data
        """
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'inventory',
            'sections': {}
        }

        # Shelf summary
        cursor.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                SUM(area_sqft) as total_area,
                COUNT(DISTINCT color) as color_count
            FROM shelf
            GROUP BY type
        """)
        report['sections']['shelf'] = {'summary': cursor.fetchall(), 'low_stock': []}

        # Low stock items on shelves
        cursor.execute("""
            SELECT name, type, color, amount
            FROM shelf
            WHERE amount <= 5
            ORDER BY amount
        """)
        report['sections']['shelf']['low_stock'] = cursor.fetchall()

        # Parts summary
        cursor.execute("""
            SELECT 
                bin,
                COUNT(*) as count,
                SUM(in_storage) as total_stock
            FROM sorting_system
            GROUP BY bin
        """)
        report['sections']['parts'] = {'summary': cursor.fetchall(), 'low_stock': []}

        # Low stock parts
        cursor.execute("""
            SELECT name, color, in_storage, bin
            FROM sorting_system
            WHERE in_storage <= 5
            ORDER BY in_storage
        """)
        report['sections']['parts']['low_stock'] = cursor.fetchall()

        return report

    def _generate_orders_report(self, cursor) -> Dict[str, Any]:
        """
        Generate orders report.

        Args:
            cursor: SQLite cursor for executing queries

        Returns:
            Dictionary containing the orders report data
        """
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'orders',
            'sections': {}
        }

        # Status summary
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                COUNT(CASE WHEN payed = 'yes' THEN 1 END) as paid_count
            FROM orders
            GROUP BY status
        """)
        report['sections']['status_summary'] = cursor.fetchall()

        # Recent orders
        cursor.execute("""
            SELECT 
                supplier,
                date_of_order,
                status,
                order_number,
                payed
            FROM orders
            WHERE date_of_order >= date('now', '-30 days')
            ORDER BY date_of_order DESC
        """)
        report['sections']['recent_orders'] = cursor.fetchall()

        # Pending payments
        cursor.execute("""
            SELECT 
                supplier,
                date_of_order,
                order_number
            FROM orders
            WHERE payed = 'no'
            ORDER BY date_of_order
        """)
        report['sections']['pending_payments'] = cursor.fetchall()

        return report

    def _generate_suppliers_report(self, cursor) -> Dict[str, Any]:
        """
        Generate suppliers report.

        Args:
            cursor: SQLite cursor for executing queries

        Returns:
            Dictionary containing the suppliers report data
        """
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'type': 'suppliers',
            'sections': {}
        }

        # Overall summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_suppliers,
                COUNT(DISTINCT country) as countries,
                COUNT(DISTINCT currency) as currencies
            FROM supplier
        """)
        report['sections']['summary'] = cursor.fetchone()

        # Supplier orders
        cursor.execute("""
            SELECT 
                s.company_name,
                COUNT(o.order_number) as order_count,
                MAX(o.date_of_order) as last_order
            FROM supplier s
            LEFT JOIN orders o ON s.company_name = o.supplier
            GROUP BY s.company_name
            ORDER BY order_count DESC
        """)
        report['sections']['supplier_orders'] = cursor.fetchall()

        # Payment terms summary
        cursor.execute("""
            SELECT 
                payment_terms,
                COUNT(*) as supplier_count
            FROM supplier
            GROUP BY payment_terms
        """)
        report['sections']['payment_terms'] = cursor.fetchall()

        return report