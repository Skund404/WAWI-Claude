# database/diagnostics.py
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import inspect, func, select, and_, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models.customer import Customer
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.product import Product
from database.models.pattern import Pattern
from database.models.supplier import Supplier
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem
from database.models.inventory import Inventory
from database.models.project import Project
from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.material import Material, Leather, Hardware, Supplies
from database.models.picking_list import PickingList
from database.models.picking_list_item import PickingListItem
from database.models.tool import Tool
from database.models.tool_list import ToolList
from database.models.tool_list_item import ToolListItem
from database.models.project_component import ProjectComponent


class DatabaseDiagnostics:
    """
    Provides tools for diagnosing and validating the leatherworking database.

    This class includes methods for:
    - Verifying table existence
    - Counting records in each table
    - Validating model relationships
    - Running comprehensive diagnostics
    - Generating diagnostic reports
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize DatabaseDiagnostics with an optional session.

        Args:
            session (Optional[Session]): SQLAlchemy session. If None, creates a new session.
        """
        if session is None:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from pathlib import Path
            import os

            # Find the database path similar to initialize_database.py
            base_dir = Path(__file__).resolve().parent
            data_dir = base_dir / 'data'
            db_path = str(data_dir / 'leatherworking_database.db')

            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found at: {db_path}")

            engine = create_engine(f"sqlite:///{db_path}")
            SessionLocal = sessionmaker(bind=engine)
            self.session = SessionLocal()
            self._own_session = True
        else:
            self.session = session
            self._own_session = False

        self.logger = logging.getLogger(__name__)

    def __del__(self):
        """Clean up resources when the object is deleted."""
        if hasattr(self, '_own_session') and self._own_session and hasattr(self, 'session'):
            self.session.close()

    def verify_table_existence(self) -> Dict[str, bool]:
        """
        Verify existence of all expected tables in the database based on the ER diagram.

        Returns:
            Dict[str, bool]: A dictionary of table names and their existence status
        """
        inspector = inspect(self.session.bind)
        tables_to_check = [
            # Customer and Sales Related
            'customers', 'sales', 'sales_items',

            # Product and Pattern Related
            'products', 'patterns',

            # Material Related
            'materials', 'leathers', 'hardware', 'supplies',

            # Supplier and Purchase Related
            'suppliers', 'purchases', 'purchase_items',

            # Inventory Related
            'inventory',

            # Project and Component Related
            'projects', 'components', 'component_materials', 'project_components',

            # Picking and Tool Management
            'picking_lists', 'picking_list_items',
            'tools', 'tool_lists', 'tool_list_items',
        ]

        table_existence = {}
        for table in tables_to_check:
            try:
                table_existence[table] = inspector.has_table(table)
            except Exception as e:
                self.logger.error(f"Error checking table {table}: {e}")
                table_existence[table] = False

        return table_existence

    def count_records_per_model(self) -> Dict[str, int]:
        """
        Count records for each model in the database.

        Returns:
            Dict[str, int]: A dictionary of model names and their record counts
        """
        models_to_count = [
            # Customer and Sales Related
            Customer, Sales, SalesItem,

            # Product and Pattern Related
            Product, Pattern,

            # Material Related
            Material, Leather, Hardware, Supplies,

            # Supplier and Purchase Related
            Supplier, Purchase, PurchaseItem,

            # Inventory Related
            Inventory,

            # Project and Component Related
            Project, Component, ComponentMaterial, ProjectComponent,

            # Picking and Tool Management
            PickingList, PickingListItem,
            Tool, ToolList, ToolListItem
        ]

        record_counts = {}
        for model in models_to_count:
            try:
                count = self.session.query(model).count()
                record_counts[model.__tablename__] = count
            except SQLAlchemyError as e:
                self.logger.error(f"Error counting records for {model.__name__}: {e}")
                record_counts[model.__tablename__] = -1

        return record_counts

    def validate_model_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate relationships for each model based on the ER diagram.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary of models and their relationship validation results
        """
        relationship_validation = {}

        def validate_model_relationships_internal(model):
            """Internal helper to validate relationships for a single model."""
            mapper = inspect(model)
            relationships = []

            try:
                for rel in mapper.relationships:
                    try:
                        # Get relationship details
                        target_model = rel.mapper.class_.__name__
                        relationship_type = str(rel.direction.name)

                        # Try to check if we can query this relationship
                        valid = True
                        error_msg = None
                        try:
                            # Just test the mapper, don't execute a query
                            mapper.relationships[rel.key]
                        except Exception as e:
                            valid = False
                            error_msg = str(e)

                        relationships.append({
                            "name": rel.key,
                            "target": target_model,
                            "type": relationship_type,
                            "valid": valid,
                            "error": error_msg
                        })
                    except Exception as e:
                        relationships.append({
                            "name": rel.key if hasattr(rel, 'key') else "unknown",
                            "target": "unknown",
                            "type": "unknown",
                            "valid": False,
                            "error": str(e)
                        })
            except Exception as e:
                relationships.append({
                    "name": "relationship_inspection_failed",
                    "target": "unknown",
                    "type": "unknown",
                    "valid": False,
                    "error": str(e)
                })

            return relationships

        models_to_validate = [
            # Customer and Sales Related
            Customer, Sales, SalesItem,

            # Product and Pattern Related
            Product, Pattern,

            # Material Related
            Material, Leather, Hardware, Supplies,

            # Supplier and Purchase Related
            Supplier, Purchase, PurchaseItem,

            # Inventory Related
            Inventory,

            # Project and Component Related
            Project, Component, ComponentMaterial, ProjectComponent,

            # Picking and Tool Management
            PickingList, PickingListItem,
            Tool, ToolList, ToolListItem
        ]

        for model in models_to_validate:
            relationship_validation[model.__name__] = validate_model_relationships_internal(model)

        return relationship_validation

    def validate_data_integrity(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate data integrity across related models.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Results of integrity checks
        """
        integrity_checks = {}

        # Check 1: Ensure all SalesItems reference valid Sales
        try:
            orphaned_sales_items = self.session.query(SalesItem).filter(
                ~SalesItem.sales_id.in_(
                    self.session.query(Sales.id)
                )
            ).all()

            integrity_checks['orphaned_sales_items'] = [{
                'id': item.id,
                'sales_id': item.sales_id,
                'product_id': item.product_id
            } for item in orphaned_sales_items]
        except Exception as e:
            integrity_checks['orphaned_sales_items'] = [{'error': str(e)}]

        # Check 2: Ensure all Projects reference valid Customers
        try:
            orphaned_projects = self.session.query(Project).filter(
                ~Project.customer_id.in_(
                    self.session.query(Customer.id)
                )
            ).all()

            integrity_checks['orphaned_projects'] = [{
                'id': project.id,
                'name': project.name,
                'customer_id': project.customer_id
            } for project in orphaned_projects]
        except Exception as e:
            integrity_checks['orphaned_projects'] = [{'error': str(e)}]

        # Check 3: Ensure all ProjectComponents reference valid Components
        try:
            invalid_project_components = self.session.query(ProjectComponent).filter(
                ~ProjectComponent.component_id.in_(
                    self.session.query(Component.id)
                )
            ).all()

            integrity_checks['invalid_project_components'] = [{
                'id': pc.id,
                'project_id': pc.project_id,
                'component_id': pc.component_id
            } for pc in invalid_project_components]
        except Exception as e:
            integrity_checks['invalid_project_components'] = [{'error': str(e)}]

        # Check 4: Ensure all ComponentMaterials reference valid Materials
        try:
            invalid_component_materials = self.session.query(ComponentMaterial).filter(
                ~ComponentMaterial.material_id.in_(
                    self.session.query(Material.id)
                )
            ).all()

            integrity_checks['invalid_component_materials'] = [{
                'id': cm.id,
                'component_id': cm.component_id,
                'material_id': cm.material_id
            } for cm in invalid_component_materials]
        except Exception as e:
            integrity_checks['invalid_component_materials'] = [{'error': str(e)}]

        return integrity_checks

    def analyze_inventory_status(self) -> Dict[str, Any]:
        """
        Analyze inventory status and identify low stock items.

        Returns:
            Dict[str, Any]: Inventory analysis results
        """
        from database.models.enums import InventoryStatus

        inventory_analysis = {
            'total_items': 0,
            'in_stock': 0,
            'low_stock': 0,
            'out_of_stock': 0,
            'by_type': {},
            'low_stock_items': []
        }

        try:
            # Get inventory counts by status
            inventory_by_status = self.session.query(
                Inventory.status,
                func.count(Inventory.id)
            ).group_by(Inventory.status).all()

            for status, count in inventory_by_status:
                inventory_analysis['total_items'] += count
                if status == InventoryStatus.IN_STOCK:
                    inventory_analysis['in_stock'] = count
                elif status == InventoryStatus.LOW_STOCK:
                    inventory_analysis['low_stock'] = count
                elif status == InventoryStatus.OUT_OF_STOCK:
                    inventory_analysis['out_of_stock'] = count

            # Get inventory counts by item type
            inventory_by_type = self.session.query(
                Inventory.item_type,
                func.count(Inventory.id)
            ).group_by(Inventory.item_type).all()

            for item_type, count in inventory_by_type:
                inventory_analysis['by_type'][item_type] = count

            # Get low stock items
            low_stock_items = self.session.query(Inventory).filter(
                Inventory.status.in_([InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK])
            ).all()

            # For each low stock item, try to get the item name
            for item in low_stock_items:
                item_name = "Unknown"
                try:
                    if item.item_type == "material":
                        material = self.session.query(Material).filter_by(id=item.item_id).first()
                        if material:
                            item_name = material.name
                    elif item.item_type == "product":
                        product = self.session.query(Product).filter_by(id=item.item_id).first()
                        if product:
                            item_name = product.name
                    elif item.item_type == "tool":
                        tool = self.session.query(Tool).filter_by(id=item.item_id).first()
                        if tool:
                            item_name = tool.name
                except:
                    pass

                inventory_analysis['low_stock_items'].append({
                    'id': item.id,
                    'item_type': item.item_type,
                    'item_id': item.item_id,
                    'name': item_name,
                    'quantity': item.quantity,
                    'status': item.status.name if hasattr(item.status, 'name') else str(item.status)
                })

        except Exception as e:
            self.logger.error(f"Error analyzing inventory: {e}")
            inventory_analysis['error'] = str(e)

        return inventory_analysis

    def analyze_sales_trends(self) -> Dict[str, Any]:
        """
        Analyze sales trends by product, customer, and time period.

        Returns:
            Dict[str, Any]: Sales trend analysis results
        """
        sales_analysis = {
            'total_sales': 0,
            'total_revenue': 0,
            'top_products': [],
            'top_customers': [],
            'monthly_sales': []
        }

        try:
            # Get total sales and revenue
            sales_totals = self.session.query(
                func.count(Sales.id),
                func.sum(Sales.total_amount)
            ).first()

            sales_analysis['total_sales'] = sales_totals[0] or 0
            sales_analysis['total_revenue'] = float(sales_totals[1] or 0)

            # Get top selling products
            top_products = self.session.query(
                Product.id,
                Product.name,
                func.sum(SalesItem.quantity).label('total_sold'),
                func.sum(SalesItem.price * SalesItem.quantity).label('total_revenue')
            ).join(SalesItem, SalesItem.product_id == Product.id) \
                .group_by(Product.id) \
                .order_by(func.sum(SalesItem.quantity).desc()) \
                .limit(5).all()

            sales_analysis['top_products'] = [
                {
                    'id': p.id,
                    'name': p.name,
                    'total_sold': p.total_sold or 0,
                    'total_revenue': float(p.total_revenue or 0)
                } for p in top_products
            ]

            # Get top customers
            top_customers = self.session.query(
                Customer.id,
                Customer.first_name,
                Customer.last_name,
                func.count(Sales.id).label('total_orders'),
                func.sum(Sales.total_amount).label('total_spent')
            ).join(Sales, Sales.customer_id == Customer.id) \
                .group_by(Customer.id) \
                .order_by(func.sum(Sales.total_amount).desc()) \
                .limit(5).all()

            sales_analysis['top_customers'] = [
                {
                    'id': c.id,
                    'name': f"{c.first_name} {c.last_name}",
                    'total_orders': c.total_orders or 0,
                    'total_spent': float(c.total_spent or 0)
                } for c in top_customers
            ]

            # Get monthly sales (using SQLite's strftime function)
            # This is SQLite-specific - would need to be adjusted for other databases
            monthly_sales = self.session.execute(text("""
                SELECT 
                    strftime('%Y-%m', sale_date) as month,
                    COUNT(*) as order_count,
                    SUM(total_amount) as revenue
                FROM 
                    sales
                GROUP BY 
                    strftime('%Y-%m', sale_date)
                ORDER BY 
                    month DESC
                LIMIT 12
            """)).fetchall()

            sales_analysis['monthly_sales'] = [
                {
                    'month': row[0],
                    'order_count': row[1],
                    'revenue': float(row[2] or 0)
                } for row in monthly_sales
            ]

        except Exception as e:
            self.logger.error(f"Error analyzing sales trends: {e}")
            sales_analysis['error'] = str(e)

        return sales_analysis

    def run_full_database_diagnostics(self) -> Dict[str, Any]:
        """
        Run a comprehensive database diagnostic check.

        Returns:
            Dict[str, Any]: A dictionary containing various diagnostic results
        """
        diagnostics_results = {
            'table_existence': self.verify_table_existence(),
            'record_counts': self.count_records_per_model(),
            'relationship_validation': self.validate_model_relationships(),
            'data_integrity': self.validate_data_integrity(),
            'inventory_status': self.analyze_inventory_status(),
            'sales_trends': self.analyze_sales_trends()
        }

        return diagnostics_results

    def print_diagnostics_report(self, diagnostics: Optional[Dict[str, Any]] = None):
        """
        Print a formatted diagnostic report.

        Args:
            diagnostics (Optional[Dict[str, Any]]): Diagnostic results to print.
                                                   If None, runs a new diagnostic check.
        """
        if diagnostics is None:
            diagnostics = self.run_full_database_diagnostics()

        print("\n=== COMPREHENSIVE DATABASE DIAGNOSTICS REPORT ===")

        # Table Existence
        print("\n== Table Existence ==")
        missing_tables = []
        for table, exists in diagnostics['table_existence'].items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{table}: {status}")
            if not exists:
                missing_tables.append(table)

        if missing_tables:
            print(f"\nWARNING: {len(missing_tables)} tables are missing: {', '.join(missing_tables)}")

        # Record Counts
        print("\n== Record Counts ==")
        empty_tables = []
        for table, count in diagnostics['record_counts'].items():
            print(f"{table}: {count} records")
            if count == 0:
                empty_tables.append(table)

        if empty_tables:
            print(f"\nNOTE: {len(empty_tables)} tables are empty: {', '.join(empty_tables)}")

        # Relationship Validation
        print("\n== Relationship Validation ==")
        relationship_issues = []
        for model, relationships in diagnostics['relationship_validation'].items():
            print(f"\n{model} Relationships:")
            for rel in relationships:
                status = "✓" if rel['valid'] else "✗"
                print(f"  {status} {rel['name']} -> {rel['target']} ({rel['type']})")
                if not rel['valid'] and rel['error']:
                    print(f"    Error: {rel['error']}")
                    relationship_issues.append(f"{model}.{rel['name']}")

        if relationship_issues:
            print(f"\nWARNING: {len(relationship_issues)} relationship issues found")

        # Data Integrity Checks
        print("\n== Data Integrity ==")
        integrity_issues = False
        for check_name, results in diagnostics['data_integrity'].items():
            if results and not (len(results) == 1 and 'error' in results[0]):
                integrity_issues = True
                print(f"\n{check_name.replace('_', ' ').title()}: {len(results)} issues found")
                for i, issue in enumerate(results[:5], 1):  # Show only first 5 issues
                    print(f"  {i}. {issue}")
                if len(results) > 5:
                    print(f"  ... and {len(results) - 5} more")

        if not integrity_issues:
            print("\nNo data integrity issues found!")

        # Inventory Status
        print("\n== Inventory Status ==")
        inventory = diagnostics['inventory_status']
        if 'error' in inventory:
            print(f"Error analyzing inventory: {inventory['error']}")
        else:
            print(f"Total inventory items: {inventory['total_items']}")
            print(f"  In stock: {inventory['in_stock']}")
            print(f"  Low stock: {inventory['low_stock']}")
            print(f"  Out of stock: {inventory['out_of_stock']}")

            print("\nInventory by type:")
            for item_type, count in inventory['by_type'].items():
                print(f"  {item_type}: {count} items")

            if inventory['low_stock_items']:
                print(f"\nLow/Out of stock items ({len(inventory['low_stock_items'])}):")
                for i, item in enumerate(inventory['low_stock_items'][:10], 1):  # Show only first 10
                    print(f"  {i}. {item['name']} ({item['item_type']}): {item['quantity']} - {item['status']}")
                if len(inventory['low_stock_items']) > 10:
                    print(f"  ... and {len(inventory['low_stock_items']) - 10} more")

        # Sales Trends
        print("\n== Sales Trends ==")
        sales = diagnostics['sales_trends']
        if 'error' in sales:
            print(f"Error analyzing sales: {sales['error']}")
        else:
            print(f"Total sales: {sales['total_sales']} orders")
            print(f"Total revenue: ${sales['total_revenue']:.2f}")

            if sales['top_products']:
                print("\nTop selling products:")
                for i, product in enumerate(sales['top_products'], 1):
                    print(f"  {i}. {product['name']}: {product['total_sold']} sold (${product['total_revenue']:.2f})")

            if sales['top_customers']:
                print("\nTop customers:")
                for i, customer in enumerate(sales['top_customers'], 1):
                    print(
                        f"  {i}. {customer['name']}: {customer['total_orders']} orders (${customer['total_spent']:.2f})")

            if sales['monthly_sales']:
                print("\nMonthly sales (recent first):")
                for i, month in enumerate(sales['monthly_sales'][:6], 1):  # Show only last 6 months
                    print(f"  {month['month']}: {month['order_count']} orders (${month['revenue']:.2f})")


def main():
    """
    Main function to run database diagnostics.

    Usage:
        python -m database.diagnostics [--silent] [--report-file=output.txt]
    """
    import argparse

    # Configure argument parser
    parser = argparse.ArgumentParser(description='Run database diagnostics')
    parser.add_argument('--silent', action='store_true', help='Run silently without console output')
    parser.add_argument('--report-file', type=str, help='Save report to a file')
    args = parser.parse_args()

    # Configure logging
    log_level = logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Run diagnostics
        diagnostics = DatabaseDiagnostics()
        full_report = diagnostics.run_full_database_diagnostics()

        # Print to console if not silent
        if not args.silent:
            diagnostics.print_diagnostics_report(full_report)

        # Save to file if requested
        if args.report_file:
            import json
            import io

            # Save full JSON results
            json_file = args.report_file
            if not json_file.endswith('.json'):
                json_file += '.json'

            with open(json_file, 'w') as f:
                json.dump(full_report, f, indent=2, default=str)

            # Also save a text report
            txt_file = args.report_file
            if txt_file.endswith('.json'):
                txt_file = txt_file[:-5] + '.txt'
            elif not txt_file.endswith('.txt'):
                txt_file += '.txt'

            # Capture print output to a file
            with open(txt_file, 'w') as f:
                # Redirect stdout temporarily
                old_stdout = sys.stdout
                sys.stdout = f
                try:
                    diagnostics.print_diagnostics_report(full_report)
                finally:
                    sys.stdout = old_stdout

            if not args.silent:
                print(f"\nDiagnostic reports saved to:")
                print(f"  - JSON: {json_file}")
                print(f"  - Text: {txt_file}")

    except Exception as e:
        logging.error(f"Database diagnostics failed: {e}")
        import traceback
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()