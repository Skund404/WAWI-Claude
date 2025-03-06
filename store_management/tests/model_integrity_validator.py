# tests/model_integrity_validator_patched.py
"""
Patched version of the model integrity validator that ensures SQLAlchemy
types are available during the import process.
"""

import sys
import os
import importlib
import inspect
import types
from typing import List, Dict, Any, Type
import warnings


# Create dummy SQLAlchemy types and inject them into sys.modules
class DummySQLType:
    def __init__(self, *args, **kwargs):
        pass


# Create a fake sqlalchemy module with common types
sqlalchemy_module = types.ModuleType('sqlalchemy')
sqlalchemy_module.Integer = DummySQLType
sqlalchemy_module.String = DummySQLType
sqlalchemy_module.Boolean = DummySQLType
sqlalchemy_module.Float = DummySQLType
sqlalchemy_module.DateTime = DummySQLType
sqlalchemy_module.ForeignKey = DummySQLType
sqlalchemy_module.MetaData = DummySQLType
sqlalchemy_module.Column = DummySQLType
sqlalchemy_module.Text = DummySQLType
sqlalchemy_module.Enum = DummySQLType
sqlalchemy_module.exc = types.ModuleType('sqlalchemy.exc')
sqlalchemy_module.exc.SQLAlchemyError = Exception

# Create a fake sqlalchemy.orm module
orm_module = types.ModuleType('sqlalchemy.orm')
orm_module.DeclarativeBase = type('DeclarativeBase', (), {})
orm_module.Mapped = type('Mapped', (), {})
orm_module.Mapper = type('Mapper', (), {})
orm_module.Session = type('Session', (), {})


def mapped_column(*args, **kwargs):
    return DummySQLType()


def relationship(*args, **kwargs):
    return DummySQLType()


orm_module.mapped_column = mapped_column
orm_module.relationship = relationship
orm_module.declared_attr = lambda x: x
orm_module.joinedload = lambda x: x

# Register these modules in sys.modules
sys.modules['sqlalchemy'] = sqlalchemy_module
sys.modules['sqlalchemy.orm'] = orm_module
sys.modules['sqlalchemy.exc'] = sqlalchemy_module.exc


# Patch the circular import resolver's lazy_import function
def patch_circular_import_resolver():
    try:
        from utils.circular_import_resolver import lazy_import as original_lazy_import

        def patched_lazy_import(module_path, class_name=None):
            if module_path == 'sqlalchemy':
                if class_name == 'Integer': return sqlalchemy_module.Integer
                if class_name == 'String': return sqlalchemy_module.String
                if class_name == 'Boolean': return sqlalchemy_module.Boolean
                if class_name == 'Float': return sqlalchemy_module.Float
                if class_name == 'DateTime': return sqlalchemy_module.DateTime
                if class_name == 'ForeignKey': return sqlalchemy_module.ForeignKey
                if class_name == 'MetaData': return sqlalchemy_module.MetaData
                if class_name == 'Column': return sqlalchemy_module.Column
                if class_name == 'Text': return sqlalchemy_module.Text
                if class_name == 'Enum': return sqlalchemy_module.Enum
                if class_name is None: return sqlalchemy_module

            if module_path == 'sqlalchemy.orm':
                if class_name == 'DeclarativeBase': return orm_module.DeclarativeBase
                if class_name == 'Mapped': return orm_module.Mapped
                if class_name == 'Mapper': return orm_module.Mapper
                if class_name == 'mapped_column': return orm_module.mapped_column
                if class_name == 'relationship': return orm_module.relationship
                if class_name == 'declared_attr': return orm_module.declared_attr
                if class_name is None: return orm_module

            return original_lazy_import(module_path, class_name)

        # Replace the original lazy_import with our patched version
        import utils.circular_import_resolver
        utils.circular_import_resolver.lazy_import = patched_lazy_import
        print("Successfully patched circular_import_resolver.lazy_import!")
    except Exception as e:
        print(f"Warning: Failed to patch circular_import_resolver: {e}")


# Attempt to patch the circular import resolver
patch_circular_import_resolver()


class ModelIntegrityValidator:
    def __init__(self, models_path: str, repositories_path: str):
        """
        Initialize the validator with paths to models and repositories.

        Args:
            models_path (str): Path to the models directory
            repositories_path (str): Path to the repositories directory
        """
        # Convert to absolute paths
        self.models_path = os.path.abspath(models_path)
        self.repositories_path = os.path.abspath(repositories_path)

        # Add project root to Python path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(self.models_path)))
        sys.path.insert(0, project_root)
        sys.path.insert(0, os.path.join(project_root, 'store_management'))

        # Suppress SQLAlchemy warnings
        warnings.filterwarnings('ignore', category=Warning)

        self.validation_results = {
            'missing_repositories': [],
            'mismatched_models': [],
            'import_issues': [],
            'relationship_issues': [],
            'model_details': []
        }

    def load_modules(self, directory: str) -> Dict[str, Any]:
        """
        Load all Python modules from a given directory.

        Args:
            directory (str): Path to the directory to load modules from

        Returns:
            Dict of module names to module objects
        """
        # Verify directory exists
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            return {}

        modules = {}
        # Determine the correct package base
        package_parts = directory.split(os.path.sep)
        package_index = package_parts.index('store_management') if 'store_management' in package_parts else -1

        if package_index == -1:
            print(f"Could not determine package base for {directory}")
            return {}

        # Construct package base
        package_base = '.'.join(package_parts[package_index:])

        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.py') and not filename.startswith('__'):
                    # Construct module path
                    rel_path = os.path.relpath(root, directory)
                    module_name = filename[:-3]

                    # Create full import path
                    if rel_path == '.':
                        import_path = f"{package_base}.{module_name}"
                    else:
                        import_path = f"{package_base}.{rel_path.replace(os.path.sep, '.')}.{module_name}"

                    try:
                        # Use importlib to import the module
                        module = importlib.import_module(import_path)
                        modules[module_name] = module
                        print(f"Successfully imported: {import_path}")
                    except ImportError as e:
                        print(f"Failed to import {import_path}: {e}")
                        self.validation_results['import_issues'].append(f"Failed to import {import_path}: {e}")
                    except Exception as e:
                        print(f"Unexpected error importing {import_path}: {e}")

        return modules

    def validate_model_repository_coverage(self):
        """
        Check if each model has a corresponding repository.
        """
        # Dynamically load models and repositories
        models = self.load_modules(self.models_path)
        repositories = self.load_modules(self.repositories_path)

        # Ignore base or utility modules
        ignored_modules = {'base', 'enums', 'mixins', '__init__', 'types', 'config',
                           'circular_import_resolver', 'interfaces', 'factories',
                           'model_metaclass', 'init_relationships', 'init',
                           'base_transaction', 'order_resolver', 'pattern_resolver',
                           'product_resolver', 'storage_resolver', 'supplier_resolver',
                           'models', 'metrics', 'picking_list', 'transaction'}

        # Collect model and mixin details
        for model_name, model_module in models.items():
            # Skip ignored modules
            if model_name in ignored_modules:
                continue

            # Look for model classes
            try:
                model_classes = [
                    (name, obj) for name, obj in inspect.getmembers(model_module, inspect.isclass)
                    if obj.__module__ == model_module.__name__ and
                       hasattr(obj, '__bases__') and
                       any('Base' in base.__name__ for base in obj.__bases__)
                ]

                for model_class_name, model_class in model_classes:
                    # Collect model details
                    model_info = {
                        'name': model_class_name,
                        'module': model_module.__name__,
                        'mixins': [],
                        'repository': None
                    }

                    # Identify mixins
                    mixins = [
                        base.__name__ for base in model_class.__bases__
                        if hasattr(base, '__name__') and 'Mixin' in base.__name__
                    ]
                    model_info['mixins'] = mixins

                    print(f"Registering model: {model_module.__name__}")
                    print(f"Mixins applied to {model_class_name}: {', '.join(mixins)}")

                    # Multiple repository naming conventions
                    repo_candidates = [
                        f"{model_class_name.lower().replace('s', '')}_repository",
                        f"{model_class_name.lower()}s_repository",
                        f"{model_class_name.lower()}_repository"
                    ]

                    # Check if any candidate repository exists
                    found_repo = False
                    for repo_name in repo_candidates:
                        if repo_name in repositories:
                            model_info['repository'] = repo_name
                            found_repo = True
                            break

                    if not found_repo:
                        self.validation_results['missing_repositories'].append(
                            f"No repository found for model: {model_class_name}"
                        )

                    # Store model details
                    self.validation_results['model_details'].append(model_info)

            except Exception as e:
                print(f"Error processing model {model_name}: {e}")

    def validate_import_relationships(self):
        """
        Check for circular or problematic imports.
        """
        models = self.load_modules(self.models_path)

        for module_name, module in models.items():
            try:
                # Check for circular import indicators
                imports = [
                    name for name, obj in inspect.getmembers(module)
                    if inspect.ismodule(obj) and obj.__name__.startswith(module.__name__.split('.')[0])
                ]

                # Optional: More sophisticated circular import detection
                for imp in imports:
                    if imp.__name__ == module.__name__:
                        self.validation_results['import_issues'].append(
                            f"Potential circular import in {module_name}"
                        )
            except Exception as e:
                self.validation_results['import_issues'].append(
                    f"Error analyzing imports for {module_name}: {e}"
                )

    def validate_model_relationships(self):
        """
        Validate relationships defined in models.
        """
        models = self.load_modules(self.models_path)

        for model_name, module in models.items():
            try:
                # Look for model classes
                model_classes = [
                    obj for name, obj in inspect.getmembers(module, inspect.isclass)
                    if obj.__module__ == module.__name__ and
                       hasattr(obj, '__bases__') and
                       any('Base' in base.__name__ for base in obj.__bases__)
                ]

                for model_class in model_classes:
                    # Check for relationships
                    try:
                        relationships = [
                            attr for attr in dir(model_class)
                            if 'relationship' in str(type(getattr(model_class, attr, None)))
                        ]

                        # Optional: More detailed relationship validation
                        if not relationships:
                            self.validation_results['relationship_issues'].append(
                                f"No relationships found for {model_class.__name__}"
                            )
                    except Exception as e:
                        print(f"Error checking relationships for {model_class.__name__}: {e}")
            except Exception as e:
                self.validation_results['relationship_issues'].append(
                    f"Error validating relationships for {model_name}: {e}"
                )

    def run_validation(self):
        """
        Run all validation checks.

        Returns:
            Dict of validation results
        """
        print("Running Model Repository Coverage Validation...")
        self.validate_model_repository_coverage()

        print("Running Import Relationship Validation...")
        self.validate_import_relationships()

        print("Running Model Relationship Validation...")
        self.validate_model_relationships()

        return self.validation_results


def main():
    # Use current script's location to determine project structure
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_script_dir))

    # Construct paths
    models_path = os.path.join(project_root, 'store_management', 'database', 'models')
    repositories_path = os.path.join(project_root, 'store_management', 'database', 'repositories')

    print(f"Project Root: {project_root}")
    print(f"Models Path: {models_path}")
    print(f"Repositories Path: {repositories_path}")

    # Ensure the correct Python path
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'store_management'))

    # Try to import the package to ensure it's recognized
    try:
        import store_management
    except ImportError as e:
        print(f"Could not import store_management package: {e}")
        print("Ensure you have an __init__.py in the store_management directory")
        return

    validator = ModelIntegrityValidator(models_path, repositories_path)
    results = validator.run_validation()

    # Print detailed results
    print("\nModel Integrity Validation Results:")

    # Detailed Model Details
    print("\nModel Details:")
    for model in results.get('model_details', []):
        print(f"Model: {model['name']}")
        print(f"  Module: {model['module']}")
        print(f"  Mixins: {', '.join(model['mixins'])}")
        print(f"  Repository: {model['repository'] or 'Not Found'}")
        print()

    # Missing Repositories
    print("\nMissing Repositories:")
    for issue in results.get('missing_repositories', []):
        print(f"  - {issue}")

    # Import Issues
    print("\nImport Issues:")
    for issue in results.get('import_issues', []):
        print(f"  - {issue}")

    # Relationship Issues
    print("\nRelationship Issues:")
    for issue in results.get('relationship_issues', []):
        print(f"  - {issue}")


if __name__ == '__main__':
    main()