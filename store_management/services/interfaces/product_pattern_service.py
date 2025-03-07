# services/interfaces/product_pattern_service.py
from abc import ABC, abstractmethod
from database.models.product import Product
from database.models.pattern import Pattern
from database.models.product_pattern import ProductPattern
from typing import List

class IProductPatternService(ABC):
    """
    Interface for Product Pattern Service defining core operations
    for managing relationships between products and patterns.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    def get_patterns_for_product(self, product_id: int) -> List[Pattern]:
        """
        Retrieve all patterns associated with a specific product.

        Args:
            product_id: ID of the product

        Returns:
            List of Pattern instances
        """
        pass

    @abstractmethod
    def get_products_for_pattern(self, pattern_id: int) -> List[Product]:
        """
        Retrieve all products associated with a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of Product instances
        """
        pass

    @abstractmethod
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
        pass