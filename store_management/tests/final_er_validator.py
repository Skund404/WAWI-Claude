# store_management/tests/final_er_validator.py
"""
A simplified ER diagram validator that focuses on matching entity names
to model classes, ignoring field definitions and relationship syntax.
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class SimpleERValidator:
    def __init__(self, er_diagram_path: str, models_path: str):
        """
        Initialize the simplified ER Diagram Validator.

        Args:
            er_diagram_path (str): Path to the ER diagram file
            models_path (str): Path to the models directory
        """
        self.er_diagram_path = os.path.abspath(er_diagram_path)
        self.models_path = os.path.abspath(models_path)
        self.entity_names = set()  # Just the entity names, no fields
        self.model_classes = {}
        self.matched_entities = {}
        self.missing_entities = []
        self.categories = {}

    def extract_entity_names(self):
        """Extract just the entity names from the ER diagram, ignoring field definitions."""
        try:
            with open(self.er_diagram_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # First, identify category headers
                category_pattern = r'##\s*(.*?)\s*\n'
                categories = re.findall(category_pattern, content)
                self.categories = {cat.strip(): [] for cat in categories if cat.strip()}

                # Find all entity definitions - looking for entity names followed by opening brace
                entity_pattern = r'([A-Za-z]+)\s*{'
                entity_matches = re.findall(entity_pattern, content)

                # Clean up and store unique entity names
                for entity in entity_matches:
                    entity_name = entity.strip()
                    if entity_name and not entity_name.startswith('#'):
                        self.entity_names.add(entity_name)

                # Associate entities with categories
                lines = content.split('\n')
                current_category = None

                for line in lines:
                    line = line.strip()

                    # Check if this is a category header
                    if line.startswith('##'):
                        category_name = line.replace('#', '').strip()
                        if category_name in self.categories:
                            current_category = category_name

                    # Check if this is an entity definition
                    elif current_category and '{' in line:
                        entity_name = line.split('{')[0].strip()
                        if entity_name in self.entity_names:
                            self.categories[current_category].append(entity_name)

                print(f"Found {len(self.entity_names)} entity names in ER diagram:")
                for entity in sorted(self.entity_names):
                    print(f"  - {entity}")

                print("\nEntities by category:")
                for category, entities in self.categories.items():
                    if entities:
                        print(f"  {category}: {', '.join(entities)}")

        except Exception as e:
            print(f"Error parsing ER diagram: {e}")
            import traceback
            traceback.print_exc()
            raise

    def extract_models_from_files(self):
        """Extract model classes directly from Python files using regex."""
        if not os.path.exists(self.models_path):
            print(f"Models directory not found: {self.models_path}")
            return

        print(f"\nLooking for models in: {self.models_path}")

        # Patterns to extract model classes
        class_pattern = r'class\s+([A-Za-z0-9_]+).*?__tablename__\s*=\s*[\'\"]([A-Za-z0-9_]+)[\'\"](.*?)(?=class|\Z)'

        for filename in os.listdir(self.models_path):
            if filename.endswith('.py') and filename != '__init__.py':
                file_path = os.path.join(self.models_path, filename)
                module_name = filename[:-3]

                try:
                    # Read file as text
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find all class definitions with __tablename__
                    matches = re.findall(class_pattern, content, re.DOTALL)

                    if matches:
                        print(f"  Found in {filename}:")

                    for class_name, tablename, _ in matches:
                        print(f"    - {class_name} (table: {tablename})")

                        # Create a minimal model class representation
                        model_info = {
                            'name': class_name,
                            'tablename': tablename,
                            'module': module_name,
                            'file': filename
                        }

                        # Store model under both original and lowercase names for matching
                        self.model_classes[class_name] = model_info
                        self.model_classes[class_name.lower()] = model_info

                except Exception as e:
                    print(f"  Error processing {filename}: {e}")

    def match_entities_to_models(self):
        """Match entity names to model classes with multiple strategies."""
        print("\nMatching entity names to model classes...")

        for entity in self.entity_names:
            # Direct name matching (exact match)
            if entity in self.model_classes:
                self.matched_entities[entity] = self.model_classes[entity]
                print(f"  Direct match: {entity} -> {self.model_classes[entity]['name']}")
                continue

            # Case-insensitive matching
            if entity.lower() in self.model_classes:
                self.matched_entities[entity] = self.model_classes[entity.lower()]
                print(f"  Case-insensitive match: {entity} -> {self.model_classes[entity.lower()]['name']}")
                continue

            # Find similar matches as suggestions
            similar_models = []
            for model_name, model_info in self.model_classes.items():
                if isinstance(model_info, dict) and (
                        entity.lower() in model_name.lower() or
                        model_name.lower() in entity.lower()
                ):
                    similar_models.append(model_info)

            # If we have similar models, log them
            if similar_models:
                print(f"  Entity '{entity}' has no exact match but similar models found:")
                seen = set()
                for model in similar_models:
                    if model['name'] not in seen:
                        seen.add(model['name'])
                        print(f"    - {model['name']} in {model['file']}")

            # No match found
            print(f"  No direct match for entity: {entity}")
            self.missing_entities.append(entity)

    def print_validation_results(self):
        """Print the validation results in a readable format."""
        print("\n=== ER Diagram Validation Results ===")

        # Print summary stats
        print(f"\nFound {len(self.entity_names)} entities in ER diagram")
        print(
            f"Found {len(self.model_classes) // 2} model classes in Python files")  # Divide by 2 for lowercase duplicates
        print(f"Successfully matched {len(self.matched_entities)} entities to models")
        print(f"Missing models for {len(self.missing_entities)} entities\n")

        # Print entities by category with their matches
        print("Entities by Category:")

        for category, entities in sorted(self.categories.items()):
            print(f"\n  {category}:")

            matched_in_category = []
            missing_in_category = []

            for entity in entities:
                if entity in self.matched_entities:
                    model = self.matched_entities[entity]
                    matched_in_category.append(f"{entity} → {model['name']} ({model['file']})")
                else:
                    similar_models = []
                    for model_name, model_info in self.model_classes.items():
                        if isinstance(model_info, dict) and (
                                entity.lower() in model_name.lower() or
                                model_name.lower() in entity.lower()
                        ):
                            model_file = model_info.get('file', 'unknown')
                            similar = f"{model_info['name']} ({model_file})"
                            if similar not in similar_models:
                                similar_models.append(similar)

                    if similar_models:
                        suggestion = f"{entity} → possible matches: {', '.join(similar_models)}"
                    else:
                        suggestion = entity

                    missing_in_category.append(suggestion)

            # Print matched entities in this category
            if matched_in_category:
                print("    Matched:")
                for match in matched_in_category:
                    print(f"    ✓ {match}")

            # Print missing entities in this category
            if missing_in_category:
                print("    Missing:" if matched_in_category else "    All Missing:")
                for missing in missing_in_category:
                    print(f"    ✗ {missing}")

    def run_validation(self):
        """Run the simplified validation process focusing on entity names."""
        try:
            print("Starting simplified ER diagram validation...")

            # Extract just the entity names
            self.extract_entity_names()

            # Extract model classes
            self.extract_models_from_files()

            # Match entity names to models
            self.match_entities_to_models()

            # Print results
            self.print_validation_results()

            # Return success if all entities matched
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
    validator = SimpleERValidator(er_diagram_path, models_path)
    success = validator.run_validation()

    # Return success or failure status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()