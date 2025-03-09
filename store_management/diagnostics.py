# database/diagnostics.py
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base
from database.models import (
    Customer, Sales, SalesItem,
    Product, ProductPattern, Pattern,
    Purchase, PurchaseItem, Supplier,
    ProductInventory, MaterialInventory,
    LeatherInventory, HardwareInventory, ToolInventory,
    Project, Component, material,
    Leather, Hardware, Tool,
    PickingList, PickingListItem,
    ToolList, ToolListItem,
    ComponentMaterial, ComponentLeather,
    ComponentHardware, ComponentTool,
    ProjectComponent
)
from database.sqlalchemy.session import get_db_session


class DatabaseDiagnostics:
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize DatabaseDiagnostics with an optional session.

        Args:
            session (Optional[Session]): SQLAlchemy session. If None, creates a new session.
        """
        self.session = session or get_db_session()
        self.logger = logging.getLogger(__name__)

    def verify_table_existence(self) -> Dict[str, bool]:
        """
        Verify existence of all expected tables in the database.

        Returns:
            Dict[str, bool]: A dictionary of table names and their existence status
        """
        inspector = inspect(self.session.bind)
        tables_to_check = [
            # Customer and Sales Related
            'customers', 'sales', 'sales_items',

            # Product and Pattern Related
            'products', 'product_patterns', 'patterns',

            # Purchase and Supplier Related
            'purchases', 'purchase_items', 'suppliers',

            # Inventory Related
            'product_inventories', 'material_inventories',
            'leather_inventories', 'hardware_inventories', 'tool_inventories',

            # Project and Component Related
            'projects', 'components', 'materials',
            'leathers', 'hardwares', 'tools',

            # Picking and Tool Management
            'picking_lists', 'picking_list_items',
            'tool_lists', 'tool_list_items',

            # Junction Tables
            'component_materials', 'component_leathers',
            'component_hardwares', 'component_tools',
            'project_components'
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
            Product, ProductPattern, Pattern,

            # Purchase and Supplier Related
            Purchase, PurchaseItem, Supplier,

            # Inventory Related
            ProductInventory, MaterialInventory,
            LeatherInventory, HardwareInventory, ToolInventory,

            # Project and Component Related
            Project, Component, Material,
            Leather, Hardware, Tool,

            # Picking and Tool Management
            PickingList, PickingListItem,
            ToolList, ToolListItem,

            # Junction Tables
            ComponentMaterial, ComponentLeather,
            ComponentHardware, ComponentTool,
            ProjectComponent
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

    def validate_model_relationships(self) -> Dict[str, List[str]]:
        """
        Validate relationships for each model.

        Returns:
            Dict[str, List[str]]: A dictionary of models and their relationship validation results
        """
        relationship_validation = {}

        def validate_model_relationships_internal(model):
            """Internal helper to validate relationships for a single model."""
            mapper = inspect(model)
            relationships = []

            try:
                for rel in mapper.relationships:
                    try:
                        # Attempt to access the relationship to check its configuration
                        mapper = inspect(rel.mapper.class_)
                        relationships.append(f"{rel.key}: Valid")
                    except Exception as e:
                        relationships.append(f"{rel.key}: Invalid - {str(e)}")
            except Exception as e:
                relationships.append(f"Relationship inspection failed: {str(e)}")

            return relationships

        models_to_validate = [
            # Customer and Sales Related
            Customer, Sales, SalesItem,

            # Product and Pattern Related
            Product, ProductPattern, Pattern,

            # Purchase and Supplier Related
            Purchase, PurchaseItem, Supplier,

            # Inventory Related
            ProductInventory, MaterialInventory,
            LeatherInventory, HardwareInventory, ToolInventory,

            # Project and Component Related
            Project, Component, Material,
            Leather, Hardware, Tool,

            # Picking and Tool Management
            PickingList, PickingListItem,
            ToolList, ToolListItem,

            # Junction Tables
            ComponentMaterial, ComponentLeather,
            ComponentHardware, ComponentTool,
            ProjectComponent
        ]

        for model in models_to_validate:
            relationship_validation[model.__name__] = validate_model_relationships_internal(model)

        return relationship_validation

    def run_full_database_diagnostics(self) -> Dict[str, Any]:
        """
        Run a comprehensive database diagnostic check.

        Returns:
            Dict[str, Any]: A dictionary containing various diagnostic results
        """
        diagnostics_results = {
            'table_existence': self.verify_table_existence(),
            'record_counts': self.count_records_per_model(),
            'relationship_validation': self.validate_model_relationships()
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
        print("\nTable Existence:")
        for table, exists in diagnostics['table_existence'].items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{table}: {status}")

        # Record Counts
        print("\nRecord Counts:")
        for table, count in diagnostics['record_counts'].items():
            print(f"{table}: {count} records")

        # Relationship Validation
        print("\nRelationship Validation:")
        for model, relationships in diagnostics['relationship_validation'].items():
            print(f"\n{model} Relationships:")
            for rel in relationships:
                print(f"  - {rel}")


def main():
    """
    Main function to run database diagnostics.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        diagnostics = DatabaseDiagnostics()
        full_report = diagnostics.run_full_database_diagnostics()
        diagnostics.print_diagnostics_report(full_report)
    except Exception as e:
        logging.error(f"Database diagnostics failed: {e}")


if __name__ == "__main__":
    main()