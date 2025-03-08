#!/usr/bin/env python
# tests/betsy_validation/validate_er_diagram.py
"""
Improved script to validate the ER diagram against the actual model implementations.
"""
import os
import sys
import re
import logging
import json
from collections import defaultdict
import traceback

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("er_diagram_validator")

# Import circular import resolver
try:
    from utils.circular_import_resolver import get_class, register_lazy_import
except ImportError:
    logger.error("Failed to import circular_import_resolver. Make sure it's available.")
    sys.exit(1)


def snake_to_camel(snake_str):
    """Convert snake_case to CamelCase."""
    return ''.join(x.capitalize() for x in snake_str.lower().split('_'))


def parse_er_diagram(er_file_path):
    """Parse the ER diagram to extract entities and their attributes."""
    if not os.path.exists(er_file_path):
        logger.error(f"ER diagram file not found: {er_file_path}")
        return None

    with open(er_file_path, 'r') as f:
        content = f.read()

    # Remove the relationship lines to avoid capturing "o" from relationship symbols
    content_no_relations = re.sub(r'\w+\s+\|\|--[o|][{|\|]\s+\w+.*?:', '', content, flags=re.DOTALL)

    # Regular expression to find entity definitions
    entity_pattern = r'(\w+)\s*{([^}]*)}'
    entities = {}

    for match in re.finditer(entity_pattern, content_no_relations):
        entity_name = match.group(1)
        attributes_block = match.group(2)

        # Skip the "o" entity which is likely a parsing artifact
        if entity_name.lower() == 'o':
            continue

        # Extract attributes
        attribute_lines = [line.strip() for line in attributes_block.strip().split('\n')]
        attributes = {}

        for line in attribute_lines:
            if line:
                parts = line.split(None, 1)  # Split by whitespace
                if len(parts) == 2:
                    attr_type, attr_name = parts
                    attributes[attr_name] = attr_type

        entities[entity_name] = attributes

    # Extract relationships
    relationships = []
    relationship_pattern = r'(\w+)\s+(\|\|--\|{|\|\|--o{|\}o--\|\||\}\|--\|\|)\s+(\w+)'

    for match in re.finditer(relationship_pattern, content):
        source = match.group(1)
        rel_type = match.group(2)
        target = match.group(3)
        relationships.append((source, rel_type, target))

    return {
        'entities': entities,
        'relationships': relationships
    }


def get_model_attributes(model_class):
    """Extract attributes from a SQLAlchemy model class."""
    attributes = {}

    # Get the table object if available
    if hasattr(model_class, '__table__'):
        for column in model_class.__table__.columns:
            attributes[column.name] = str(column.type)

    return attributes


def get_model_relationships(model_class):
    """Extract relationships from a SQLAlchemy model class."""
    relationships = []

    # Look for relationship attributes in the class
    if hasattr(model_class, '__mapper__') and hasattr(model_class.__mapper__, 'relationships'):
        for name, rel in model_class.__mapper__.relationships.items():
            target_class = rel.mapper.class_
            target_name = target_class.__name__
            relationships.append((model_class.__name__, name, target_name))

    return relationships


def snake_case(camel_case_str):
    """Convert CamelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_module_name_candidates(model_name):
    """Get potential module names for a model class."""
    # Convert model name to snake case for module naming
    snake_name = snake_case(model_name)

    # Generate possible module names
    candidates = [
        snake_name,
        snake_name.lower(),
        snake_name.replace('_', ''),
        model_name.lower(),
        # Handle common naming patterns
        snake_name + 's',  # plural
        snake_name.replace('_item', '_items'),
        snake_name.replace('_list', '_lists'),
        snake_name.replace('_inventory', '_inventories'),
    ]

    # Components are often in a single module
    if 'component' in snake_name.lower():
        candidates.append('components')

    # Some items might be in parent modules
    if '_' in snake_name:
        parent_module = snake_name.split('_')[0]
        candidates.append(parent_module)

    # Remove duplicates
    return list(set(candidates))


def load_model_classes_from_paths():
    """Load model classes by trying different import paths."""
    models = {}

    # Expected models based on ER diagram
    expected_models = [
        'Customer', 'Sales', 'SalesItem', 'Product', 'ProductPattern', 'Purchase',
        'PurchaseItem', 'Supplier', 'ProductInventory', 'MaterialInventory',
        'LeatherInventory', 'HardwareInventory', 'ToolInventory', 'Project',
        'Pattern', 'Component', 'Material', 'Leather', 'Hardware', 'Tool',
        'ComponentMaterial', 'ComponentLeather', 'ComponentHardware', 'ComponentTool',
        'ProjectComponent', 'PickingList', 'PickingListItem', 'ToolList', 'ToolListItem',
        'Storage'
    ]

    # Try to load each model class
    for model_name in expected_models:
        # Skip 'o' which is not a real model
        if model_name.lower() == 'o':
            continue

        # Get possible module names
        module_candidates = get_module_name_candidates(model_name)

        # Try each possible path
        for module_name in module_candidates:
            try:
                # First try the direct module
                model_class = get_class(f'database.models.{module_name}', model_name)
                if model_class:
                    models[model_name] = model_class
                    logger.debug(f"Loaded model: {model_name} from database.models.{module_name}")
                    break
            except Exception as e:
                # Try direct import from database.models
                try:
                    model_class = get_class('database.models', model_name)
                    if model_class:
                        models[model_name] = model_class
                        logger.debug(f"Loaded model: {model_name} directly from database.models")
                        break
                except Exception as e2:
                    continue  # Try next candidate

    # Look for models in special modules like components, inventory
    special_modules = ['components', 'inventory', 'sales', 'purchase', 'tool', 'picking_list']

    for module_name in special_modules:
        try:
            # Import the module and look for expected model classes
            module = __import__(f'database.models.{module_name}', fromlist=['*'])
            for attr_name in dir(module):
                # Skip private attributes
                if attr_name.startswith('_'):
                    continue

                attr = getattr(module, attr_name)

                # Check if it's a class and in our expected list
                if isinstance(attr, type) and attr_name in expected_models and attr_name not in models:
                    models[attr_name] = attr
                    logger.debug(f"Loaded model: {attr_name} from module {module_name}")
        except ImportError:
            continue  # Module doesn't exist, skip it

    return models


def validate_entities(er_entities, models):
    """Validate that all entities in the ER diagram exist as models."""
    missing_models = set(er_entities.keys()) - set(models.keys())
    extra_models = set(models.keys()) - set(er_entities.keys()) - {'Base', 'BaseModel'}

    if missing_models:
        logger.error(f"Entities in ER diagram but missing in code: {missing_models}")
    else:
        logger.info("All entities in ER diagram have corresponding models in the code.")

    if extra_models:
        logger.warning(f"Models in code but not in ER diagram: {extra_models}")

    return not missing_models


def validate_attributes(er_entities, models):
    """Validate that attributes in the ER diagram match model attributes."""
    validation_results = defaultdict(list)

    for entity_name, er_attributes in er_entities.items():
        if entity_name not in models:
            # Already handled in validate_entities
            continue

        model_class = models[entity_name]
        model_attrs = get_model_attributes(model_class)

        # Check for attributes in ER diagram but missing in model
        for attr_name in er_attributes:
            if attr_name not in model_attrs:
                validation_results[entity_name].append(
                    f"Attribute '{attr_name}' is in ER diagram but missing in model"
                )

        # Check for attributes in model but missing in ER diagram
        required_model_attrs = {"id", "created_at", "updated_at", "uuid", "is_deleted", "deleted_at"}
        for attr_name in model_attrs:
            if attr_name not in er_attributes and attr_name not in required_model_attrs:
                validation_results[entity_name].append(
                    f"Attribute '{attr_name}' is in model but missing in ER diagram"
                )

    has_issues = False
    for entity_name, issues in validation_results.items():
        if issues:
            has_issues = True
            logger.warning(f"Issues with {entity_name}:")
            for issue in issues:
                logger.warning(f"  - {issue}")

    if not has_issues:
        logger.info("All entity attributes in ER diagram match model attributes (with common exceptions).")

    return not has_issues


def suggest_fixes(er_entities, models):
    """Suggest fixes for any discrepancies between ER diagram and models."""
    # First suggest updating the ER diagram
    logger.info("\n=== ER DIAGRAM UPDATES ===")
    for model_name, model_class in models.items():
        if model_name not in er_entities:
            if model_name.endswith('Base'):
                continue  # Skip base classes

            logger.info(f"Suggested addition to ER diagram for {model_name}:")
            attrs = get_model_attributes(model_class)
            logger.info(f"{model_name} {{")
            for attr_name, attr_type in attrs.items():
                # Skip standard attributes
                if attr_name not in {"created_at", "updated_at", "uuid", "is_deleted", "deleted_at"}:
                    logger.info(f"    {map_sqlalchemy_type_to_er(attr_type)} {attr_name}")
            logger.info("}")
            logger.info("")

    # Then suggest model implementations
    logger.info("\n=== MODEL IMPLEMENTATIONS ===")
    for entity_name, er_attributes in er_entities.items():
        if entity_name not in models:
            module_name = snake_case(entity_name)
            logger.info(f"Suggested model implementation for {entity_name}:")
            logger.info(f"""
# database/models/{module_name}.py
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from database.models.base import Base
from database.models.enums import *

class {entity_name}(Base):
    __tablename__ = '{module_name}s'

    # Add attributes from ER diagram
    id = Column(Integer, primary_key=True)
""")
            for attr_name, attr_type in er_attributes.items():
                if attr_name != "id":  # Skip id which is already added
                    logger.info(f"    {attr_name} = Column({map_er_type_to_sqlalchemy(attr_type)})")
            logger.info("")


def map_er_type_to_sqlalchemy(er_type):
    """Map ER diagram types to SQLAlchemy column types."""
    type_map = {
        'int': 'Integer',
        'str': 'String',
        'float': 'Float',
        'bool': 'Boolean',
        'datetime': 'DateTime',
        'json': 'JSON',
    }

    # Handle enum types
    if er_type in {
        'CustomerStatus', 'CustomerTier', 'SaleStatus', 'PaymentStatus',
        'ProjectStatus', 'ProjectType', 'ComponentType', 'MaterialType',
        'InventoryStatus', 'LeatherType', 'HardwareType', 'ToolType',
        'SkillLevel', 'QualityGrade', 'MeasurementUnit', 'PurchaseStatus',
        'PickingListStatus', 'ToolListStatus', 'SupplierStatus'
    }:
        return f'Enum({er_type})'

    return type_map.get(er_type, 'String')


def map_sqlalchemy_type_to_er(sqlalchemy_type):
    """Map SQLAlchemy column types to ER diagram types."""
    type_map = {
        'INTEGER': 'int',
        'VARCHAR': 'str',
        'TEXT': 'str',
        'FLOAT': 'float',
        'BOOLEAN': 'bool',
        'DATETIME': 'datetime',
        'JSON': 'json',
    }

    # Extract the base type from SQLAlchemy type string
    base_type = sqlalchemy_type.split('(')[0].upper()

    return type_map.get(base_type, 'str')


def print_detailed_report(er_entities, models):
    """Print a detailed report of model mapping."""
    logger.info("\n=== DETAILED REPORT ===")

    # Print entity statistics
    total_entities = len(er_entities)
    loaded_models = len(models)
    missing_models = total_entities - loaded_models

    logger.info(f"Total entities in ER diagram: {total_entities}")
    logger.info(f"Successfully loaded models: {loaded_models}")
    logger.info(f"Missing models: {missing_models}")

    # Print loaded models
    if loaded_models > 0:
        logger.info("\nSuccessfully loaded models:")
        for model_name in sorted(models.keys()):
            model_class = models[model_name]
            attrs = get_model_attributes(model_class)
            logger.info(f"  - {model_name} ({len(attrs)} attributes)")

    # Print missing models
    if missing_models > 0:
        logger.info("\nMissing models:")
        for entity_name in sorted(set(er_entities.keys()) - set(models.keys())):
            er_attrs = er_entities[entity_name]
            logger.info(f"  - {entity_name} ({len(er_attrs)} attributes in ER diagram)")

    # Print relationship stats
    logger.info("\nRelationship statistics:")
    total_relationships = sum(len(get_model_relationships(model)) for model in models.values())
    logger.info(f"  - Total relationships in loaded models: {total_relationships}")


def try_importing_model_from_components(model_name):
    """Specially handle components module which may contain multiple model classes."""
    try:
        # Import the components module
        from database.models.components import (
            Component, PatternComponent, ProjectComponent,
            ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool
        )

        # Map component class names to classes
        component_classes = {
            'Component': Component,
            'PatternComponent': PatternComponent,
            'ProjectComponent': ProjectComponent,
            'ComponentMaterial': ComponentMaterial,
            'ComponentLeather': ComponentLeather,
            'ComponentHardware': ComponentHardware,
            'ComponentTool': ComponentTool
        }

        # Return the requested class if it exists
        if model_name in component_classes:
            return component_classes[model_name]
    except Exception as e:
        pass

    return None


def main():
    """Main function to run the ER diagram validation."""
    er_file_path = os.path.join(os.path.dirname(__file__), 'er_diagram.md')

    logger.info(f"Starting ER diagram validation for: {er_file_path}")

    # Parse ER diagram
    er_data = parse_er_diagram(er_file_path)
    if not er_data:
        logger.error("Failed to parse ER diagram")
        return 1

    logger.info(f"Found {len(er_data['entities'])} entities in ER diagram")
    logger.info(f"Found {len(er_data['relationships'])} relationships in ER diagram")

    # Try to import components specially
    component_models = {}
    try:
        component_models = {
            'Component': try_importing_model_from_components('Component'),
            'ComponentMaterial': try_importing_model_from_components('ComponentMaterial'),
            'ComponentLeather': try_importing_model_from_components('ComponentLeather'),
            'ComponentHardware': try_importing_model_from_components('ComponentHardware'),
            'ComponentTool': try_importing_model_from_components('ComponentTool'),
            'ProjectComponent': try_importing_model_from_components('ProjectComponent'),
        }
        # Remove None values
        component_models = {k: v for k, v in component_models.items() if v is not None}
    except Exception as e:
        logger.warning(f"Error importing component models: {e}")

    # Load model classes
    models = load_model_classes_from_paths()

    # Add component models
    models.update(component_models)

    logger.info(f"Loaded {len(models)} model classes")

    # Print detailed report
    print_detailed_report(er_data['entities'], models)

    # Validate entities
    entities_valid = validate_entities(er_data['entities'], models)

    # Validate attributes
    attributes_valid = validate_attributes(er_data['entities'], models)

    # Suggest fixes if there are issues
    if not entities_valid or not attributes_valid:
        logger.info("\nSuggested fixes:")
        suggest_fixes(er_data['entities'], models)

    # Report overall status
    if entities_valid and attributes_valid:
        logger.info("ER Diagram Validation: PASSED")
        return 0
    else:
        logger.error("ER Diagram Validation: FAILED - See above for details")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)