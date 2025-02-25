# database/__init__.py
from utils.circular_import_resolver import CircularImportResolver

# Use a try/except block to handle circular imports
try:
    # Import models
    from .models.components import Component, PatternComponent, ProjectComponent
    from .models.material import Material
    from .models.order import Order
    from .models.pattern import Pattern
    from .models.product import Product
    from .models.project import Project
    from .models.storage import Storage
    from .models.supplier import Supplier
except ImportError as e:
    CircularImportResolver.register_pending_import(__name__, e)

def register_models():
    """
    Function to register all models in the application.
    This helps with resolving any circular import issues.
    """
    try:
        # This function can be called after the entire application is loaded
        # to ensure all models are properly registered and available
        pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error registering models: {str(e)}")