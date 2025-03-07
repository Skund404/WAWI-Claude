# database/models/product.py
"""
Comprehensive Product Model for Leatherworking Management System

Implements the Product entity from the ER diagram with advanced
relationship management and validation strategies.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Type

from sqlalchemy import Column, Float, Integer, String, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    MaterialType,
    SkillLevel,
    ProjectType
)
from database.models.mixins import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('ProductPattern', 'database.models.product_pattern', 'ProductPattern')
register_lazy_import('ProductInventory', 'database.models.product_inventory', 'ProductInventory')
register_lazy_import('SalesItem', 'database.models.sales_item', 'SalesItem')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')
register_lazy_import('Storage', 'database.models.storage', 'Storage')


# Validation utility functions
class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


def validate_not_empty(data: Dict[str, Any], field_name: str, message: str = None):
    """
    Validate that a field is not empty.

    Args:
        data: Data dictionary to validate
        field_name: Field to check
        message: Optional custom error message

    Raises:
        ValidationError: If the field is empty
    """
    if field_name not in data or data[field_name] is None:
        raise ValidationError(message or f"{field_name} cannot be empty")


def validate_positive_number(data: Dict[str, Any], field_name: str, allow_zero: bool = False, message: str = None):
    """
    Validate that a field is a positive number.

    Args:
        data: Data dictionary to validate
        field_name: Field to check
        allow_zero: Whether zero is considered valid
        message: Optional custom error message

    Raises:
        ValidationError: If the field is not a positive number
    """
    if field_name not in data:
        return

    value = data[field_name]

    if value is None:
        return

    try:
        number_value = float(value)
        if allow_zero:
            if number_value < 0:
                raise ValidationError(message or f"{field_name} must be a non-negative number")
        else:
            if number_value <= 0:
                raise ValidationError(message or f"{field_name} must be a positive number")
    except (ValueError, TypeError):
        raise ValidationError(message or f"{field_name} must be a valid number")


class ModelValidator:
    """Utility class for model validation."""

    @staticmethod
    def validate_enum(value: Any, enum_class: Type, field_name: str) -> None:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field being validated

        Raises:
            ValidationError: If validation fails
        """
        try:
            if not isinstance(value, enum_class):
                # Try to convert string to enum
                if isinstance(value, str):
                    try:
                        enum_class[value.upper()]
                        return
                    except (KeyError, AttributeError):
                        pass
                raise ValidationError(f"{field_name} must be a valid {enum_class.__name__}")
        except Exception:
            raise ValidationError(f"Invalid {field_name} value")


class Product(Base, TimestampMixin, ValidationMixin, CostingMixin):
    """
    Product model representing items that can be sold in the leatherworking system.

    Implements comprehensive tracking of product details,
    relationships, and business logic.
    """
    __tablename__ = 'products'

    # Core product attributes
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Pricing and financial attributes
    price = Column(Float, nullable=False, default=0.0)

    # Tracking and identification
    sku = Column(
        String(50),
        nullable=True,
        unique=True,
        default=lambda: f"PROD-{uuid.uuid4().hex[:8].upper()}"
    )
    barcode = Column(String(50), nullable=True, unique=True)

    # Product characteristics
    material_type = Column(
        Enum(MaterialType),
        nullable=True
    )
    skill_level = Column(
        Enum(SkillLevel),
        nullable=True
    )
    project_type = Column(
        Enum(ProjectType),
        nullable=True
    )

    # Visibility and status
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)

    # Physical attributes
    weight = Column(Float, nullable=True)
    dimensions = Column(String(100), nullable=True)

    # Metadata and additional information
    extra_metadata = Column(JSON, nullable=True)

    # Foreign keys
    supplier_id = Column(
        Integer,
        ForeignKey('suppliers.id'),
        nullable=True
    )
    storage_id = Column(
        Integer,
        ForeignKey('storages.id'),
        nullable=True
    )

    # Relationships with lazy loading and circular import resolution
    patterns = relationship(
        "ProductPattern",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    inventories = relationship(
        "ProductInventory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    sales_items = relationship(
        "SalesItem",
        back_populates="product"
    )

    components = relationship(
        "ProjectComponent",
        back_populates="product",
        foreign_keys="ProjectComponent.product_id"
    )

    supplier = relationship(
        "Supplier",
        back_populates="products"
    )

    storage = relationship(
        "Storage",
        back_populates="product_items"
    )

    def __init__(self, **kwargs):
        """
        Initialize a Product instance with comprehensive validation.

        Args:
            **kwargs: Keyword arguments for product attributes

        Raises:
            ModelValidationError: If validation fails
        """
        try:
            # Validate and filter input data
            self._validate_product_data(kwargs)

            # Initialize base model
            super().__init__(**kwargs)

            # Post-initialization processing
            self._post_init_processing()

        except (ValidationError, SQLAlchemyError) as e:
            logger.error(f"Product initialization failed: {e}")
            raise ModelValidationError(f"Failed to create Product: {str(e)}") from e

    @classmethod
    def _validate_product_data(cls, data: Dict[str, Any]) -> None:
        """
        Comprehensive validation of product creation data.

        Args:
            data (Dict[str, Any]): Product creation data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        validate_not_empty(data, 'name', 'Product name is required')

        # Validate price
        if 'price' in data:
            validate_positive_number(
                data,
                'price',
                allow_zero=False,
                message="Price must be a positive number"
            )

        # Validate optional fields
        if 'material_type' in data and data['material_type']:
            cls._validate_material_type(data['material_type'])

        if 'skill_level' in data and data['skill_level']:
            cls._validate_skill_level(data['skill_level'])

        if 'project_type' in data and data['project_type']:
            cls._validate_project_type(data['project_type'])

        # Validate weight if provided
        if 'weight' in data and data['weight'] is not None:
            validate_positive_number(
                data,
                'weight',
                allow_zero=False,
                message="Weight must be a positive number"
            )

    def _post_init_processing(self) -> None:
        """
        Perform additional processing after instance creation.

        Applies business logic and performs final validations.
        """
        # Generate SKU if not provided
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"

        # Set default status
        if not hasattr(self, 'is_active'):
            self.is_active = True

    @classmethod
    def _validate_material_type(cls, material_type: Union[str, MaterialType]) -> MaterialType:
        """
        Validate material type.

        Args:
            material_type: Material type to validate

        Returns:
            Validated MaterialType

        Raises:
            ValidationError: If material type is invalid
        """
        if isinstance(material_type, str):
            try:
                return MaterialType[material_type.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid material type. Must be one of {[t.name for t in MaterialType]}"
                )

        if not isinstance(material_type, MaterialType):
            raise ValidationError("Invalid material type")

        return material_type

    @classmethod
    def _validate_skill_level(cls, skill_level: Union[str, SkillLevel]) -> SkillLevel:
        """
        Validate skill level.

        Args:
            skill_level: Skill level to validate

        Returns:
            Validated SkillLevel

        Raises:
            ValidationError: If skill level is invalid
        """
        if isinstance(skill_level, str):
            try:
                return SkillLevel[skill_level.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid skill level. Must be one of {[l.name for l in SkillLevel]}"
                )

        if not isinstance(skill_level, SkillLevel):
            raise ValidationError("Invalid skill level")

        return skill_level

    @classmethod
    def _validate_project_type(cls, project_type: Union[str, ProjectType]) -> ProjectType:
        """
        Validate project type.

        Args:
            project_type: Project type to validate

        Returns:
            Validated ProjectType

        Raises:
            ValidationError: If project type is invalid
        """
        if isinstance(project_type, str):
            try:
                return ProjectType[project_type.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid project type. Must be one of {[t.name for t in ProjectType]}"
                )

        if not isinstance(project_type, ProjectType):
            raise ValidationError("Invalid project type")

        return project_type

    def deactivate(self) -> None:
        """
        Deactivate the product.
        """
        self.is_active = False
        logger.info(f"Product {self.id} deactivated")

    def activate(self) -> None:
        """
        Activate the product.
        """
        self.is_active = True
        logger.info(f"Product {self.id} activated")

    def update_price(self, new_price: float) -> None:
        """
        Update the product price.

        Args:
            new_price: New product price

        Raises:
            ValidationError: If price is invalid
        """
        validate_positive_number(
            {'price': new_price},
            'price',
            allow_zero=False,
            message="Price must be a positive number"
        )

        self.price = new_price
        logger.info(f"Product {self.id} price updated to {new_price}")

    def add_pattern(self, pattern) -> None:
        """
        Add a pattern to the product.

        Args:
            pattern: Pattern to add
        """
        try:
            # Lazy import to avoid circular dependencies
            ProductPattern = lazy_import('ProductPattern')

            # Create product pattern association if it doesn't exist
            product_pattern = ProductPattern(
                product_id=self.id,
                pattern_id=pattern.id
            )

            if not hasattr(self, 'patterns'):
                self.patterns = []

            # Check if pattern already exists
            pattern_exists = False
            for existing_pattern in self.patterns:
                if (existing_pattern.product_id == product_pattern.product_id and
                        existing_pattern.pattern_id == product_pattern.pattern_id):
                    pattern_exists = True
                    break

            if not pattern_exists:
                self.patterns.append(product_pattern)
                logger.info(f"Pattern {pattern.id} added to Product {self.id}")

        except Exception as e:
            logger.error(f"Error adding pattern: {e}")
            raise ModelValidationError(f"Failed to add pattern: {str(e)}")

    def __repr__(self) -> str:
        """
        String representation of the product.

        Returns:
            str: Detailed product representation
        """
        return (
            f"<Product("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"price={self.price}, "
            f"active={self.is_active}, "
            f"sku='{self.sku}'"
            f")>"
        )


def initialize_relationships():
    """
    Initialize relationships to resolve potential circular imports.
    """
    logger.debug("Initializing Product relationships")
    try:
        # Import necessary models
        from database.models.product_pattern import ProductPattern
        from database.models.product_inventory import ProductInventory
        from database.models.sales_item import SalesItem
        from database.models.supplier import Supplier
        from database.models.storage import Storage

        # Ensure relationships are properly configured
        logger.info("Product relationships initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up Product relationships: {e}")
        logger.error(str(e))


# Register for lazy import resolution
register_lazy_import('Product', 'database.models.product', 'Product')