# services/interfaces/product_service.py
from abc import ABC, abstractmethod
from database.models.product import Product
from database.models.enums import MaterialType
from typing import List, Dict, Any, Optional


class IProductService(ABC):
    """
    Abstract base class defining the interface for Product services.

    Defines the contract for creating, retrieving, updating,
    and deleting Product entities.
    """

    @abstractmethod
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Create a new product.

        Args:
            product_data (Dict[str, Any]): Product creation data

        Returns:
            Product: Newly created product instance

        Raises:
            ValidationError: If product data is invalid
        """
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Product:
        """
        Retrieve a product by its ID.

        Args:
            product_id (int): Unique identifier of the product

        Returns:
            Product: Retrieved product instance

        Raises:
            NotFoundError: If no product is found with the given ID
        """
        pass

    @abstractmethod
    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Product:
        """
        Update an existing product.

        Args:
            product_id (int): ID of the product to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Product: Updated product instance

        Raises:
            NotFoundError: If product doesn't exist
            ValidationError: If update data is invalid
        """
        pass

    @abstractmethod
    def delete_product(self, product_id: int) -> None:
        """
        Soft delete a product.

        Args:
            product_id (int): ID of the product to delete

        Raises:
            NotFoundError: If product doesn't exist
        """
        pass

    @abstractmethod
    def list_products(self,
                      active_only: bool = True,
                      material_type: Optional[MaterialType] = None) -> List[Product]:
        """
        List products with optional filtering.

        Args:
            active_only (bool): Filter for only active products
            material_type (Optional[MaterialType]): Filter by material type

        Returns:
            List[Product]: List of products matching the criteria
        """
        pass