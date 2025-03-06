# store_management/tests/minimal_er_validator.py
"""
A minimal ER diagram validator that extracts model classes directly from Python files
using regular expressions, avoiding any import errors.
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class MinimalERValidator:
    def __init__(self, er_diagram_path: str, models_path: str):
        """
        Initialize the ER Diagram Validator with path settings.

        Args:
            er_diagram_path (str): Path to the ER diagram file
            models_path (str): Path to the models directory
        """
        self.er_diagram_path = os.path.abspath(er_diagram_path)
        self.models_path = os.path.abspath(models_path)
        self.entities = set()
        self.relationships = []
        self.model_classes = {}
        self.matched_entities = {}
        self.missing_entities = []

        # Define name matching rules for common entity names
        self.name_matching_rules = {
            'Material': [
                'Material', 'MaterialItem', 'MaterialInventory',
                'ComponentMaterial'
            ],
            'Inventory': [
                'Inventory', 'ProductInventory', 'MaterialInventory',
                'LeatherInventory', 'HardwareInventory', 'ToolInventory'
            ],
            'Sales': [
                'Sales', 'Sale', 'SalesOrder', 'Order'
            ],
            'SalesItem': [
                'SalesItem', 'SaleItem', 'OrderItem'
            ],
            'PickingList': [
                'PickingList', 'PickingListItem', 'Picking'
            ],
            'Component': [
                'Component', 'ComponentMaterial', 'ProjectComponent', 'PatternComponent'
            ],
            'Project': [
                'Project', 'ProjectComponent'
            ],
            'Pattern': [
                'Pattern', 'PatternComponent', 'ProductPattern'
            ]
        }

    def parse_er_diagram(self):
        """Parse the ER diagram to extract entities and relationships."""
        try:
            with open(self.er_diagram_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Extract entities
                entity_matches = re.findall(r'##\s*([A-Za-z]+(?:\s+[A-Za-z]+)*)\s*{', content)
                self.entities = set(entity.strip() for entity in entity_matches)
                print(f"Found {len(self.entities)} entities in ER diagram:")
                for entity in sorted(self.entities):
                    print(f"  - {entity}")

                # Extract relationships
                relationship_patterns = [
                    r'([A-Za-z]+)\s*-->\s*([A-Za-z]+)',  # Arrow
                    r'([A-Za-z]+)\s*--\s*([A-Za-z]+)',  # Dash
                    r'([A-Za-z]+)\s*\|\|\s*--\s*([A-Za-z]+)'  # Advanced
                ]

                for pattern in relationship_patterns:
                    matches = re.findall(pattern, content)
                    self.relationships.extend(matches)

                print(f"Found {len(self.relationships)} relationships in ER diagram")

        except Exception as e:
            print(f"Error parsing ER diagram: {e}")
            raise

    def extract_models_from_files(self):
        """Extract model classes directly from Python files using regex."""
        if not os.path.exists(self.models_path):
            print(f"Models directory not found: {self.models_path}")
            return

        print(f"Looking for models in: {self.models_path}")

        # Patterns to extract model classes
        class_pattern = r'class\s+([A-Za-z0-9_]+).*?__tablename__\s*=\s*[\'\"]([A-Za-z0-9_]+)[\'\"](.*?)(?=class|\Z)'

        for filename in os.listdir(self.models_path):
            if filename.endswith('.py') and filename != '__init__.py':
                file_path = os.path.join(self.models_path, filename)
                module_name = filename[:-3]

                print(f"Scanning {filename}...")

                try:
                    # Read file as text
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find all class definitions with __tablename__
                    matches = re.findall(class_pattern, content, re.DOTALL)

                    for class_name, tablename, _ in matches:
                        print(f"  Found model: {class_name} (table: {tablename})")

                        # Create a minimal model class representation
                        model_info = {
                            'name': class_name,
                            'tablename': tablename,
                            'module': module_name
                        }

                        # Store model under both original and lowercase names for matching
                        self.model_classes[class_name] = model_info
                        self.model_classes[class_name.lower()] = model_info

                except Exception as e:
                    print(f"  Error processing {filename}: {e}")

    def validate_entities(self):
        """Match entities from ER diagram with extracted model classes."""
        print("\nMatching entities with model classes...")

        for entity in self.entities:
            # Direct name matching
            if entity in self.model_classes:
                self.matched_entities[entity] = self.model_classes[entity]
                continue

            # Try lowercase matching
            if entity.lower() in self.model_classes:
                self.matched_entities[entity] = self.model_classes[entity.lower()]
                continue

            # Advanced name matching with variants
            matched = False
            for canonical, variants in self.name_matching_rules.items():
                if entity in variants or entity.lower() in [v.lower() for v in variants]:
                    # Check if any variant exists in model classes
                    for variant in variants:
                        if variant in self.model_classes:
                            self.matched_entities[entity] = self.model_classes[variant]
                            matched = True
                            break
                if matched:
                    break

            # If no match found, add to missing entities
            if not matched:
                self.missing_entities.append(entity)

    def print_validation_results(self):
        """Print the validation results in a readable format."""
        print("\n=== ER Diagram Validation Results ===\n")

        # Print matched entities
        print("Matched Entities:")
        if self.matched_entities:
            for entity, model in sorted(self.matched_entities.items()):
                print(f"  - {entity}: {model['module']}.{model['name']} (table: {model['tablename']})")
        else:
            print("  No entities matched!")

        # Print missing entities
        if self.missing_entities:
            print("\nMissing Entities:")
            for entity in sorted(self.missing_entities):
                print(f"  - {entity}")

                # Show similar names for suggestions
                similar_names = [
                    name for name in self.model_classes
                    if name.lower() not in ['name', 'tablename', 'module'] and  # Skip dict keys
                       (entity.lower() in name.lower() or name.lower() in entity.lower())
                ]

                if similar_names:
                    print("    Possible matches:")
                    for name in similar_names:
                        if isinstance(self.model_classes[name], dict):  # Check it's a model
                            print(f"    - {self.model_classes[name]['name']}")
        else:
            print("\nAll entities in the ER diagram have corresponding models!")

        # Print relationship validation
        print("\nRelationship Validation:")
        missing_rel_entities = set()

        for entity1, entity2 in self.relationships:
            entity1_exists = entity1 in self.matched_entities or entity1 in self.model_classes
            entity2_exists = entity2 in self.matched_entities or entity2 in self.model_classes

            if not entity1_exists or not entity2_exists:
                print(f"  - Incomplete Relationship: {entity1} -- {entity2}")
                if not entity1_exists:
                    print(f"    Missing Entity: {entity1}")
                    missing_rel_entities.add(entity1)
                if not entity2_exists:
                    print(f"    Missing Entity: {entity2}")
                    missing_rel_entities.add(entity2)

        if not missing_rel_entities:
            print("  All relationships connect existing entities!")

    def run_validation(self):
        """Run the full validation process."""
        try:
            print("Starting ER diagram validation...")

            # Parse ER diagram
            self.parse_er_diagram()

            # Extract model classes
            self.extract_models_from_files()

            # Validate entities
            self.validate_entities()

            # Print results
            self.print_validation_results()

            return len(self.missing_entities) == 0

        except Exception as e:
            print(f"Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    # Paths
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    er_diagram_path = os.path.join(current_script_dir, 'er_diagram.md')
    models_path = os.path.join(project_root, 'database', 'models')

    print(f"Project root: {project_root}")
    print(f"ER diagram path: {er_diagram_path}")
    print(f"Models path: {models_path}")

    # Create and run validator
    validator = MinimalERValidator(er_diagram_path, models_path)
    success = validator.run_validation()

    # Return success or failure status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()