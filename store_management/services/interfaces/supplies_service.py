# services/interfaces/supplies_service.py
from typing import Dict, List, Any, Optional, Protocol


class ISuppliesService(Protocol):
    """Interface for the Supplies Service.

    The Supplies Service handles operations related to consumable supplies used in
    leatherworking, such as thread, adhesives, dyes, finishes, and edge paint.
    """

    def get_by_id(self, supply_id: int) -> Dict[str, Any]:
        """Retrieve a supply item by its ID.

        Args:
            supply_id: The ID of the supply to retrieve

        Returns:
            A dictionary representation of the supply

        Raises:
            NotFoundError: If the supply with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all supplies with optional filtering.

        Args:
            filters: Optional filters to apply to the supply query

        Returns:
            List of dictionaries representing supplies
        """
        ...

    def create(self, supply_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supply item.

        Args:
            supply_data: Dictionary containing supply data

        Returns:
            Dictionary representation of the created supply

        Raises:
            ValidationError: If the supply data is invalid
        """
        ...

    def update(self, supply_id: int, supply_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supply item.

        Args:
            supply_id: ID of the supply to update
            supply_data: Dictionary containing updated supply data

        Returns:
            Dictionary representation of the updated supply

        Raises:
            NotFoundError: If the supply with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, supply_id: int) -> bool:
        """Delete a supply item by its ID.

        Args:
            supply_id: ID of the supply to delete

        Returns:
            True if the supply was successfully deleted

        Raises:
            NotFoundError: If the supply with the given ID does not exist
            ServiceError: If the supply cannot be deleted (e.g., in use)
        """
        ...

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find supplies by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching supplies
        """
        ...

    def find_by_type(self, supply_type: str) -> List[Dict[str, Any]]:
        """Find supplies by type.

        Args:
            supply_type: Supply type to filter by

        Returns:
            List of dictionaries representing supplies of the specified type
        """
        ...

    def find_by_color(self, color: str) -> List[Dict[str, Any]]:
        """Find supplies by color.

        Args:
            color: Color to filter by

        Returns:
            List of dictionaries representing supplies of the specified color
        """
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Find supplies provided by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of dictionaries representing supplies from the supplier

        Raises:
            NotFoundError: If the supplier does not exist
        """
        ...

    def get_inventory_status(self, supply_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a supply item.

        Args:
            supply_id: ID of the supply

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the supply does not exist
        """
        ...

    def adjust_inventory(self, supply_id: int,
                         quantity: float,
                         reason: str) -> Dict[str, Any]:
        """Adjust the inventory of a supply item.

        Args:
            supply_id: ID of the supply
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the supply does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        ...

    def get_components_using(self, supply_id: int) -> List[Dict[str, Any]]:
        """Get components that use a specific supply item.

        Args:
            supply_id: ID of the supply

        Returns:
            List of dictionaries representing components that use the supply

        Raises:
            NotFoundError: If the supply does not exist
        """
        ...

    def get_usage_history(self, supply_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the usage history for a supply item.

        Args:
            supply_id: ID of the supply
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing usage records

        Raises:
            NotFoundError: If the supply does not exist
        """
        ...

    def calculate_usage_rate(self, supply_id: int,
                             period_days: int = 30) -> Dict[str, Any]:
        """Calculate the usage rate of a supply item.

        Args:
            supply_id: ID of the supply
            period_days: Number of days to analyze

        Returns:
            Dictionary containing usage rate information

        Raises:
            NotFoundError: If the supply does not exist
        """
        ...

    def get_low_stock_supplies(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get supplies that are low in stock.

        Args:
            threshold: Optional threshold percentage (0-100)

        Returns:
            List of dictionaries representing low stock supplies
        """
        ...

    def get_reorder_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for supplies that should be reordered.

        Returns:
            List of dictionaries representing supplies that should be reordered
        """
        ...

    def track_batch(self, supply_id: int,
                    batch_number: str,
                    batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a specific batch of a supply item.

        Args:
            supply_id: ID of the supply
            batch_number: Batch number
            batch_data: Dictionary containing batch information

        Returns:
            Dictionary representing the tracked batch

        Raises:
            NotFoundError: If the supply does not exist
            ValidationError: If the batch data is invalid
        """
        ...

    def get_batch_info(self, supply_id: int, batch_number: str) -> Dict[str, Any]:
        """Get information about a specific batch of a supply item.

        Args:
            supply_id: ID of the supply
            batch_number: Batch number

        Returns:
            Dictionary containing batch information

        Raises:
            NotFoundError: If the supply or batch does not exist
        """
        ...