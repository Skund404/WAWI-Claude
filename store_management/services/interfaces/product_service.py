# database/services/interfaces/product_service.py
"""
Interface definition for Product Service.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any

from database.models.enums import MaterialType
from database.models.product import Product
from database.models.product_inventory import ProductInventory


class IProductService(ABC):
    """
    Interface defining contract for Product Service operations.
    """

    @abstractmethod
    def create_product(
        self,
        name: str,
        price: float,
        **kwargs
    ) -> Product:
        """
        Create a new product.

        Args:
            name: Product name
            price: Product price
            **kwargs: Additional product attributes

        Returns:
            Created Product instance
        """
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: str) -> Product:
        """
        Retrieve a product by its ID.

        Args:
            product_id: Unique identifier of the product

        Returns:
            Product instance
        """
        pass

    @abstractmethod
    def update_product(
        self,
        product_id: str,
        **update_data
    ) -> Product:
        """
        Update an existing product.

        Args:
            product_id: Unique identifier of the product
            update_data: Dictionary of fields to update

        Returns:
            Updated Product instance
        """
        pass

    @abstractmethod
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Unique identifier of the product

        Returns:
            Boolean indicating successful deletion
        """
        pass

    @abstractmethod
    def get_products_by_type(
        self,
        material_type: Optional[MaterialType] = None
    ) -> List[Product]:
        """
        Retrieve products filtered by material type.

        Args:
            material_type: Optional material type to filter products

        Returns:
            List of Product instances
        """
        pass

    @abstractmethod
    def add_product_inventory(
        self,
        product_id: str,
        quantity: int,
        storage_location: Optional[str] = None
    ) -> ProductInventory:
        """
        Add inventory for a specific product.

        Args:
            product_id: Unique identifier of the product
            quantity: Quantity to add to inventory
            storage_location: Optional storage location

        Returns:
            ProductInventory instance
        """
        pass