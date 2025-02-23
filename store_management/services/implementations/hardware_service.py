# Path: services/implementations/hardware_service.py

from typing import List, Optional, Dict, Any
from services.interfaces.hardware_service import IHardwareService
from database.repositories.hardware_repository import HardwareRepository
from database.models.hardware import (
    Hardware,
    HardwareType,
    HardwareMaterial,
    HardwareFinish
)
from utils.error_handler import ApplicationError, ValidationError


class HardwareService(IHardwareService):
    """
    Service layer for managing hardware with business logic and validation.
    """

    def __init__(self, hardware_repository: HardwareRepository):
        """
        Initialize the hardware service with a repository.

        Args:
            hardware_repository (HardwareRepository): Hardware data access layer
        """
        self._repository = hardware_repository

    def create_hardware(self, hardware_data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item with comprehensive validation.

        Args:
            hardware_data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: Created hardware instance

        Raises:
            ValidationError: If hardware data is invalid
        """
        # Validate hardware data
        self._validate_hardware_data(hardware_data)

        try:
            # Check for duplicate hardware
            existing_hardware = self._check_duplicate_hardware(hardware_data)
            if existing_hardware:
                raise ValidationError(
                    "Hardware with similar details already exists",
                    {"existing_hardware_id": existing_hardware.id}
                )

            # Create hardware
            hardware = self._repository.create_hardware(hardware_data)

            # Post-creation processing
            self._post_hardware_creation_tasks(hardware)

            return hardware

        except Exception as e:
            # Log the error
            raise ApplicationError(f"Failed to create hardware: {str(e)}")

    def _validate_hardware_data(self, hardware_data: Dict[str, Any]):
        """
        Validate hardware creation data.

        Args:
            hardware_data (Dict[str, Any]): Hardware data to validate

        Raises:
            ValidationError: If data is invalid
        """
        # Validate required fields
        required_fields = ['name', 'hardware_type', 'material']
        for field in required_fields:
            if field not in hardware_data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate hardware type
        try:
            hardware_data['hardware_type'] = HardwareType[hardware_data['hardware_type']]
        except KeyError:
            raise ValidationError(f"Invalid hardware type: {hardware_data['hardware_type']}")

        # Validate material
        try:
            hardware_data['material'] = HardwareMaterial[hardware_data['material']]
        except KeyError:
            raise ValidationError(f"Invalid hardware material: {hardware_data['material']}")

        # Optional validations
        if 'finish' in hardware_data:
            try:
                hardware_data['finish'] = HardwareFinish[hardware_data['finish']]
            except KeyError:
                raise ValidationError(f"Invalid hardware finish: {hardware_data['finish']}")

        # Validate numerical fields
        if hardware_data.get('current_stock', 0) < 0:
            raise ValidationError("Current stock cannot be negative")

        if hardware_data.get('unit_cost', 0) < 0:
            raise ValidationError("Unit cost cannot be negative")

        if hardware_data.get('load_capacity', 0) < 0:
            raise ValidationError("Load capacity cannot be negative")

    def _check_duplicate_hardware(self, hardware_data: Dict[str, Any]) -> Optional[Hardware]:
        """
        Check for existing hardware with similar details.

        Args:
            hardware_data (Dict[str, Any]): Hardware data to check

        Returns:
            Optional[Hardware]: Existing hardware if found
        """
        similar_hardware = self._repository.search_hardware(
            hardware_type=hardware_data.get('hardware_type'),
            material=hardware_data.get('material'),
            finish=hardware_data.get('finish')
        )

        # Basic duplicate check
        for hardware in similar_hardware:
            if hardware.name == hardware_data.get('name'):
                return hardware

        return None

    def _post_hardware_creation_tasks(self, hardware: Hardware):
        """
        Perform additional tasks after hardware creation.

        Args:
            hardware (Hardware): Newly created hardware
        """
        # Example: Log hardware creation
        # You could add more post-creation logic here
        pass

    def get_hardware(self, hardware_id: int) -> Optional[Hardware]:
        """
        Retrieve a hardware item by ID.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            Optional[Hardware]: Retrieved hardware

        Raises:
            ApplicationError: If hardware retrieval fails
        """
        try:
            return self._repository.get_hardware_by_id(hardware_id)
        except Exception as e:
            raise ApplicationError(f"Failed to retrieve hardware: {str(e)}")

    def update_hardware(self, hardware_id: int, update_data: Dict[str, Any]) -> Optional[Hardware]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (int): Hardware identifier
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Hardware]: Updated hardware

        Raises:
            ValidationError: If update data is invalid
            ApplicationError: If update fails
        """
        # Validate update data
        self._validate_hardware_update(update_data)

        try:
            return self._repository.update_hardware(hardware_id, update_data)
        except Exception as e:
            raise ApplicationError(f"Failed to update hardware: {str(e)}")

    def _validate_hardware_update(self, update_data: Dict[str, Any]):
        """
        Validate hardware update data.

        Args:
            update_data (Dict[str, Any]): Data to validate

        Raises:
            ValidationError: If data is invalid
        """
        # Optional validations for each possible update field
        if 'hardware_type' in update_data:
            try:
                update_data['hardware_type'] = HardwareType[update_data['hardware_type']]
            except KeyError:
                raise ValidationError(f"Invalid hardware type: {update_data['hardware_type']}")

        if 'material' in update_data:
            try:
                update_data['material'] = HardwareMaterial[update_data['material']]
            except KeyError:
                raise ValidationError(f"Invalid hardware material: {update_data['material']}")

        if 'finish' in update_data:
            try:
                update_data['finish'] = HardwareFinish[update_data['finish']]
            except KeyError:
                raise ValidationError(f"Invalid hardware finish: {update_data['finish']}")

        # Additional specific validations
        if 'current_stock' in update_data and update_data['current_stock'] < 0:
            raise ValidationError("Current stock cannot be negative")

        if 'load_capacity' in update_data and update_data['load_capacity'] < 0:
            raise ValidationError("Load capacity cannot be negative")

    def delete_hardware(self, hardware_id: int) -> bool:
        """
        Delete a hardware item.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            bool: Success of deletion

        Raises:
            ApplicationError: If deletion fails
        """
        try:
            return self._repository.delete_hardware(hardware_id)
        except Exception as e:
            raise ApplicationError(f"Failed to delete hardware: {str(e)}")

    def get_low_stock_hardware(self, include_zero_stock: bool = False) -> List[Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            include_zero_stock (bool): Whether to include hardware with zero stock

        Returns:
            List[Hardware]: Hardware items below minimum stock level
        """
        return self._repository.get_low_stock_hardware(include_zero_stock)

    def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware

        Raises:
            ApplicationError: If report generation fails
        """
        try:
            return self._repository.generate_hardware_performance_report()
        except Exception as e:
            raise ApplicationError(f"Failed to generate hardware performance report: {str(e)}")

    def find_compatible_hardware(self, project_component, hardware_type: Optional[HardwareType] = None) -> List[
        Hardware]:
        """
        Find hardware compatible with a specific project component.

        Args:
            project_component (ProjectComponent): Project component to match
            hardware_type (Optional[HardwareType]): Optional specific hardware type to filter

        Returns:
            List[Hardware]: Compatible hardware items
        """
        # Search for hardware based on component and optional type
        compatible_hardware = []

        # Search all hardware, optionally filtered by type
        search_params = {}
        if hardware_type:
            search_params['hardware_type'] = hardware_type

        all_hardware = self._repository.search_hardware(**search_params)

        # Filter for compatibility
        for hardware in all_hardware:
            if hardware.compatibility_check(project_component):
                compatible_hardware.append(hardware)

        return compatible_hardware

    def analyze_hardware_usage(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze hardware usage across projects or for a specific project.

        Args:
            project_id (Optional[int]): Optional specific project to analyze

        Returns:
            Dict[str, Any]: Detailed hardware usage analysis
        """
        # Placeholder for complex hardware usage analysis
        hardware_usage = {
            'total_hardware_types': 0,
            'hardware_distribution': {},
            'most_used_hardware': [],
            'least_used_hardware': []
        }

        # In a real implementation, this would involve:
        # - Querying project components
        # - Tracking hardware usage across projects
        # - Generating detailed analytics

        return hardware_usage