# F:\WAWI Homebrew\WAWI Claude\store_management\database\__init__.py

from utils.circular_import_resolver import CircularImportResolver

def register_models():
    """
    Centralized model registration to avoid circular imports.
    """
    try:
        # Importing models dynamically to avoid circular imports
        from .models.pattern import Pattern
        from .models.project import Project
        from .models.components import Component, ProjectComponent, PatternComponent
        from .models.material import Material
        from .models.supplier import Supplier
        from .models.order import Order
        from .models.product import Product
        from .models.storage import Storage

        # Register models with the circular import resolver
        CircularImportResolver.register_class('Pattern', Pattern)
        CircularImportResolver.register_class('Project', Project)
        CircularImportResolver.register_class('Component', Component)
        CircularImportResolver.register_class('ProjectComponent', ProjectComponent)
        CircularImportResolver.register_class('PatternComponent', PatternComponent)
        CircularImportResolver.register_class('Material', Material)
        CircularImportResolver.register_class('Supplier', Supplier)
        CircularImportResolver.register_class('Order', Order)
        CircularImportResolver.register_class('Product', Product)
        CircularImportResolver.register_class('Storage', Storage)

    except ImportError as e:
        print(f"Error registering models: {e}")

# Register models when the module is imported
register_models()