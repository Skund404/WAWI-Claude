

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class DatabaseUtilities:

    @inject(MaterialService)
        def __init__(self, db_path: Path):
    self.db_path = db_path

    @inject(MaterialService)
        def export_database(self, export_path: Path) -> bool:
    """Export database to a zip file containing JSON and CSV formats"""
    try:
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED
                             ) as zipf:
            schema = self.export_schema()
            zipf.writestr('schema.json', json.dumps(schema, indent=2))
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
            )
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                cursor.execute(f'SELECT * FROM {table_name}')
                columns = [description[0] for description in cursor.
                           description]
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                zipf.writestr(f'json/{table_name}.json', json.dumps(
                    data, indent=2, default=str))
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

    @inject(MaterialService)
        def import_database(self, import_path: Path) -> bool:
    """Import database from a zip file"""
    try:
        backup_path = self.db_path.with_suffix('.backup')
        with open(self.db_path, 'rb') as src, open(backup_path, 'wb'
                                                   ) as dst:
            dst.write(src.read())
        with zipfile.ZipFile(import_path, 'r') as zipf:
            schema = json.loads(zipf.read('schema.json'))
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
            )
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(f'DROP TABLE IF EXISTS {table[0]}')
            for table_name, table_schema in schema.items():
                cursor.execute(table_schema)
            for filename in zipf.namelist():
                if filename.startswith('json/') and filename.endswith(
                        '.json'):
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
        if backup_path.exists():
            with open(backup_path, 'rb') as src, open(self.db_path, 'wb'
                                                      ) as dst:
                dst.write(src.read())
        return False
    finally:
        if backup_path.exists():
            backup_path.unlink()

    @inject(MaterialService)
        def export_schema(self) -> Dict[str, str]:
    """Export database schema"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    schema = {}
    cursor.execute(
        """
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
    )
    for table_name, table_sql in cursor.fetchall():
        schema[table_name] = table_sql
    conn.close()
    return schema

    @inject(MaterialService)
        def optimize_database(self) -> bool:
    """Optimize database (vacuum, analyze, etc.)"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('VACUUM')
        cursor.execute('ANALYZE')
        cursor.execute(
            """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
        )
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f'ANALYZE {table[0]}')
        conn.close()
        return True
    except Exception as e:
        print(f'Optimization error: {str(e)}')
        return False

    @inject(MaterialService)
        def verify_database(self) -> Dict[str, Any]:
    """Verify database integrity and return status report"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        report = {'status': 'ok', 'errors': [], 'warnings': [],
                  'statistics': {}}
        cursor.execute('PRAGMA integrity_check')
        integrity = cursor.fetchone()[0]
        if integrity != 'ok':
            report['status'] = 'error'
            report['errors'].append(f'Integrity check failed: {integrity}')
        cursor.execute('PRAGMA foreign_key_check')
        fk_violations = cursor.fetchall()
        if fk_violations:
            report['status'] = 'error'
            report['errors'].append(
                f'Foreign key violations found: {len(fk_violations)}')
        cursor.execute(
            """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
        )
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            report['statistics'][table_name] = {'row_count': count}
        conn.close()
        return report
    except Exception as e:
        return {'status': 'error', 'errors': [str(e)], 'warnings': [],
                'statistics': {}}

    @inject(MaterialService)
        def generate_report(self, report_type: str) -> Dict[str, Any]:
    """Generate various types of reports"""
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

    @inject(MaterialService)
        def _generate_inventory_report(self, cursor) -> Dict[str, Any]:
    """Generate inventory report"""
    report = {'timestamp': datetime.datetime.now().isoformat(), 'type':
              'inventory', 'sections': {}}
    cursor.execute(
        """
            SELECT 
                type,
                COUNT(*) as count,
                SUM(area_sqft) as total_area,
                COUNT(DISTINCT color) as color_count
            FROM shelf
            GROUP BY type
        """
    )
    report['sections']['shelf'] = {'summary': cursor.fetchall(),
                                   'low_stock': []}
    cursor.execute(
        """
            SELECT name, type, color, amount
            FROM shelf
            WHERE amount <= 5
            ORDER BY amount
        """
    )
    report['sections']['shelf']['low_stock'] = cursor.fetchall()
    cursor.execute(
        """
            SELECT 
                bin,
                COUNT(*) as count,
                SUM(in_storage) as total_stock
            FROM sorting_system
            GROUP BY bin
        """
    )
    report['sections']['parts'] = {'summary': cursor.fetchall(),
                                   'low_stock': []}
    cursor.execute(
        """
            SELECT name, color, in_storage, bin
            FROM sorting_system
            WHERE in_storage <= 5
            ORDER BY in_storage
        """
    )
    report['sections']['parts']['low_stock'] = cursor.fetchall()
    return report

    @inject(MaterialService)
        def _generate_orders_report(self, cursor) -> Dict[str, Any]:
    """Generate orders report"""
    report = {'timestamp': datetime.datetime.now().isoformat(), 'type':
              'orders', 'sections': {}}
    cursor.execute(
        """
            SELECT 
                status,
                COUNT(*) as count,
                COUNT(CASE WHEN payed = 'yes' THEN 1 END) as paid_count
            FROM orders
            GROUP BY status
        """
    )
    report['sections']['status_summary'] = cursor.fetchall()
    cursor.execute(
        """
            SELECT 
                supplier,
                date_of_order,
                status,
                order_number,
                payed
            FROM orders
            WHERE date_of_order >= date('now', '-30 days')
            ORDER BY date_of_order DESC
        """
    )
    report['sections']['recent_orders'] = cursor.fetchall()
    cursor.execute(
        """
            SELECT 
                supplier,
                date_of_order,
                order_number
            FROM orders
            WHERE payed = 'no'
            ORDER BY date_of_order
        """
    )
    report['sections']['pending_payments'] = cursor.fetchall()
    return report

    @inject(MaterialService)
        def _generate_suppliers_report(self, cursor) -> Dict[str, Any]:
    """Generate suppliers report"""
    report = {'timestamp': datetime.datetime.now().isoformat(), 'type':
              'suppliers', 'sections': {}}
    cursor.execute(
        """
            SELECT 
                COUNT(*) as total_suppliers,
                COUNT(DISTINCT country) as countries,
                COUNT(DISTINCT currency) as currencies
            FROM supplier
        """
    )
    report['sections']['summary'] = cursor.fetchone()
    cursor.execute(
        """
            SELECT 
                s.company_name,
                COUNT(o.order_number) as order_count,
                MAX(o.date_of_order) as last_order
            FROM supplier s
            LEFT JOIN orders o ON s.company_name = o.supplier
            GROUP BY s.company_name
            ORDER BY order_count DESC
        """
    )
    report['sections']['supplier_orders'] = cursor.fetchall()
    cursor.execute(
        """
            SELECT 
                payment_terms,
                COUNT(*) as supplier_count
            FROM supplier
            GROUP BY payment_terms
        """
    )
    report['sections']['payment_terms'] = cursor.fetchall()
    return report
