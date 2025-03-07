# services/implementations/product_pattern_service.py
from database.models.product import Product
from database.models.pattern import Pattern
from database.models.product_pattern import ProductPattern
from database.repositories.product_pattern_repository import ProductPatternRepository
from database.sqlalchemy.session import get_db_session
from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.product_pattern_service import IProductPatternService
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Dict, List, Optional
import logging


class ProductPatternService(BaseService, IProductPatternService):
    def __init__(
            self,
            session: Optional[Session] = None,
            product_pattern_repository: Optional[ProductPatternRepository] = None
    ):
        """
        Initialize the Product Pattern Service.

        Args:
            session: SQLAlchemy database session
            product_pattern_repository: Repository for product pattern data access
        """
        self.session = session or get_db_session()
        self.product_pattern_repository = product_pattern_repository or ProductPatternRepository(self.session)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_product_pattern(
            self,
            product_id: int,
            pattern_id: int
    ) -> ProductPattern:
        """
        Create a link between a product and a pattern.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern

        Returns:
            Created ProductPattern instance
        """
        try:
            product_pattern = ProductPattern(
                product_id=product_id,
                pattern_id=pattern_id
            )

            self.session.add(product_pattern)
            self.session.commit()

            self.logger.info(
                f"Created product pattern link for product {product_id} and pattern {pattern_id}"
            )
            return product_pattern

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating product pattern link: {str(e)}")
            raise ValidationError(f"Failed to create product pattern link: {str(e)}")

    def get_patterns_for_product(self, product_id: int) -> List[Pattern]:
        """
        Retrieve all patterns associated with a specific product.

        Args:
            product_id: ID of the product

        Returns:
            List of Pattern instances
        """
        try:
            product_patterns = self.product_pattern_repository.get_patterns_by_product(product_id)

            if not product_patterns:
                self.logger.warning(f"No patterns found for product {product_id}")
                return []

            return [pp.pattern for pp in product_patterns]

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving patterns for product: {str(e)}")
            raise NotFoundError(f"Failed to retrieve patterns: {str(e)}")

    def get_products_for_pattern(self, pattern_id: int) -> List[Product]:
        """
        Retrieve all products associated with a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of Product instances
        """
        try:
            product_patterns = self.product_pattern_repository.get_products_by_pattern(pattern_id)

            if not product_patterns:
                self.logger.warning(f"No products found for pattern {pattern_id}")
                return []

            return [pp.product for pp in product_patterns]

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving products for pattern: {str(e)}")
            raise NotFoundError(f"Failed to retrieve products: {str(e)}")

    def remove_product_pattern_link(
            self,
            product_id: int,
            pattern_id: int
    ) -> None:
        """
        Remove the link between a product and a pattern.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern
        """
        try:
            product_pattern = self.product_pattern_repository.get_by_product_and_pattern(
                product_id, pattern_id
            )

            if not product_pattern:
                raise NotFoundError(
                    f"No link found between product {product_id} and pattern {pattern_id}"
                )

            self.session.delete(product_pattern)
            self.session.commit()

            self.logger.info(
                f"Removed product pattern link for product {product_id} and pattern {pattern_id}"
            )

        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error removing product pattern link: {str(e)}")
            raise ValidationError(f"Failed to remove product pattern link: {str(e)}")