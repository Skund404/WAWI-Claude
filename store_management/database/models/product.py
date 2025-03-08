# database/models/product.py
"""
Comprehensive Product Model for Leatherworking Management System

Implements the Product entity from the ER diagram with advanced
relationship management and validation strategies.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import sqltypes  # Using sqltypes for Enum

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    MaterialType,
    SkillLevel,
    ProjectType
)
from database.models.base import (
    TimestampMixin,
    ValidationMixin,
    CostingMixin,
    apply_mixins
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import (
    ModelValidator,
    ValidationError,
    validate_not_empty,
    validate_positive_number
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


# Use apply_mixins directly in the class definition
class Product(Base, apply_mixins(TimestampMixin, ValidationMixin, CostingMixin)):
    """
    Product model representing items that can be sold in the leatherworking system.

    Implements comprehensive tracking of product details,
    relationships, and business logic.
    """
    __tablename__ = 'products'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Core product attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing and financial attributes
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Tracking and identification
    sku: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        unique=True,
        default=lambda: f"PROD-{uuid.uuid4().hex[:8].upper()}"
    )
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)

    # Product characteristics - Using sqltypes.Enum explicitly to avoid conflicts
    material_type: Mapped[Optional[MaterialType]] = mapped_column(
        sqltypes.Enum(MaterialType),
        nullable=True
    )
    skill_level: Mapped[Optional[SkillLevel]] = mapped_column(
        sqltypes.Enum(SkillLevel),
        nullable=True
    )
    project_type: Mapped[Optional[ProjectType]] = mapped_column(
        sqltypes.Enum(ProjectType),
        nullable=True
    )

    # Visibility and status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Physical attributes
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata and additional information
    product_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Renamed from metadata

    # Foreign keys
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('suppliers.id'),
        nullable=True
    )
    storage_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('storages.id'),
        nullable=True
    )

    # Relationships with lazy loading and circular import resolution
    patterns: Mapped[List['ProductPattern']] = relationship(
        "ProductPattern",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    inventories: Mapped[List['ProductInventory']] = relationship(
        "ProductInventory",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    sales_items: Mapped[List['SalesItem']] = relationship(
        "SalesItem",
        back_populates="product"
    )

    components: Mapped[List['ProjectComponent']] = relationship(
        "ProjectComponent",
        back_populates="product",
        foreign_keys="[ProjectComponent.product_id]"
    )

    supplier: Mapped[Optional['Supplier']] = relationship(
        "Supplier",
        back_populates="products"
    )

    storage: Mapped[Optional['Storage']] = relationship(
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
            # Handle metadata rename if present
            if 'metadata' in kwargs:
                kwargs['product_metadata'] = kwargs.pop('metadata')

            # Also handle extra_metadata rename for backward compatibility
            if 'extra_metadata' in kwargs:
                kwargs['product_metadata'] = kwargs.pop('extra_metadata')

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

        # Initialize product_metadata if not provided
        if not hasattr(self, 'product_metadata') or self.product_metadata is None:
            self.product_metadata = {}

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
                    f"Invalid material type. Must be one of {[t.name for t in MaterialType]}",
                    "material_type"
                )

        if not isinstance(material_type, MaterialType):
            raise ValidationError("Invalid material type", "material_type")

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
                    f"Invalid skill level. Must be one of {[l.name for l in SkillLevel]}",
                    "skill_level"
                )

        if not isinstance(skill_level, SkillLevel):
            raise ValidationError("Invalid skill level", "skill_level")

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
                    f"Invalid project type. Must be one of {[t.name for t in ProjectType]}",
                    "project_type"
                )

        if not isinstance(project_type, ProjectType):
            raise ValidationError("Invalid project type", "project_type")

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
        # Lazy import to avoid circular dependencies
        ProductPattern = lazy_import('database.models.product_pattern', 'ProductPattern')

        # Create product pattern association if not exists
        product_pattern = ProductPattern(
            product_id=self.id,
            pattern_id=pattern.id
        )

        if product_pattern not in self.patterns:
            self.patterns.append(product_pattern)
            logger.info(f"Pattern {pattern.id} added to Product {self.id}")

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