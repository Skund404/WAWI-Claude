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
            if isinstance(data.get('hardware_type'), str):
                try:
                    data['hardware_type'] = HardwareType[data['hardware_type']]
                except KeyError:
                    raise ValueError(f"Invalid hardware type: {data['hardware_type']}")

            if isinstance(data.get('material'), str):
                try:
                    data['material'] = HardwareMaterial[data['material']]
                except KeyError:
                    raise ValueError(f"Invalid material: {data['material']}")

            if 'finish' in data and isinstance(data.get('finish'), str):
                try:
                    data['finish'] = HardwareFinish[data['finish']]
                except KeyError:
                    raise ValueError(f"Invalid finish: {data['finish']}")

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
                filter_conditions.append(Hardware.quantity >= min_stock)

            if max_stock is not None:
                filter_conditions.append(Hardware.quantity <= max_stock)

            if min_load_capacity is not None and hasattr(Hardware, 'load_capacity'):
                filter_conditions.append(Hardware.load_capacity >= min_load_capacity)

            if max_load_capacity is not None and hasattr(Hardware, 'load_capacity'):
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
            if 'hardware_type' in data and isinstance(data.get('hardware_type'), str):
                try:
                    data['hardware_type'] = HardwareType[data['hardware_type']]
                except KeyError:
                    raise ValueError(f"Invalid hardware type: {data['hardware_type']}")

            if 'material' in data and isinstance(data.get('material'), str):
                try:
                    data['material'] = HardwareMaterial[data['material']]
                except KeyError:
                    raise ValueError(f"Invalid material: {data['material']}")

            if 'finish' in data:
                if isinstance(data.get('finish'), str):
                    try:
                        data['finish'] = HardwareFinish[data['finish']]
                    except KeyError:
                        raise ValueError(f"Invalid finish: {data['finish']}")
                elif data['finish'] is None:
                    # Allow setting finish to None
                    pass

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

    def get_low_stock_hardware(self, threshold: int = 5) -> List[Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            threshold (int): Threshold for low stock

        Returns:
            List[Hardware]: Hardware items below threshold
        """
        try:
            query = select(Hardware).where(Hardware.quantity <= threshold)
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

    def filter_by_finish(self, finish: HardwareFinish) -> List[Hardware]:
        """
        Filter hardware items by finish type.

        Args:
            finish (HardwareFinish): The finish type to filter by

        Returns:
            List[Hardware]: Hardware items with the specified finish
        """
        try:
            query = select(Hardware).where(Hardware.finish == finish)
            results = self.session.execute(query).scalars().all()
            return list(results)
        except SQLAlchemyError as e:
            self.logger.error(f'Error filtering hardware by finish: {e}')
            raise

    @inject(IMaterialService)
    def get_compatible_materials(self, hardware_id: int, material_service: IMaterialService) -> List[Dict[str, Any]]:
        """
        Get materials compatible with the hardware item.

        Uses dependency injection to get the material service.

        Args:
            hardware_id: ID of the hardware item
            material_service: Injected material service

        Returns:
            List[Dict[str, Any]]: List of compatible materials
        """
        hardware = self.get_by_id(hardware_id)
        if not hardware:
            return []

        # Example implementation - adjust based on your business rules
        compatible_materials = []

        try:
            # Get materials compatible with this hardware type
            all_materials = material_service.get_all_materials()
            for material in all_materials:
                # Add your compatibility logic here
                compatible_materials.append(material.to_dict())
        except Exception as e:
            self.logger.error(f"Error getting compatible materials: {str(e)}")

        return compatible_materials