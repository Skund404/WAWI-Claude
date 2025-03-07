# database/services/implementations/product_pattern_service.py
"""
Service implementation for managing ProductPattern entities and their relationships.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
import logging

from database.models.product import Product
from database.models.pattern import Pattern
from database.models.product_pattern import ProductPattern
from database.repositories.product_repository import ProductRepository
from database.repositories.pattern_repository import PatternRepository
from database.repositories.product_pattern_repository import ProductPatternRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.product_pattern_service import IProductPatternService


class ProductPatternService(BaseService, IProductPatternService):
    """
    Service for managing ProductPattern-related operations.

    Handles creation, retrieval, and management of relationships
    between products and patterns.
    """

    def __init__(
        self,
        session=None,
        product_repository: Optional[ProductRepository] = None,
        pattern_repository: Optional[PatternRepository] = None,
        product_pattern_repository: Optional[ProductPatternRepository] = None
    ):
        """
        Initialize the Product Pattern Service.

        Args:
            session: SQLAlchemy database session
            product_repository: Repository for product data access
            pattern_repository: Repository for pattern data access
            product_pattern_repository: Repository for product pattern relationships
        """
        self.session = session or get_db_session()
        self.product_repository = product_repository or ProductRepository(self.session)
        self.pattern_repository = pattern_repository or PatternRepository(self.session)
        self.product_pattern_repository = (
                product_pattern_repository or
                ProductPatternRepository(self.session)
        )

        self.logger = logging.getLogger(__name__)

    def create_product_pattern(
        self,
        product_id: str,
        pattern_id: str,
        **kwargs
    ) -> ProductPattern:
        """
        Create a new product-pattern relationship.

        Args:
            product_id: Unique identifier of the product
            pattern_id: Unique identifier of the pattern
            **kwargs: Additional product pattern attributes

        Returns:
            Created ProductPattern instance

        Raises:
            NotFoundError: If product or pattern is not found
            ValidationError: If product-pattern creation fails
        """
        try:
            # Verify product exists
            product = self.product_repository.get(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Verify pattern exists
            pattern = self.pattern_repository.get(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Check if product-pattern relationship already exists
            existing_relationship = self.product_pattern_repository.get_by_product_and_pattern(
                product_id,
                pattern_id
            )
            if existing_relationship:
                raise ValidationError("Product-pattern relationship already exists")

            # Generate a unique identifier
            product_pattern_id = str(uuid.uuid4())

            # Create product pattern relationship
            product_pattern_data = {
                'id': product_pattern_id,
                'product_id': product_id,
                'pattern_id': pattern_id,
                **kwargs
            }

            product_pattern = ProductPattern(**product_pattern_data)

            # Save product pattern relationship
            with self.session:
                self.session.add(product_pattern)
                self.session.commit()
                self.session.refresh(product_pattern)

            self.logger.info(f"Created product pattern relationship: {product_pattern_id}")
            return product_pattern

        except Exception as e:
            self.logger.error(f"Error creating product pattern relationship: {str(e)}")
            raise ValidationError(f"Product pattern creation failed: {str(e)}")

    def get_product_patterns(
        self,
        product_id: Optional[str] = None,
        pattern_id: Optional[str] = None
    ) -> List[ProductPattern]:
        """
        Retrieve product-pattern relationships.

        Args:
            product_id: Optional product identifier to filter relationships
            pattern_id: Optional pattern identifier to filter relationships

        Returns:
            List of ProductPattern instances
        """
        try:
            # Retrieve product pattern relationships based on filters
            product_patterns = self.product_pattern_repository.get_by_product_or_pattern(
                product_id,
                pattern_id
            )
            return product_patterns

        except Exception as e:
            self.logger.error(f"Error retrieving product patterns: {str(e)}")
            return []

    def get_patterns_for_product(self, product_id: str) -> List[Pattern]:
        """
        Retrieve all patterns associated with a specific product.

        Args:
            product_id: Unique identifier of the product

        Returns:
            List of Pattern instances associated with the product

        Raises:
            NotFoundError: If product is not found
        """
        try:
            # Verify product exists
            product = self.product_repository.get(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Retrieve patterns for the product
            product_patterns = self.product_pattern_repository.get_by_product_or_pattern(
                product_id=product_id
            )

            # Extract patterns from relationships
            patterns = [
                self.pattern_repository.get(pp.pattern_id)
                for pp in product_patterns
                if pp.pattern_id
            ]

            return patterns

        except Exception as e:
            self.logger.error(f"Error retrieving patterns for product: {str(e)}")
            raise NotFoundError(f"Patterns retrieval failed: {str(e)}")

    def get_products_for_pattern(self, pattern_id: str) -> List[Product]:
        """
        Retrieve all products associated with a specific pattern.

        Args:
            pattern_id: Unique identifier of the pattern

        Returns:
            List of Product instances associated with the pattern

        Raises:
            NotFoundError: If pattern is not found
        """
        try:
            # Verify pattern exists
            pattern = self.pattern_repository.get(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Retrieve products for the pattern
            product_patterns = self.product_pattern_repository.get_by_product_or_pattern(
                pattern_id=pattern_id
            )

            # Extract products from relationships
            products = [
                self.product_repository.get(pp.product_id)
                for pp in product_patterns
                if pp.product_id
            ]

            return products

        except Exception as e:
            self.logger.error(f"Error retrieving products for pattern: {str(e)}")
            raise NotFoundError(f"Products retrieval failed: {str(e)}")

    def remove_product_pattern(
        self,
        product_id: str,
        pattern_id: str
    ) -> bool:
        """
        Remove a product-pattern relationship.

        Args:
            product_id: Unique identifier of the product
            pattern_id: Unique identifier of the pattern

        Returns:
            Boolean indicating successful removal

        Raises:
            NotFoundError: If product-pattern relationship is not found
            ValidationError: If relationship removal fails
        """
        try:
            # Find the specific product pattern relationship
            product_pattern = self.product_pattern_repository.get_by_product_and_pattern(
                product_id,
                pattern_id
            )

            if not product_pattern:
                raise NotFoundError(f"Product-pattern relationship not found")

            # Remove the relationship
            with self.session:
                self.session.delete(product_pattern)
                self.session.commit()

            self.logger.info(f"Removed product-pattern relationship for product {product_id} and pattern {pattern_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing product pattern relationship: {str(e)}")
            raise ValidationError(f"Product pattern relationship removal failed: {str(e)}")