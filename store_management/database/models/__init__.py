# Path: store_management/database/models/__init__.py
"""
Central model registration and circular import resolution.
"""

from sqlalchemy.orm import DeclarativeBase
from typing import Dict, Type, Any, List


class ModelRegistry:
    """
    Centralized registry for managing model imports and dependencies.
    """
    _models: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str, model_class: Type[Any]) -> None:
        """
        Register a model class.

        Args:
            name (str): Unique identifier for the model.
            model_class (Type[Any]): The model class to register.
        """
        cls._models[name] = model_class

    @classmethod
    def get(cls, name: str) -> Type[Any]:
        """
        Retrieve a registered model class.

        Args:
            name (str): Unique identifier for the model.

        Returns:
            Type[Any]: The requested model class.

        Raises:
            KeyError: If the model is not registered.
        """
        if name not in cls._models:
            raise KeyError(f"Model '{name}' is not registered")
        return cls._models[name]

    @classmethod
    def get_all_models(cls) -> List[Type[Any]]:
        """
        Retrieve all registered models.

        Returns:
            List[Type[Any]]: List of all registered model classes.
        """
        return list(cls._models.values())


class Base(DeclarativeBase):
    """
    Base declarative class for SQLAlchemy models.
    """
    pass


def _safe_import(module_name: str, class_name: str) -> Any:
    """
    Safely import a class, handling potential import errors.

    Args:
        module_name (str): Name of the module to import from.
        class_name (str): Name of the class to import.

    Returns:
        Any: Imported class or None if import fails.
    """
    try:
        module = __import__(f'database.models.{module_name}', fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Error importing {class_name} from {module_name}: {e}")
        return None


def _register_models():
    """
    Register models with the ModelRegistry to prevent circular imports.
    """
    # Define a list of models to import
    models_to_register = [
        ('Supplier', 'supplier_resolver'),
        ('Product', 'product_resolver'),
        ('OrderItem', 'order_item_resolver'),
        ('Order', 'order_resolver'),
        ('Storage', 'storage_resolver'),
        # Add other models as needed
    ]

    # Attempt to register models
    for class_name, module_name in models_to_register:
        model_class = _safe_import(module_name, class_name)
        if model_class:
            ModelRegistry.register(class_name, model_class)

    # Additional setup for resolvers to break circular dependencies
    try:
        from .supplier_resolver import SupplierModelResolver
        from .product_resolver import ProductModelResolver
        from .order_resolver import OrderModelResolver
        from .order_item_resolver import OrderItemModelResolver
        from .storage_resolver import StorageModelResolver

        # Cross-register models for resolvers
        supplier_model = ModelRegistry.get('Supplier')
        product_model = ModelRegistry.get('Product')
        order_model = ModelRegistry.get('Order')
        order_item_model = ModelRegistry.get('OrderItem')
        storage_model = ModelRegistry.get('Storage')

        # Set models in resolvers
        SupplierModelResolver.set_product_model(product_model)
        SupplierModelResolver.set_order_model(order_model)

        ProductModelResolver.set_supplier_model(supplier_model)
        ProductModelResolver.set_order_item_model(order_item_model)
        ProductModelResolver.set_storage_model(storage_model)

        OrderModelResolver.set_supplier_model(supplier_model)
        OrderModelResolver.set_order_item_model(order_item_model)

        OrderItemModelResolver.set_product_model(product_model)
        OrderItemModelResolver.set_order_model(order_model)

        StorageModelResolver.set_product_model(product_model)

    except Exception as e:
        print(f"Error setting up model resolvers: {e}")


# Import enums to ensure they are available
from .enums import (
    ProjectType, SkillLevel, ProjectStatus,
    ProductionStatus, MaterialType, TransactionType,
    OrderStatus, PaymentStatus, ShoppingListStatus,
    StitchType, EdgeFinishType
)

# Run model registration
_register_models()

# Export all relevant classes and enums
__all__ = [
    'Base', 'ModelRegistry',
    # Enums
    'ProjectType', 'SkillLevel', 'ProjectStatus',
    'ProductionStatus', 'MaterialType', 'TransactionType',
    'OrderStatus', 'PaymentStatus', 'ShoppingListStatus',
    'StitchType', 'EdgeFinishType'
]