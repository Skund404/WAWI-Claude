# database/repositories/product_pattern_repository.py
"""
Repository for managing ProductPattern entities.

This repository handles database operations for the many-to-many relationship
between products and patterns.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.product_pattern import ProductPattern
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)


class ProductPatternRepository(BaseRepository[ProductPattern]):
    """Repository for managing ProductPattern entities."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the ProductPattern Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ProductPattern)
        logger.debug("ProductPatternRepository initialized")

    def get_all_by_product_id(self, product_id: int) -> List[ProductPattern]:
        """
        Get all pattern associations for a specific product.

        Args:
            product_id (int): The product ID to query

        Returns:
            List[ProductPattern]: List of product-pattern associations
        """
        try:
            query = self.session.query(ProductPattern).filter(
                ProductPattern.product_id == product_id
            )
            result = query.all()
            logger.debug(f"Retrieved {len(result)} patterns for product ID {product_id}")
            return result
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving patterns for product ID {product_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_all_by_pattern_id(self, pattern_id: int) -> List[ProductPattern]:
        """
        Get all product associations for a specific pattern.

        Args:
            pattern_id (int): The pattern ID to query

        Returns:
            List[ProductPattern]: List of product-pattern associations
        """
        try:
            query = self.session.query(ProductPattern).filter(
                ProductPattern.pattern_id == pattern_id
            )
            result = query.all()
            logger.debug(f"Retrieved {len(result)} products for pattern ID {pattern_id}")
            return result
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving products for pattern ID {pattern_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def create_association(self, product_id: int, pattern_id: int) -> ProductPattern:
        """
        Create a new association between a product and a pattern.

        Args:
            product_id (int): The product ID
            pattern_id (int): The pattern ID

        Returns:
            ProductPattern: The created association

        Raises:
            DatabaseError: If there's an error creating the association
        """
        try:
            # Check if association already exists
            existing = self.session.query(ProductPattern).filter(
                and_(
                    ProductPattern.product_id == product_id,
                    ProductPattern.pattern_id == pattern_id
                )
            ).first()

            if existing:
                logger.debug(f"Association already exists for product ID {product_id} and pattern ID {pattern_id}")
                return existing

            # Create new association
            association = ProductPattern(product_id=product_id, pattern_id=pattern_id)
            self.session.add(association)
            self.session.commit()
            logger.debug(f"Created association for product ID {product_id} and pattern ID {pattern_id}")
            return association
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Error creating association between product ID {product_id} and pattern ID {pattern_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def delete_association(self, product_id: int, pattern_id: int) -> bool:
        """
        Delete an association between a product and a pattern.

        Args:
            product_id (int): The product ID
            pattern_id (int): The pattern ID

        Returns:
            bool: True if the association was deleted, False otherwise

        Raises:
            DatabaseError: If there's an error deleting the association
        """
        try:
            result = self.session.query(ProductPattern).filter(
                and_(
                    ProductPattern.product_id == product_id,
                    ProductPattern.pattern_id == pattern_id
                )
            ).delete()

            self.session.commit()
            deleted = result > 0

            if deleted:
                logger.debug(f"Deleted association for product ID {product_id} and pattern ID {pattern_id}")
            else:
                logger.debug(f"No association found for product ID {product_id} and pattern ID {pattern_id}")

            return deleted
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Error deleting association between product ID {product_id} and pattern ID {pattern_id}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)