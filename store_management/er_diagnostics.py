# improved_er_diagnostics.py
"""
Improved ER Diagram Validator for Database Structure.

This script validates that the database structure correctly follows
the entity-relationship diagram as defined in the project specification.
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from sqlalchemy import inspect, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_path():
    """
    Get the path to the SQLite database file.

    Returns:
        str: Path to the database file
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / 'data'
    return str(data_dir / 'leatherworking_database.db')


def get_db_session():
    """
    Create a database session.

    Returns:
        Session: SQLAlchemy session
    """
    try:
        db_path = get_database_path()
        logger.info(f"Using database: {db_path}")
        engine = create_engine(f"sqlite:///{db_path}")
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        sys.exit(1)


class ERDiagramParser:
    """Parse ER diagram from markdown file."""

    def __init__(self, file_path: str):
        """
        Initialize the ER diagram parser.

        Args:
            file_path: Path to the ER diagram markdown file
        """
        self.file_path = file_path
        self.entities = {}
        self.relationships = []
        logger.info(f"Parsing ER diagram from: {file_path}")

    def parse(self) -> Dict[str, Any]:
        """
        Parse the ER diagram file.

        Returns:
            Dict containing 'entities' and 'relationships'
        """
        try:
            # Check if file exists
            if not os.path.exists(self.file_path):
                logger.error(f"ER diagram file not found: {self.file_path}")
                logger.info("Searching for ER diagram in common locations...")

                # Try to find the file in common locations
                base_dir = Path(__file__).resolve().parent
                possible_locations = [
                    base_dir / 'tests' / 'er_diagram.md',
                    base_dir / 'docs' / 'er_diagram.md',
                    base_dir / 'er_diagram.md'
                ]

                for loc in possible_locations:
                    if os.path.exists(loc):
                        logger.info(f"Found ER diagram at: {loc}")
                        self.file_path = str(loc)
                        break
                else:
                    # Create a simple sample if none found
                    logger.warning("No ER diagram found, using a simple sample for testing.")
                    return self._create_sample_diagram()

            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Print a small sample of the content for debugging
            logger.info(f"ER Diagram content sample (first 200 chars): {content[:200]}...")

            # Extract entity definitions - looking for patterns like:
            # Customer {
            #     int id
            #     str name
            #     str email
            #     CustomerStatus status
            # }
            entity_blocks = re.findall(r'(\w+)\s*{([^}]+)}', content)

            for entity_name, entity_body in entity_blocks:
                # Process entity attributes
                attributes = []
                for line in entity_body.strip().split('\n'):
                    line = line.strip()
                    if line and ' ' in line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            attr_type, attr_name = parts
                            attributes.append({
                                'name': attr_name.strip(),
                                'type': attr_type.strip()
                            })

                self.entities[entity_name] = {
                    'name': entity_name,
                    'attributes': attributes
                }

            logger.info(f"Found {len(self.entities)} entities in ER diagram")
            logger.debug(f"Entities: {list(self.entities.keys())}")

            # Extract relationships with a more flexible pattern
            relationship_text = re.findall(r'(\w+)\s+(\|\||}\||}\{|\{\|)--(\|\||o\{|\|\{|o\|)\s+(\w+)\s+:\s+([^\n]+)',
                                           content)

            for match in relationship_text:
                if len(match) >= 5:
                    entity1, rel_start, rel_end, entity2, description = match
                    self.relationships.append({
                        'entity1': entity1.strip(),
                        'entity2': entity2.strip(),
                        'type': f"{rel_start}--{rel_end}",
                        'description': description.strip()
                    })

            logger.info(f"Found {len(self.relationships)} relationships in ER diagram")
            logger.debug(f"First few relationships: {self.relationships[:3] if self.relationships else 'None'}")

            return {
                'entities': self.entities,
                'relationships': self.relationships
            }
        except Exception as e:
            logger.error(f"Error parsing ER diagram: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'entities': {}, 'relationships': []}

    def _create_sample_diagram(self) -> Dict[str, Any]:
        """Create a simple sample diagram for testing."""
        return {
            'entities': {
                'Product': {
                    'name': 'Product',
                    'attributes': [
                        {'name': 'id', 'type': 'int'},
                        {'name': 'name', 'type': 'str'},
                        {'name': 'price', 'type': 'float'}
                    ]
                },
                'Customer': {
                    'name': 'Customer',
                    'attributes': [
                        {'name': 'id', 'type': 'int'},
                        {'name': 'name', 'type': 'str'},
                        {'name': 'email', 'type': 'str'}
                    ]
                }
            },
            'relationships': [
                {
                    'entity1': 'Customer',
                    'entity2': 'Product',
                    'type': '||--o{',
                    'description': 'purchases'
                }
            ]
        }


class DatabaseDiagnostics:
    """Base diagnostics for database structure."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize with an optional session.

        Args:
            session: SQLAlchemy session or None to create a new one
        """
        self.session = session or get_db_session()

    def verify_table_existence(self) -> Dict[str, bool]:
        """
        Verify existence of tables in the database.

        Returns:
            Dict[str, bool]: Table names and existence status
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

        existing_tables = inspector.get_table_names()
        table_existence = {}

        for table in tables_to_check:
            table_existence[table] = table in existing_tables

        return table_existence

    def count_records_per_table(self) -> Dict[str, int]:
        """
        Count records for each table in the database.

        Returns:
            Dict[str, int]: Table names and record counts
        """
        inspector = inspect(self.session.bind)
        tables = inspector.get_table_names()

        record_counts = {}
        for table in tables:
            try:
                # Use text() to explicitly mark SQL statements
                result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                record_counts[table] = count
            except SQLAlchemyError as e:
                logger.error(f"Error counting records for {table}: {e}")
                record_counts[table] = -1

        return record_counts

    def get_foreign_keys(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get foreign key information for all tables.

        Returns:
            Dict[str, List[Dict[str, str]]]: Foreign key information by table
        """
        inspector = inspect(self.session.bind)
        tables = inspector.get_table_names()

        foreign_keys = {}
        for table in tables:
            try:
                fks = inspector.get_foreign_keys(table)
                foreign_keys[table] = fks
            except Exception as e:
                logger.error(f"Error getting foreign keys for {table}: {e}")
                foreign_keys[table] = []

        return foreign_keys

    def run_full_database_diagnostics(self) -> Dict[str, Any]:
        """
        Run a comprehensive database diagnostic check.

        Returns:
            Dict[str, Any]: Various diagnostic results
        """
        diagnostics_results = {
            'table_existence': self.verify_table_existence(),
            'record_counts': self.count_records_per_table(),
            'foreign_keys': self.get_foreign_keys()
        }

        return diagnostics_results

    def print_diagnostics_report(self, diagnostics: Optional[Dict[str, Any]] = None):
        """
        Print a formatted diagnostic report.

        Args:
            diagnostics: Diagnostic results or None to run diagnostics
        """
        if diagnostics is None:
            diagnostics = self.run_full_database_diagnostics()

        print("\n=== DATABASE DIAGNOSTICS REPORT ===")

        # Table Existence
        print("\nTable Existence:")
        for table, exists in diagnostics['table_existence'].items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{table}: {status}")

        # Record Counts
        print("\nRecord Counts:")
        for table, count in diagnostics['record_counts'].items():
            print(f"{table}: {count} records")

        # Foreign Keys
        print("\nForeign Keys:")
        for table, fks in diagnostics['foreign_keys'].items():
            if fks:
                print(f"\n{table} Foreign Keys:")
                for fk in fks:
                    ref_table = fk.get('referred_table', 'Unknown')
                    constrained_cols = fk.get('constrained_columns', [])
                    referred_cols = fk.get('referred_columns', [])

                    for idx, col in enumerate(constrained_cols):
                        ref_col = referred_cols[idx] if idx < len(referred_cols) else 'Unknown'
                        print(f"  - {col} -> {ref_table}.{ref_col}")


class ERDiagramValidator:
    """Validate database structure against ER diagram."""

    def __init__(self, session: Optional[Session] = None, er_diagram_path: Optional[str] = None):
        """
        Initialize the ER diagram validator.

        Args:
            session: SQLAlchemy session
            er_diagram_path: Path to the ER diagram file
        """
        self.session = session or get_db_session()
        base_dir = Path(__file__).resolve().parent
        self.er_diagram_path = er_diagram_path or str(base_dir / 'tests' / 'er_diagram.md')
        self.db_diagnostics = DatabaseDiagnostics(session=self.session)

    def _get_database_metadata(self) -> Dict[str, Any]:
        """
        Get database metadata.

        Returns:
            Dict containing metadata about tables, columns, and relationships
        """
        try:
            inspector = inspect(self.session.bind)
            tables = inspector.get_table_names()

            metadata = {
                'tables': {},
                'foreign_keys': []
            }

            for table_name in tables:
                # Get columns
                columns = inspector.get_columns(table_name)
                column_info = {}
                for column in columns:
                    column_info[column['name']] = {
                        'type': str(column['type']),
                        'nullable': column['nullable'],
                        'primary_key': column.get('primary_key', False)
                    }

                # Get foreign keys
                fks = inspector.get_foreign_keys(table_name)

                metadata['tables'][table_name] = {
                    'columns': column_info,
                    'foreign_keys': fks
                }

                # Add foreign keys to global list
                for fk in fks:
                    metadata['foreign_keys'].append({
                        'source_table': table_name,
                        'source_column': fk['constrained_columns'][0] if fk['constrained_columns'] else None,
                        'target_table': fk['referred_table'],
                        'target_column': fk['referred_columns'][0] if fk['referred_columns'] else None
                    })

            return metadata
        except Exception as e:
            logger.error(f"Error getting database metadata: {e}")
            return {'tables': {}, 'foreign_keys': []}

    def _map_entity_to_table_name(self, entity_name: str) -> str:
        """
        Map entity name from ER diagram to table name in database.

        Args:
            entity_name: Entity name from ER diagram

        Returns:
            Corresponding table name
        """
        # Handle different possible conversions

        # First try direct lowercase match (most common)
        lower_name = entity_name.lower()

        # Special cases for irregular plurals or common patterns
        if entity_name == 'PickingList':
            return 'picking_lists'
        elif entity_name == 'ToolList':
            return 'tool_lists'
        elif entity_name == 'SalesItem':
            return 'sales_items'
        elif entity_name == 'ProductInventory':
            return 'product_inventories'
        elif entity_name == 'MaterialInventory':
            return 'material_inventories'
        elif entity_name == 'LeatherInventory':
            return 'leather_inventories'
        elif entity_name == 'HardwareInventory':
            return 'hardware_inventories'
        elif entity_name == 'ToolInventory':
            return 'tool_inventories'

        # For CamelCase entities, convert to snake_case plural
        if any(c.isupper() for c in entity_name[1:]):
            # Convert CamelCase to snake_case
            snake_case = ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in entity_name]).lstrip('_')
            # Pluralize
            if snake_case.endswith('y'):
                return snake_case[:-1] + 'ies'
            elif snake_case.endswith('s'):
                return snake_case + 'es'
            else:
                return snake_case + 's'

        # Default pluralization strategy
        if lower_name.endswith('y'):
            return lower_name[:-1] + 'ies'
        elif lower_name.endswith('s'):
            return lower_name + 'es'
        else:
            return lower_name + 's'

    def _map_attribute_to_column_name(self, attr_name: str) -> str:
        """
        Map attribute name from ER diagram to column name in database.

        Args:
            attr_name: Attribute name from ER diagram

        Returns:
            Corresponding column name
        """
        # Check for CamelCase and convert to snake_case
        if any(c.isupper() for c in attr_name[1:]):
            # Convert CamelCase to snake_case
            return ''.join(['_' + c.lower() if c.isupper() else c.lower() for c in attr_name]).lstrip('_')

        # Otherwise just return lowercase
        return attr_name.lower()

    def validate_table_existence(self, er_entities: Dict[str, Any], db_metadata: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that all entities in the ER diagram exist as tables in the database.

        Args:
            er_entities: Entities from ER diagram
            db_metadata: Database metadata

        Returns:
            Dict of entity names and their existence status
        """
        table_existence = {}

        for entity_name in er_entities:
            table_name = self._map_entity_to_table_name(entity_name)
            table_existence[entity_name] = table_name in db_metadata['tables']

        return table_existence

    def validate_columns(self, er_entities: Dict[str, Any], db_metadata: Dict[str, Any]) -> Dict[str, Dict[str, bool]]:
        """
        Validate that all attributes in the ER diagram exist as columns in the database.

        Args:
            er_entities: Entities from ER diagram
            db_metadata: Database metadata

        Returns:
            Dict of entity names and their attribute existence status
        """
        column_validation = {}

        for entity_name, entity_data in er_entities.items():
            table_name = self._map_entity_to_table_name(entity_name)

            if table_name not in db_metadata['tables']:
                # Skip validation if table doesn't exist
                column_validation[entity_name] = {
                    attr['name']: False for attr in entity_data['attributes']
                }
                continue

            table_columns = db_metadata['tables'][table_name]['columns']
            entity_attrs = {}

            for attr in entity_data['attributes']:
                # Skip attributes that are relationships
                if attr['type'].startswith('fk') or attr['type'] == 'rel':
                    continue

                attr_name = attr['name']
                column_name = self._map_attribute_to_column_name(attr_name)

                # Check if attribute exists as column
                entity_attrs[attr_name] = column_name in table_columns

                # If not found, try with _id suffix for foreign keys
                if not entity_attrs[attr_name] and not column_name.endswith('_id'):
                    entity_attrs[attr_name] = (column_name + '_id') in table_columns

            column_validation[entity_name] = entity_attrs

        return column_validation

    def validate_relationships(self, er_relationships: List[Dict[str, Any]], db_metadata: Dict[str, Any]) -> List[
        Dict[str, Any]]:
        """
        Validate that all relationships in the ER diagram exist as foreign keys in the database.

        Args:
            er_relationships: Relationships from ER diagram
            db_metadata: Database metadata

        Returns:
            List of relationship validations
        """
        relationship_validations = []

        for rel in er_relationships:
            entity1 = rel['entity1']
            entity2 = rel['entity2']
            rel_type = rel.get('type', '')
            description = rel.get('description', '')

            table1 = self._map_entity_to_table_name(entity1)
            table2 = self._map_entity_to_table_name(entity2)

            # Check if tables exist
            if table1 not in db_metadata['tables'] or table2 not in db_metadata['tables']:
                relationship_validations.append({
                    'entity1': entity1,
                    'entity2': entity2,
                    'rel_type': rel_type,
                    'description': description,
                    'exists': False,
                    'reason': 'One or both tables do not exist'
                })
                continue

            # Check for junction table for many-to-many relationships
            if 'o{--o{' in rel_type or '}o--o{' in rel_type or '}o--}o' in rel_type:
                # Look for junction table
                entity1_lower = entity1.lower()
                entity2_lower = entity2.lower()

                junction_options = [
                    f"{entity1_lower}_{entity2_lower}",
                    f"{entity2_lower}_{entity1_lower}",
                    f"{entity1_lower}{entity2_lower}",
                    f"{entity2_lower}{entity1_lower}"
                ]

                junction_found = False

                for junction_name in junction_options:
                    if junction_name in db_metadata['tables']:
                        junction_found = True
                        break

                if not junction_found:
                    relationship_validations.append({
                        'entity1': entity1,
                        'entity2': entity2,
                        'rel_type': rel_type,
                        'description': description,
                        'exists': False,
                        'reason': 'Junction table not found for many-to-many relationship'
                    })
                    continue

            # Check for foreign key from entity1 to entity2
            fk_entity1_to_entity2 = next((fk for fk in db_metadata['foreign_keys']
                                          if fk['source_table'] == table1 and
                                          fk['target_table'] == table2), None)

            # Check for foreign key from entity2 to entity1
            fk_entity2_to_entity1 = next((fk for fk in db_metadata['foreign_keys']
                                          if fk['source_table'] == table2 and
                                          fk['target_table'] == table1), None)

            # Determine if the relationship is valid based on the type
            relationship_exists = False
            matching_fk = None

            if '||--||' in rel_type:  # one-to-one
                relationship_exists = bool(fk_entity1_to_entity2 or fk_entity2_to_entity1)
                matching_fk = fk_entity1_to_entity2 or fk_entity2_to_entity1
            elif '||--o{' in rel_type:  # one-to-many
                relationship_exists = bool(fk_entity2_to_entity1)
                matching_fk = fk_entity2_to_entity1
            elif '||--o|' in rel_type:  # one-to-many (optional)
                relationship_exists = bool(fk_entity2_to_entity1)
                matching_fk = fk_entity2_to_entity1
            elif '}o--||' in rel_type:  # many-to-one
                relationship_exists = bool(fk_entity1_to_entity2)
                matching_fk = fk_entity1_to_entity2
            else:  # Default case or many-to-many (should have been checked above)
                relationship_exists = bool(fk_entity1_to_entity2 or fk_entity2_to_entity1)
                matching_fk = fk_entity1_to_entity2 or fk_entity2_to_entity1

            relationship_validations.append({
                'entity1': entity1,
                'entity2': entity2,
                'rel_type': rel_type,
                'description': description,
                'exists': relationship_exists,
                'matching_fk': matching_fk
            })

        return relationship_validations

    def validate_against_er_diagram(self) -> Dict[str, Any]:
        """
        Validate the database structure against the ER diagram.

        Returns:
            Dict containing validation results
        """
        # Parse ER diagram
        parser = ERDiagramParser(self.er_diagram_path)
        er_diagram = parser.parse()

        # Get database metadata
        db_metadata = self._get_database_metadata()

        # Validate
        table_existence = self.validate_table_existence(er_diagram['entities'], db_metadata)
        column_validation = self.validate_columns(er_diagram['entities'], db_metadata)
        relationship_validation = self.validate_relationships(er_diagram['relationships'], db_metadata)

        # Get existing database diagnostics
        db_diagnostics = self.db_diagnostics.run_full_database_diagnostics()

        # Calculate validation summary
        entity_count = len(er_diagram['entities'])
        existing_entity_count = sum(1 for exists in table_existence.values() if exists)
        entity_percentage = (existing_entity_count / entity_count * 100) if entity_count > 0 else 0

        column_count = sum(len(attrs) for attrs in column_validation.values())
        existing_column_count = sum(sum(1 for exists in attrs.values() if exists)
                                    for attrs in column_validation.values())
        column_percentage = (existing_column_count / column_count * 100) if column_count > 0 else 0

        relationship_count = len(relationship_validation)
        existing_relationship_count = sum(1 for rel in relationship_validation if rel['exists'])
        relationship_percentage = (
                    existing_relationship_count / relationship_count * 100) if relationship_count > 0 else 0

        # Combine results
        validation_results = {
            'er_diagram_validation': {
                'table_existence': table_existence,
                'column_validation': column_validation,
                'relationship_validation': relationship_validation,
                'summary': {
                    'entity_percentage': entity_percentage,
                    'column_percentage': column_percentage,
                    'relationship_percentage': relationship_percentage
                }
            },
            'database_diagnostics': db_diagnostics
        }

        return validation_results

    def print_validation_report(self, validation_results: Optional[Dict[str, Any]] = None):
        """
        Print a formatted validation report.

        Args:
            validation_results: Validation results to print.
                              If None, runs validation.
        """
        if validation_results is None:
            validation_results = self.validate_against_er_diagram()

        er_validation = validation_results['er_diagram_validation']

        print("\n=== ER DIAGRAM VALIDATION REPORT ===")

        # Summary
        summary = er_validation.get('summary', {})
        print("\nValidation Summary:")
        print(f"  Entity-Table Mapping: {summary.get('entity_percentage', 0):.1f}% match")
        print(f"  Column-Attribute Mapping: {summary.get('column_percentage', 0):.1f}% match")
        print(f"  Relationship Mapping: {summary.get('relationship_percentage', 0):.1f}% match")

        # Table Existence
        print("\nEntity-Table Mapping Validation:")
        table_existence = er_validation['table_existence']
        for entity, exists in table_existence.items():
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{entity} -> {self._map_entity_to_table_name(entity)}: {status}")

        # Column Validation
        print("\nEntity Attribute Validation:")
        column_validation = er_validation['column_validation']
        for entity, attributes in column_validation.items():
            if not attributes:  # Skip if no attributes
                continue

            print(f"\n{entity} Attributes:")
            for attr, exists in attributes.items():
                status = "✓ EXISTS" if exists else "✗ MISSING"
                print(f"  - {attr} -> {self._map_attribute_to_column_name(attr)}: {status}")

        # Relationship Validation
        print("\nRelationship Validation:")
        relationship_validation = er_validation['relationship_validation']
        for rel in relationship_validation:
            status = "✓ EXISTS" if rel['exists'] else "✗ MISSING"
            print(
                f"{rel['entity1']} <-> {rel['entity2']} ({rel.get('description', rel.get('rel_type', 'unknown'))}): {status}")
            if rel['exists'] and rel.get('matching_fk'):
                fk = rel['matching_fk']
                print(
                    f"  - FK: {fk['source_table']}.{fk['source_column']} -> {fk['target_table']}.{fk['target_column']}")
            elif not rel['exists'] and 'reason' in rel:
                print(f"  - Reason: {rel['reason']}")

        # Print regular database diagnostics
        self.db_diagnostics.print_diagnostics_report(validation_results['database_diagnostics'])


def main():
    """
    Main function for running the ER diagram validation.
    """
    print("Running Improved ER Diagram Validation...")

    try:
        er_path = None
        if len(sys.argv) > 1:
            er_path = sys.argv[1]

        validator = ERDiagramValidator(er_diagram_path=er_path)
        validation_results = validator.validate_against_er_diagram()
        validator.print_validation_report(validation_results)
    except Exception as e:
        logger.error(f"ER diagram validation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()