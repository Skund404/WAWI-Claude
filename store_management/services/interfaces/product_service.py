# services/interfaces/product_service.py
from typing import Dict, List, Any, Optional, Protocol


class IProductService(Protocol):
    """Interface for the Product Service.

    The Product Service handles operations related to the product catalog,
    pricing, and inventory management of finished products.
    """

    def get_by_id(self, product_id: int) -> Dict[str, Any]:
        """Retrieve a product by its ID.

        Args:
            product_id: The ID of the product to retrieve

        Returns:
            A dictionary representation of the product

        Raises:
            NotFoundError: If the product with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all products with optional filtering.

        Args:
            filters: Optional filters to apply to the product query

        Returns:
            List of dictionaries representing products
        """
        ...

    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product.

        Args:
            product_data: Dictionary containing product data

        Returns:
            Dictionary representation of the created product

        Raises:
            ValidationError: If the product data is invalid
        """
        ...

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product.

        Args:
            product_id: ID of the product to update
            product_data: Dictionary containing updated product data

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, product_id: int) -> bool:
        """Delete a product by its ID.

        Args:
            product_id: ID of the product to delete

        Returns:
            True if the product was successfully deleted

        Raises:
            NotFoundError: If the product with the given ID does not exist
            ServiceError: If the product cannot be deleted (e.g., in use)
        """
        ...

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find products by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching products
        """
        ...

    def get_by_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Find products that use a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of dictionaries representing products using the pattern

        Raises:
            NotFoundError: If the pattern with the given ID does not exist
        """
        ...

    def link_pattern(self, product_id: int, pattern_id: int) -> Dict[str, Any]:
        """Link a pattern to a product.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product or pattern does not exist
            ValidationError: If the pattern is already linked to the product
        """
        ...

    def unlink_pattern(self, product_id: int, pattern_id: int) -> bool:
        """Unlink a pattern from a product.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern

        Returns:
            True if the pattern was successfully unlinked

        Raises:
            NotFoundError: If the product or the product-pattern link does not exist
        """
        ...

    def update_inventory(self, product_id: int, quantity: int, notes: str = None) -> Dict[str, Any]:
        """Update the inventory of a product.

        Args:
            product_id: ID of the product
            quantity: Quantity to adjust (positive or negative)
            notes: Optional notes about the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the product does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        ...

    def get_inventory_status(self, product_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the product does not exist
        """
        ...

    def calculate_production_cost(self, product_id: int) -> Dict[str, float]:
        """Calculate the production cost of a product based on its pattern and materials.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with cost breakdown (materials, labor, overhead, total)

        Raises:
            NotFoundError: If the product does not exist
            ServiceError: If the product is not linked to a pattern
        """
        ...

    def update_pricing(self, product_id: int, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the pricing information for a product.

        Args:
            product_id: ID of the product
            pricing_data: Dictionary containing pricing information

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product does not exist
            ValidationError: If the pricing data is invalid
        """
        ...

    def get_sales_history(self, product_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the sales history for a product.

        Args:
            product_id: ID of the product
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing sales information

        Raises:
            NotFoundError: If the product does not exist
        """
        ...