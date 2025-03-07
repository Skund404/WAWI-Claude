# database/services/interfaces/product_pattern_service.py
"""
Interface definition for Product Pattern Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from database.models.product import Product
from database.models.pattern import Pattern
from database.models.product_pattern import ProductPattern


class IProductPatternService(ABC):
    """
    Interface defining contract for Product Pattern Service operations.
    """

    @abstractmethod
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
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_patterns_for_product(self, product_id: str) -> List[Pattern]:
        """
        Retrieve all patterns associated with a specific product.

        Args:
            product_id: Unique identifier of the product

        Returns:
            List of Pattern instances associated with the product
        """
        pass

    @abstractmethod
    def get_products_for_pattern(self, pattern_id: str) -> List[Product]:
        """
        Retrieve all products associated with a specific pattern.

        Args:
            pattern_id: Unique identifier of the pattern

        Returns:
            List of Product instances associated with the pattern
        """
        pass

    @abstractmethod
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
        """
        pass