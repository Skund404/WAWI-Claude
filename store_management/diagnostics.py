# database/diagnostics.py
import logging
import sys
from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, func, select, text, create_engine
from sqlalchemy.orm import Session, sessionmaker
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

    The diagnostics now strictly follow the ER diagram provided.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize DatabaseDiagnostics with an optional session.

        Args:
            session (Optional[Session]): SQLAlchemy session. If None, creates a new session.
        """
        import os
        from pathlib import Path

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        if session is None:
            # Use the current file's directory as the base directory; assumed to be store_management
            base_dir = Path(__file__).resolve().parent
            # Assume the data folder is inside store_management
            data_dir = base_dir / "data"
            db_path = str(data_dir / "leatherworking_database.db")
            db_path = os.path.abspath(db_path)
            self.logger.info(f"Database path (Diagnostics): {db_path}")

            if not os.path.exists(db_path):
                msg = f"Database file not found at: {db_path}"
                self.logger.error(msg)
                raise FileNotFoundError(msg)

            # Create a single engine instance with echo enabled initially for reflection.
            self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
            SessionLocal = sessionmaker(bind=self.engine)
            self.session = SessionLocal()
            self._own_session = True

            try:
                self.logger.info("Starting SQLAlchemy metadata reflection...")
                Base.metadata.reflect(bind=self.session.bind)
                self.logger.info("SQLAlchemy metadata reflection completed.")
            except Exception as e:
                self.logger.error(f"Failed to refresh SQLAlchemy metadata: {e}")
                self.logger.exception(e)
                raise
            finally:
                self.engine.echo = False
        else:
            self.session = session
            self._own_session = False

    def __del__(self):
        """Clean up resources when the object is deleted."""
        if getattr(self, "_own_session", False) and hasattr(self, "session"):
            self.session.close()

    def verify_table_existence(self) -> Dict[str, bool]:
        """
        Verify existence of all expected tables in the database based on the ER diagram.

        Returns:
            Dict[str, bool]: A dictionary of table names and their existence status.
        """
        inspector = inspect(self.session.bind)
        self.logger.info("\nTables found by SQLAlchemy AFTER reflection:")
        for table_name in inspector.get_table_names():
            self.logger.info(f"- {table_name}")

        expected_tables = [
            # Customer and Sales Related
            "customers", "sales", "sales_items",
            # Product and Pattern Related
            "products", "patterns",
            # Material and its subtypes
            "materials", "leathers", "hardware", "supplies",
            # Supplier and Purchase Related
            "suppliers", "purchases", "purchase_items",
            # Inventory Related
            "inventory",
            # Project and Component Related
            "projects", "components", "component_materials", "project_components",
            # Picking and Tool Management
            "picking_lists", "picking_list_items",
            "tools", "tool_lists", "tool_list_items",
        ]

        table_existence = {}
        for table in expected_tables:
            self.logger.info(f"Checking for table: {table}")
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
            Dict[str, int]: A dictionary of model names and their record counts.
        """
        models_to_count = [
            # Customer and Sales Related
            Customer, Sales, SalesItem,
            # Product and Pattern Related
            Product, Pattern,
            # Material and its subtypes
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
                self.logger.error(
                    f"Error counting records for {model.__name__}: {e}"
                )
                record_counts[model.__tablename__] = -1

        return record_counts

    def validate_model_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate relationships for each model based on the ER diagram.

        Returns:
            Dict[str, List[Dict[str, Any]]]: A dictionary of models
            and their relationship validation results.
        """
        relationship_validation = {}

        def validate_model_relationships_internal(model):
            """Internal helper to validate relationships for a single model."""
            mapper = inspect(model)
            relationships = []
            try:
                for rel in mapper.relationships:
                    try:
                        target_model = rel.mapper.class_.__name__
                        relationship_type = str(rel.direction.name)
                        valid = True
                        error_msg = None
                        try:
                            getattr(model, rel.key)
                        except Exception as e:
                            valid = False
                            error_msg = str(e)
                        relationships.append({
                            "name": rel.key,
                            "target": target_model,
                            "type": relationship_type,
                            "valid": valid,
                            "error": error_msg,
                        })
                    except Exception as e:
                        relationships.append({
                            "name": rel.key if hasattr(rel, "key") else "unknown",
                            "target": "unknown",
                            "type": "unknown",
                            "valid": False,
                            "error": str(e),
                        })
            except Exception as e:
                relationships.append({
                    "name": "relationship_inspection_failed",
                    "target": "unknown",
                    "type": "unknown",
                    "valid": False,
                    "error": str(e),
                })
            return relationships

        models_to_validate = [
            # Customer and Sales Related
            Customer, Sales, SalesItem,
            # Product and Pattern Related
            Product, Pattern,
            # Material and its subtypes
            Material, Leather, Hardware, Supplies,
            # Supplier and Purchase Related
            Supplier, Purchase, PurchaseItem,
            # Inventory Related
            Inventory,
            # Project and Component Related
            Project, Component, ComponentMaterial, ProjectComponent,
            # Picking and Tool Management
            PickingList, PickingListItem,
            Tool, ToolList, ToolListItem,
        ]

        for model in models_to_validate:
            relationship_validation[model.__name__] = validate_model_relationships_internal(model)

        return relationship_validation

    def validate_data_integrity(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate data integrity across related models according to the ER diagram.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Results of integrity checks.
        """
        integrity_checks = {}

        # 1. SalesItems should reference valid Sales and Products.
        orphaned_sales_items_sales = self.session.query(SalesItem).filter(
            ~SalesItem.sales_id.in_(select(Sales.id))
        ).all()
        orphaned_sales_items_product = self.session.query(SalesItem).filter(
            ~SalesItem.product_id.in_(select(Product.id))
        ).all()
        integrity_checks["orphaned_sales_items_sales"] = [{
            "id": item.id,
            "sales_id": item.sales_id,
            "product_id": item.product_id,
        } for item in orphaned_sales_items_sales]
        integrity_checks["orphaned_sales_items_product"] = [{
            "id": item.id,
            "sales_id": item.sales_id,
            "product_id": item.product_id,
        } for item in orphaned_sales_items_product]

        # 2. Projects must reference a valid Sale (per the ER diagram).
        orphaned_projects = self.session.query(Project).filter(
            ~Project.sales_id.in_(select(Sales.id))
        ).all()
        integrity_checks["orphaned_projects"] = [{
            "id": project.id,
            "name": project.name,
            "sales_id": project.sales_id,
        } for project in orphaned_projects]

        # 3. ProjectComponents must reference valid Components.
        invalid_project_components = self.session.query(ProjectComponent).filter(
            ~ProjectComponent.component_id.in_(select(Component.id))
        ).all()
        integrity_checks["invalid_project_components"] = [{
            "id": pc.id,
            "project_id": pc.project_id,
            "component_id": pc.component_id,
        } for pc in invalid_project_components]

        # 4. ComponentMaterials must reference valid Materials.
        invalid_component_materials = self.session.query(ComponentMaterial).filter(
            ~ComponentMaterial.material_id.in_(select(Material.id))
        ).all()
        integrity_checks["invalid_component_materials"] = [{
            "id": cm.id,
            "component_id": cm.component_id,
            "material_id": cm.material_id,
        } for cm in invalid_component_materials]

        # 5. PurchaseItems must reference valid items based on their type
        orphaned_purchase_items_material = self.session.query(PurchaseItem).filter(
            PurchaseItem.item_type == "material",
            ~PurchaseItem.item_id.in_(select(Material.id))
        ).all()
        orphaned_purchase_items_tool = self.session.query(PurchaseItem).filter(
            PurchaseItem.item_type == "tool",
            ~PurchaseItem.item_id.in_(select(Tool.id))
        ).all()
        integrity_checks["orphaned_purchase_items"] = [{
            "id": item.id,
            "purchase_id": item.purchase_id,
            "item_id": item.item_id,
            "item_type": item.item_type,
        } for item in orphaned_purchase_items_material + orphaned_purchase_items_tool]

        # 6. PurchaseItems must also reference valid Purchases.
        orphaned_purchase_items_purchase = self.session.query(PurchaseItem).filter(
            ~PurchaseItem.purchase_id.in_(select(Purchase.id))
        ).all()
        integrity_checks["orphaned_purchase_items_purchase"] = [{
            "id": item.id,
            "purchase_id": item.purchase_id,
            "item_id": item.item_id,
            "item_type": item.item_type,
        } for item in orphaned_purchase_items_purchase]

        # 7. Inventory records must reference valid items based on item_type.
        invalid_inventory_material = self.session.query(Inventory).filter(
            Inventory.item_type == "material",
            ~Inventory.item_id.in_(select(Material.id))
        ).all()
        invalid_inventory_product = self.session.query(Inventory).filter(
            Inventory.item_type == "product",
            ~Inventory.item_id.in_(select(Product.id))
        ).all()
        invalid_inventory_tool = self.session.query(Inventory).filter(
            Inventory.item_type == "tool",
            ~Inventory.item_id.in_(select(Tool.id))
        ).all()
        integrity_checks["invalid_inventory_records"] = [{
            "id": item.id,
            "item_type": item.item_type,
            "item_id": item.item_id,
            "quantity": item.quantity,
        } for item in invalid_inventory_material + invalid_inventory_product + invalid_inventory_tool]

        # 8. PickingListItems must reference valid PickingList, Component, and Material.
        orphaned_plist = self.session.query(PickingListItem).filter(
            ~PickingListItem.picking_list_id.in_(select(PickingList.id))
        ).all()
        orphaned_plist_component = self.session.query(PickingListItem).filter(
            ~PickingListItem.component_id.in_(select(Component.id))
        ).all()
        orphaned_plist_material = self.session.query(PickingListItem).filter(
            ~PickingListItem.material_id.in_(select(Material.id))
        ).all()
        integrity_checks["orphaned_picking_list_items"] = {
            "missing_picking_list": [{
                "id": item.id,
                "picking_list_id": item.picking_list_id,
            } for item in orphaned_plist],
            "missing_component": [{
                "id": item.id,
                "component_id": item.component_id,
            } for item in orphaned_plist_component],
            "missing_material": [{
                "id": item.id,
                "material_id": item.material_id,
            } for item in orphaned_plist_material],
        }

        # 9. ToolListItems must reference valid Tools.
        orphaned_tool_list_items = self.session.query(ToolListItem).filter(
            ~ToolListItem.tool_id.in_(select(Tool.id))
        ).all()
        integrity_checks["orphaned_tool_list_items"] = [{
            "id": item.id,
            "tool_list_id": item.tool_list_id,
            "tool_id": item.tool_id,
            "quantity": item.quantity,
        } for item in orphaned_tool_list_items]

        # 10. Sales must reference valid Customers.
        orphaned_sales_customers = self.session.query(Sales).filter(
            ~Sales.customer_id.in_(select(Customer.id))
        ).all()
        integrity_checks["orphaned_sales_customers"] = [{
            "id": sale.id,
            "customer_id": sale.customer_id,
        } for sale in orphaned_sales_customers]

        # 11. Purchases must reference a valid Supplier.
        orphaned_purchases = self.session.query(Purchase).filter(
            ~Purchase.supplier_id.in_(select(Supplier.id))
        ).all()
        integrity_checks["orphaned_purchases"] = [{
            "id": purchase.id,
            "supplier_id": purchase.supplier_id,
        } for purchase in orphaned_purchases]

        # 12. ToolLists must reference valid Projects.
        orphaned_tool_list = self.session.query(ToolList).filter(
            ~ToolList.project_id.in_(select(Project.id))
        ).all()
        integrity_checks["orphaned_tool_lists"] = [{
            "id": tl.id,
            "project_id": tl.project_id,
        } for tl in orphaned_tool_list]

        return integrity_checks

    def analyze_inventory_status(self) -> Dict[str, Any]:
        """
        Analyze inventory status and identify low stock items.

        Returns:
            Dict[str, Any]: Inventory analysis results.
        """
        from database.models.enums import InventoryStatus

        inventory_analysis = {
            "total_items": 0,
            "in_stock": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "by_type": {},
            "low_stock_items": [],
        }

        try:
            # Count items by status.
            inventory_by_status = self.session.query(
                Inventory.status, func.count(Inventory.id)
            ).group_by(Inventory.status).all()

            for status, count in inventory_by_status:
                inventory_analysis["total_items"] += count
                if status == InventoryStatus.IN_STOCK:
                    inventory_analysis["in_stock"] = count
                elif status == InventoryStatus.LOW_STOCK:
                    inventory_analysis["low_stock"] = count
                elif status == InventoryStatus.OUT_OF_STOCK:
                    inventory_analysis["out_of_stock"] = count

            # Count items by item type.
            inventory_by_type = self.session.query(
                Inventory.item_type, func.count(Inventory.id)
            ).group_by(Inventory.item_type).all()

            for item_type, count in inventory_by_type:
                inventory_analysis["by_type"][item_type] = count

            # Get low/out-of-stock items.
            low_stock_items = self.session.query(Inventory).filter(
                Inventory.status.in_([
                    InventoryStatus.LOW_STOCK,
                    InventoryStatus.OUT_OF_STOCK,
                ])
            ).all()

            for item in low_stock_items:
                item_name = "Unknown"
                try:
                    if item.item_type == "material":
                        material = self.session.query(Material).filter_by(
                            id=item.item_id
                        ).first()
                        if material:
                            item_name = material.name
                    elif item.item_type == "product":
                        product = self.session.query(Product).filter_by(
                            id=item.item_id
                        ).first()
                        if product:
                            item_name = product.name
                    elif item.item_type == "tool":
                        tool = self.session.query(Tool).filter_by(
                            id=item.item_id
                        ).first()
                        if tool:
                            item_name = tool.name
                except Exception:
                    pass

                inventory_analysis["low_stock_items"].append({
                    "id": item.id,
                    "item_type": item.item_type,
                    "item_id": item.item_id,
                    "name": item_name,
                    "quantity": item.quantity,
                    "status": item.status.name if hasattr(item.status, "name")
                    else str(item.status),
                })

        except Exception as e:
            self.logger.error(f"Error analyzing inventory: {e}")
            inventory_analysis["error"] = str(e)

        return inventory_analysis

    def analyze_sales_trends(self) -> Dict[str, Any]:
        """
        Analyze sales trends by product, customer, and time period.

        Returns:
            Dict[str, Any]: Sales trend analysis results.
        """
        sales_analysis = {
            "total_sales": 0,
            "total_revenue": 0,
            "top_products": [],
            "top_customers": [],
            "monthly_sales": [],
        }

        try:
            # Total sales and revenue.
            sales_totals = self.session.query(
                func.count(Sales.id), func.sum(Sales.total_amount)
            ).first()

            sales_analysis["total_sales"] = sales_totals[0] or 0
            sales_analysis["total_revenue"] = float(sales_totals[1] or 0)

            # Top selling products.
            top_products = (
                self.session.query(
                    Product.id,
                    Product.name,
                    func.sum(SalesItem.quantity).label("total_sold"),
                    func.sum(SalesItem.price * SalesItem.quantity).label("total_revenue"),
                )
                .join(SalesItem, SalesItem.product_id == Product.id)
                .group_by(Product.id)
                .order_by(func.sum(SalesItem.quantity).desc())
                .limit(5)
                .all()
            )
            sales_analysis["top_products"] = [{
                "id": p.id,
                "name": p.name,
                "total_sold": p.total_sold or 0,
                "total_revenue": float(p.total_revenue or 0),
            } for p in top_products]

            # Top customers.
            top_customers = (
                self.session.query(
                    Customer.id,
                    Customer.first_name,
                    Customer.last_name,
                    func.count(Sales.id).label("total_orders"),
                    func.sum(Sales.total_amount).label("total_spent"),
                )
                .join(Sales, Sales.customer_id == Customer.id)
                .group_by(Customer.id)
                .order_by(func.sum(Sales.total_amount).desc())
                .limit(5)
                .all()
            )
            sales_analysis["top_customers"] = [{
                "id": c.id,
                "name": f"{c.first_name} {c.last_name}",
                "total_orders": c.total_orders or 0,
                "total_spent": float(c.total_spent or 0),
            } for c in top_customers]

            # Monthly sales (SQLite-specific using strftime).
            monthly_sales = self.session.execute(text("""
                SELECT 
                    strftime('%Y-%m', created_at) AS month,
                    COUNT(*) AS order_count,
                    SUM(total_amount) AS revenue
                FROM 
                    sales
                GROUP BY 
                    strftime('%Y-%m', created_at)
                ORDER BY 
                    month DESC
                LIMIT 12
            """)).fetchall()

            sales_analysis["monthly_sales"] = [{
                "month": row[0],
                "order_count": row[1],
                "revenue": float(row[2] or 0),
            } for row in monthly_sales]

        except Exception as e:
            self.logger.error(f"Error analyzing sales trends: {e}")
            sales_analysis["error"] = str(e)

        return sales_analysis

    def run_full_database_diagnostics(self) -> Dict[str, Any]:
        """
        Run a comprehensive database diagnostic check.

        Returns:
            Dict[str, Any]: A dictionary containing various diagnostic results.
        """
        diagnostics_results = {
            "table_existence": self.verify_table_existence(),
            "record_counts": self.count_records_per_model(),
            "relationship_validation": self.validate_model_relationships(),
            "data_integrity": self.validate_data_integrity(),
            "inventory_status": self.analyze_inventory_status(),
            "sales_trends": self.analyze_sales_trends(),
        }
        return diagnostics_results

    def print_diagnostics_report(
        self, diagnostics: Optional[Dict[str, Any]] = None
    ):
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
        for table, exists in diagnostics["table_existence"].items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{table}: {status}")
            if not exists:
                missing_tables.append(table)

        if missing_tables:
            print(
                f"\nWARNING: {len(missing_tables)} tables are missing: {', '.join(missing_tables)}"
            )

        # Record Counts
        print("\n== Record Counts ==")
        empty_tables = []
        for table, count in diagnostics["record_counts"].items():
            print(f"{table}: {count} records")
            if count == 0:
                empty_tables.append(table)
        if empty_tables:
            print(
                f"\nNOTE: {len(empty_tables)} tables are empty: {', '.join(empty_tables)}"
            )

        # Relationship Validation
        print("\n== Relationship Validation ==")
        relationship_issues = []
        for model, relationships in diagnostics["relationship_validation"].items():
            print(f"\n{model} Relationships:")
            for rel in relationships:
                status = "✓" if rel["valid"] else "✗"
                print(f"  {status} {rel['name']} -> {rel['target']} ({rel['type']})")
                if not rel["valid"] and rel["error"]:
                    print(f"    Error: {rel['error']}")
                    relationship_issues.append(f"{model}.{rel['name']}")
        if relationship_issues:
            print(
                f"\nWARNING: {len(relationship_issues)} relationship issues found"
            )

        # Data Integrity Checks
        print("\n== Data Integrity ==")
        integrity = diagnostics["data_integrity"]
        if integrity:
            for key, issues in integrity.items():
                if isinstance(issues, list) and issues:
                    print(f"\n{key.replace('_', ' ').title()}: {len(issues)} issues found")
                    for i, issue in enumerate(issues[:5], 1):
                        print(f"  {i}. {issue}")
                    if len(issues) > 5:
                        print(f"  ... and {len(issues)-5} more")
                elif isinstance(issues, dict):
                    for subkey, subissues in issues.items():
                        if subissues:
                            print(
                                f"\n{subkey.replace('_', ' ').title()}: {len(subissues)} issues found"
                            )
                            for i, issue in enumerate(subissues[:5], 1):
                                print(f"  {i}. {issue}")
                            if len(subissues) > 5:
                                print(f"  ... and {len(subissues)-5} more")
        else:
            print("\nNo data integrity issues found!")

        # Inventory Status
        print("\n== Inventory Status ==")
        inventory = diagnostics["inventory_status"]
        if "error" in inventory:
            print(f"Error analyzing inventory: {inventory['error']}")
        else:
            print(f"Total inventory items: {inventory['total_items']}")
            print(f"  In stock: {inventory['in_stock']}")
            print(f"  Low stock: {inventory['low_stock']}")
            print(f"  Out of stock: {inventory['out_of_stock']}")
            print("\nInventory by type:")
            for item_type, count in inventory["by_type"].items():
                print(f"  {item_type}: {count} items")
            if inventory["low_stock_items"]:
                print(
                    f"\nLow/Out of stock items ({len(inventory['low_stock_items'])}):"
                )
                for i, item in enumerate(inventory["low_stock_items"][:10], 1):
                    print(
                        f"  {i}. {item['name']} ({item['item_type']}): {item['quantity']} - {item['status']}"
                    )
                if len(inventory["low_stock_items"]) > 10:
                    print(
                        f"  ... and {len(inventory['low_stock_items']) - 10} more"
                    )

        # Sales Trends
        print("\n== Sales Trends ==")
        sales = diagnostics["sales_trends"]
        if "error" in sales:
            print(f"Error analyzing sales: {sales['error']}")
        else:
            print(f"Total sales: {sales['total_sales']} orders")
            print(f"Total revenue: ${sales['total_revenue']:.2f}")
            if sales["top_products"]:
                print("\nTop selling products:")
                for i, product in enumerate(sales["top_products"], 1):
                    print(
                        f"  {i}. {product['name']}: {product['total_sold']} sold (${product['total_revenue']:.2f})"
                    )
            if sales["top_customers"]:
                print("\nTop customers:")
                for i, customer in enumerate(sales["top_customers"], 1):
                    print(
                        f"  {i}. {customer['name']}: {customer['total_orders']} orders (${customer['total_spent']:.2f})"
                    )
            if sales["monthly_sales"]:
                print("\nMonthly sales (recent first):")
                for i, month in enumerate(sales["monthly_sales"][:6], 1):
                    print(
                        f"  {month['month']}: {month['order_count']} orders (${month['revenue']:.2f})"
                    )

def main():
    """
    Main function to run database diagnostics.

    Usage:
        python -m database.diagnostics [--silent] [--report-file=output.txt]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run database diagnostics")
    parser.add_argument(
        "--silent", action="store_true", help="Run silently without console output"
    )
    parser.add_argument(
        "--report-file", type=str, help="Save report to a file"
    )
    args = parser.parse_args()

    log_level = logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        diagnostics = DatabaseDiagnostics()
        full_report = diagnostics.run_full_database_diagnostics()

        if not args.silent:
            diagnostics.print_diagnostics_report(full_report)

        if args.report_file:
            import json

            json_file = args.report_file
            if not json_file.endswith(".json"):
                json_file += ".json"

            with open(json_file, "w") as f:
                json.dump(full_report, f, indent=2, default=str)

            txt_file = args.report_file
            if txt_file.endswith(".json"):
                txt_file = txt_file[:-5] + ".txt"
            elif not txt_file.endswith(".txt"):
                txt_file += ".txt"

            with open(txt_file, "w") as f:
                old_stdout = sys.stdout
                sys.stdout = f
                try:
                    diagnostics.print_diagnostics_report(full_report)
                finally:
                    sys.stdout = old_stdout

            if not args.silent:
                print("\nDiagnostic reports saved to:")
                print(f"  - JSON: {json_file}")
                print(f"  - Text: {txt_file}")

    except Exception as e:
        logging.error(f"Database diagnostics failed: {e}")
        import traceback

        logging.error(traceback.format_exc())


def check_actual_tables():
    """
    Connect directly using SQLite to check actual tables and columns.
    """
    import sqlite3
    from pathlib import Path
    import os

    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    db_path = str(data_dir / "leatherworking_database.db")
    db_path = os.path.abspath(db_path)
    print(f"Database path (SQLite check): {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Actual tables in database:")
    for table in tables:
        print(f"- {table[0]}")

    for table_name in ["materials", "products", "customers", "inventory"]:
        try:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            if columns:
                print(f"\nColumns in {table_name} table:")
                for column in columns:
                    print(f"- {column[1]} ({column[2]})")
        except sqlite3.OperationalError:
            print(f"\n{table_name} table doesn't exist or can't be accessed")

    conn.close()


if __name__ == "__main__":
    # Uncomment one of these to run the desired entry point:
    # check_actual_tables()
    main()
