

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IHardwareService(ABC):
    """
    Interface for Hardware Service in the Leatherworking Management System.
    Defines the contract for hardware-related operations.
    """

    @abstractmethod
    @inject(MaterialService)
        def create_hardware(self, hardware_data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item.

        Args:
            hardware_data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: Created hardware instance
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def get_hardware(self, hardware_id: int) -> Optional[Hardware]:
        """
        Retrieve a hardware item by ID.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            Optional[Hardware]: Retrieved hardware
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def update_hardware(self, hardware_id: int, update_data: Dict[str, Any]
                        ) -> Optional[Hardware]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (int): Hardware identifier
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Hardware]: Updated hardware
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def delete_hardware(self, hardware_id: int) -> bool:
        """
        Delete a hardware item.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            bool: Success of deletion
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def get_low_stock_hardware(self, include_zero_stock: bool = False) -> List[
            Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            include_zero_stock (bool): Whether to include hardware with zero stock

        Returns:
            List[Hardware]: Hardware items below minimum stock level
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware
        """
        pass
