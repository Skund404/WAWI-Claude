# relative path: store_management/database/repositories/hardware_repository.py
"""
Repository for managing hardware with advanced querying capabilities.

Provides comprehensive methods for hardware item management,
including creation, retrieval, updating, and reporting.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
import logging

from di.core import inject
from services.interfaces.material_service import IMaterialService
from database.models.hardware import Hardware, HardwareType, HardwareMaterial, HardwareFinish
from database.repositories.base_repository import BaseRepository


class HardwareRepository(BaseRepository[Hardware]):
    """
    Repository for managing hardware items with advanced querying capabilities.

    Provides methods to interact with hardware, including
    CRUD operations, filtering, and performance reporting.
    """

    @inject('IMaterialService')
    def __init__(self, session, material_service: Optional[IMaterialService] = None):
        """
        Initialize the HardwareRepository with a database session.

        Args:
            session: SQLAlchemy database session
            material_service (Optional[IMaterialService], optional): Material service for additional operations
        """
        super().__init__(session, Hardware)
        self.logger = logging.getLogger(self.__class__.__module__)
        self._material_service = material_service

    def create(self, data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item with comprehensive validation.

        Args:
            data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: Created hardware instance

        Raises:
            ValueError: If hardware data validation fails
        """
        try:
            # Convert enum string values if provided
            if 'hardware_type' in data:
                data['hardware_type'] = HardwareType[data['hardware_type']]

            if 'material' in data:
                data['material'] = HardwareMaterial[data['material']]

            if 'finish' in data:
                data['finish'] = HardwareFinish[data['finish']]

            # Create hardware instance
            hardware = Hardware(**data)

            # Add to session and commit
            self.session.add(hardware)
            self.session.commit()

            self.logger.info(f'Created hardware item: {hardware.name}')
            return hardware
        except (ValueError, KeyError) as e:
            self.logger.error(f'Error creating hardware: Invalid enum value - {e}')
            raise ValueError(f'Invalid enum value: {e}')
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f'Database error creating hardware: {e}')
            raise

    def get_by_id(self, id_value: int) -> Optional[Hardware]:
        """
        Retrieve a hardware item by its ID.

        Args:
            id_value (int): Hardware identifier

        Returns:
            Optional[Hardware]: Retrieved hardware or None
        """
        try:
            query = select(Hardware).where(Hardware.id == id_value)
            result = self.session.execute(query).scalar_one_or_none()
            return result
        except SQLAlchemyError as e:
            self.logger.error(f'Error retrieving hardware with ID {id_value}: {e}')
            raise

    def search(
            self,
            hardware_type: Optional[HardwareType] = None,
            material: Optional[HardwareMaterial] = None,
            finish: Optional[HardwareFinish] = None,
            min_stock: Optional[int] = None,
            max_stock: Optional[int] = None,
            min_load_capacity: Optional[float] = None,
            max_load_capacity: Optional[float] = None
    ) -> List[Hardware]:
        """
        Advanced search for hardware with multiple filtering options.

        Args:
            hardware_type (Optional[HardwareType]): Filter by hardware type
            material (Optional[HardwareMaterial]): Filter by material
            finish (Optional[HardwareFinish]): Filter by finish
            min_stock (Optional[int]): Minimum current stock
            max_stock (Optional[int]): Maximum current stock
            min_load_capacity (Optional[float]): Minimum load capacity
            max_load_capacity (Optional[float]): Maximum load capacity

        Returns:
            List[Hardware]: Matching hardware items
        """
        try:
            # Start with base query
            query = select(Hardware)

            # Prepare filter conditions
            filter_conditions = []

            if hardware_type:
                filter_conditions.append(Hardware.hardware_type == hardware_type)

            if material:
                filter_conditions.append(Hardware.material == material)

            if finish:
                filter_conditions.append(Hardware.finish == finish)

            if min_stock is not None:
                filter_conditions.append(Hardware.current_stock >= min_stock)

            if max_stock is not None:
                filter_conditions.append(Hardware.current_stock <= max_stock)

            if min_load_capacity is not None:
                filter_conditions.append(Hardware.load_capacity >= min_load_capacity)

            if max_load_capacity is not None:
                filter_conditions.append(Hardware.load_capacity <= max_load_capacity)

            # Apply filters if any
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

            # Execute query
            results = self.session.execute(query).scalars().all()
            return list(results)
        except SQLAlchemyError as e:
            self.logger.error(f'Error searching hardware: {e}')
            raise

    def update(self, id_value: int, data: Dict[str, Any]) -> Optional[Hardware]:
        """
        Update an existing hardware item.

        Args:
            id_value (int): Hardware identifier
            data (Dict[str, Any]): Data to update

        Returns:
            Optional[Hardware]: Updated hardware or None
        """
        try:
            # Retrieve existing hardware
            hardware = self.get_by_id(id_value)

            if not hardware:
                self.logger.warning(f'Hardware with ID {id_value} not found')
                return None

            # Convert enum string values if provided
            if 'hardware_type' in data:
                data['hardware_type'] = HardwareType[data['hardware_type']]

            if 'material' in data:
                data['material'] = HardwareMaterial[data['material']]

            if 'finish' in data:
                data['finish'] = HardwareFinish[data['finish']]

            # Update hardware attributes
            for key, value in data.items():
                setattr(hardware, key, value)

            # Commit changes
            self.session.commit()

            self.logger.info(f'Updated hardware item: {hardware.name}')
            return hardware
        except (ValueError, KeyError) as e:
            self.logger.error(f'Error updating hardware: Invalid enum value - {e}')
            raise ValueError(f'Invalid enum value: {e}')
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f'Database error updating hardware: {e}')
            raise

    def delete(self, id_value: int) -> bool:
        """
        Delete a hardware item.

        Args:
            id_value (int): Hardware identifier

        Returns:
            bool: Success of deletion
        """
        try:
            # Retrieve hardware
            hardware = self.get_by_id(id_value)

            if not hardware:
                self.logger.warning(f'Hardware with ID {id_value} not found')
                return False

            # Delete hardware
            self.session.delete(hardware)
            self.session.commit()

            self.logger.info(f'Deleted hardware item with ID {id_value}')
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f'Error deleting hardware: {e}')
            raise

    def get_low_stock_hardware(self, include_zero_stock: bool = False) -> List[Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            include_zero_stock (bool): Whether to include hardware with zero stock

        Returns:
            List[Hardware]: Hardware items below minimum stock level
        """
        try:
            query = select(Hardware)

            if not include_zero_stock:
                query = query.where(Hardware.current_stock > 0)

            query = query.where(Hardware.current_stock <= Hardware.minimum_stock_level)

            results = self.session.execute(query).scalars().all()
            return list(results)
        except SQLAlchemyError as e:
            self.logger.error(f'Error retrieving low stock hardware: {e}')
            raise

    def get_hardware_by_supplier(self, supplier_id: int) -> List[Hardware]:
        """
        Retrieve hardware items from a specific supplier.

        Args:
            supplier_id (int): Supplier identifier

        Returns:
            List[Hardware]: Hardware items from the specified supplier
        """
        try:
            query = select(Hardware).where(Hardware.supplier_id == supplier_id)
            results = self.session.execute(query).scalars().all()
            return list(results)
        except SQLAlchemyError as e:
            self.logger.error(f'Error retrieving hardware for supplier {supplier_id}: {e}')
            raise

    def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware
        """
        try:
            query = select(Hardware)
            hardware_items = self.session.execute(query).scalars().all()

            hardware_report = []
            for hardware in hardware_items:
                # Assuming calculate_hardware_performance is a method on the Hardware model
                performance_score = (
                    hardware.calculate_hardware_performance()
                    if hasattr(hardware, 'calculate_hardware_performance')
                    else 0
                )

                hardware_report.append({
                    'hardware_id': hardware.id,
                    'name': hardware.name,
                    'hardware_type': hardware.hardware_type.name,
                    'performance_score': performance_score,
                    'current_stock': hardware.current_stock,
                    'load_capacity': hardware.load_capacity,
                    'corrosion_resistance': hardware.corrosion_resistance
                })

            # Sort by performance score in descending order
            return sorted(hardware_report, key=lambda x: x['performance_score'], reverse=True)
        except SQLAlchemyError as e:
            self.logger.error(f'Error generating hardware performance report: {e}')
            raise