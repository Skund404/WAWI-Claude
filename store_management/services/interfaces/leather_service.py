# services/interfaces/leather_service.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from database.models.enums import InventoryStatus, LeatherType, MaterialQualityGrade, TransactionType


class ILeatherService(ABC):
    """
    Interface for leather management operations.

    This service provides business logic for leather inventory operations,
    managing the creation, querying, updating, and inventory management of
    leather materials.
    """

    @abstractmethod
    def get_all_leathers(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         leather_type: Optional[LeatherType] = None,
                         grade: Optional[MaterialQualityGrade] = None,
                         color: Optional[str] = None,
                         thickness_min: Optional[float] = None,
                         thickness_max: Optional[float] = None,
                         min_size: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get all leathers with optional filtering.

        Args:
            include_deleted (bool): Whether to include soft-deleted leathers
            status (Optional[InventoryStatus]): Filter by status
            leather_type (Optional[LeatherType]): Filter by leather type
            grade (Optional[MaterialQualityGrade]): Filter by quality grade
            color (Optional[str]): Filter by color
            thickness_min (Optional[float]): Filter by minimum thickness
            thickness_max (Optional[float]): Filter by maximum thickness
            min_size (Optional[float]): Filter by minimum size in square feet

        Returns:
            List[Dict[str, Any]]: List of leather dictionaries
        """
        pass

    @abstractmethod
    def get_leather_by_id(self, leather_id: int) -> Dict[str, Any]:
        """
        Get a leather by its ID.

        Args:
            leather_id (int): ID of the leather to retrieve

        Returns:
            Dict[str, Any]: Leather as a dictionary
        """
        pass

    @abstractmethod
    def create_leather(self, leather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new leather item.

        Args:
            leather_data (Dict[str, Any]): Data for the new leather

        Returns:
            Dict[str, Any]: Created leather as a dictionary
        """
        pass

    @abstractmethod
    def update_leather(self, leather_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing leather.

        Args:
            leather_id (int): ID of the leather to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Dict[str, Any]: Updated leather as a dictionary
        """
        pass

    @abstractmethod
    def delete_leather(self, leather_id: int, permanent: bool = False) -> bool:
        """
        Delete a leather (soft delete by default).

        Args:
            leather_id (int): ID of the leather to delete
            permanent (bool): Whether to permanently delete

        Returns:
            bool: True if successful
        """
        pass

    @abstractmethod
    def restore_leather(self, leather_id: int) -> Dict[str, Any]:
        """
        Restore a soft-deleted leather.

        Args:
            leather_id (int): ID of the leather to restore

        Returns:
            Dict[str, Any]: Restored leather as a dictionary
        """
        pass

    @abstractmethod
    def search_leathers(self, search_term: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Search for leathers by various fields.

        Args:
            search_term (str): Search term to look for
            include_deleted (bool): Whether to include soft-deleted leathers

        Returns:
            List[Dict[str, Any]]: List of matching leather dictionaries
        """
        pass

    @abstractmethod
    def adjust_leather_quantity(self, leather_id: int, quantity_change: int,
                                transaction_type: Union[TransactionType, str],
                                notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Adjust the quantity of a leather and create a transaction record.

        Args:
            leather_id (int): ID of the leather
            quantity_change (int): Amount to change quantity by (positive or negative)
            transaction_type (Union[TransactionType, str]): Type of transaction
            notes (Optional[str]): Additional notes for the transaction

        Returns:
            Dict[str, Any]: Updated leather as a dictionary
        """
        pass

    @abstractmethod
    def get_transaction_history(self, leather_id: int,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transaction history for a specific leather.

        Args:
            leather_id (int): ID of the leather
            limit (Optional[int]): Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of transactions as dictionaries
        """
        pass

    @abstractmethod
    def get_low_stock_leathers(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Get all leathers with quantity below a specified threshold.

        Args:
            threshold (int): Quantity threshold

        Returns:
            List[Dict[str, Any]]: List of low stock leathers as dictionaries
        """
        pass

    @abstractmethod
    def get_out_of_stock_leathers(self) -> List[Dict[str, Any]]:
        """
        Get all leathers that are out of stock.

        Returns:
            List[Dict[str, Any]]: List of out of stock leathers as dictionaries
        """
        pass

    @abstractmethod
    def get_leather_inventory_value(self) -> Dict[str, Any]:
        """
        Calculate the total inventory value of all leather items.

        Returns:
            Dict[str, Any]: Dictionary with total value and breakdowns
        """
        pass

    @abstractmethod
    def batch_update_leathers(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple leather records in a batch.

        Args:
            updates (List[Dict[str, Any]]): List of dictionaries with 'id' and fields to update

        Returns:
            List[Dict[str, Any]]: List of updated leathers as dictionaries
        """
        pass