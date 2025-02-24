

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IProductService(ABC):
    """
    Abstract base class defining the interface for Product Service operations.

    Provides a comprehensive contract for product management,
    including creation, retrieval, updating, and deletion of products.
    """

    @abstractmethod
    @inject(MaterialService)
        def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product.

        Args:
            product_data (Dict[str, Any]): Data for creating a new product

        Returns:
            Dict[str, Any]: Created product details

        Raises:
            ValidationError: If product data is invalid
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific product by ID.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            Optional[Dict[str, Any]]: Product details

        Raises:
            ResourceNotFoundError: If product is not found
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def update_product(self, product_id: int, product_data: Dict[str, Any]
                       ) -> Dict[str, Any]:
        """
        Update an existing product.

        Args:
            product_id (int): Unique identifier for the product
            product_data (Dict[str, Any]): Updated product information

        Returns:
            Dict[str, Any]: Updated product details

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If product data is invalid
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def delete_product(self, product_id: int) -> bool:
        """
        Delete a product.

        Args:
            product_id (int): Unique identifier for the product

        Returns:
            bool: True if deletion was successful

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If product cannot be deleted
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def search_products(self, search_params: Dict[str, Any]) -> List[Dict[
            str, Any]]:
        """
        Search for products based on various criteria.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Dict[str, Any]]: List of matching products
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def update_product_stock(self, product_id: int, quantity_change: float,
                             transaction_type: str = 'ADJUSTMENT', notes: Optional[str] = None) -> Dict[
            str, Any]:
        """
        Update the stock of a product.

        Args:
            product_id (int): Unique identifier for the product
            quantity_change (float): Amount to change stock by
            transaction_type (str): Type of stock transaction
            notes (Optional[str]): Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated product details

        Raises:
            ResourceNotFoundError: If product is not found
            ValidationError: If stock update is invalid
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def generate_product_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive product report.

        Returns:
            Dict[str, Any]: Detailed product report containing:
            - Summary statistics
            - Low stock products
            - Other relevant product insights
        """
        pass
