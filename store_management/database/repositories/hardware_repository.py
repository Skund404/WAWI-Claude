# database/repositories/hardware_repository.py
"""
Repository for hardware data access.
Provides database operations for hardware items.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from sqlalchemy import and_, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from database.models.hardware import Hardware
from database.models.enums import HardwareType, HardwareMaterial, HardwareFinish
from database.models.enums import InventoryStatus
from database.repositories.base_repository import BaseRepository
from services.interfaces.material_service import IMaterialService


class HardwareRepository(BaseRepository[Hardware]):
    """
    Repository for hardware data access operations.
    Extends BaseRepository with hardware-specific functionality.
    """

    def __init__(self, session: Session, material_service: Optional[IMaterialService] = None):
        """
        Initialize the HardwareRepository with a database session.

        Args:
            session: SQLAlchemy database session
            material_service (Optional[IMaterialService], optional): Material service for additional operations
        """
        super().__init__(session, Hardware)
        self.logger = logging.getLogger(__name__)
        self.material_service = material_service

    def get_all(self, include_inactive: bool = False, include_deleted: bool = False) -> List[Hardware]:
        """
        Get all hardware items with filtering options.

        Args:
            include_inactive (bool): Whether to include inactive hardware
            include_deleted (bool): Whether to include soft-deleted hardware

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            query = select(Hardware)

            # Apply filters
            filters = []
            if not include_inactive:
                filters.append(Hardware.is_active == True)
            if not include_deleted:
                filters.append(Hardware.is_deleted == False)

            if filters:
                query = query.where(and_(*filters))

            # Execute query
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving hardware items: {str(e)}")
            raise

    def get_by_id(self, hardware_id: str, include_deleted: bool = False) -> Optional[Hardware]:
        """
        Get a hardware item by its ID.

        Args:
            hardware_id (str): ID of the hardware to retrieve
            include_deleted (bool): Whether to include soft-deleted hardware

        Returns:
            Optional[Hardware]: Hardware item if found, None otherwise
        """
        try:
            query = select(Hardware).where(Hardware.id == hardware_id)

            if not include_deleted:
                query = query.where(Hardware.is_deleted == False)

            # Execute query
            result = self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving hardware with ID {hardware_id}: {str(e)}")
            raise

    def create(self, hardware: Hardware) -> Hardware:
        """
        Create a new hardware item.

        Args:
            hardware (Hardware): Hardware item to create

        Returns:
            Hardware: Created hardware item
        """
        try:
            self.session.add(hardware)
            self.session.commit()
            self.session.refresh(hardware)
            return hardware
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error creating hardware: {str(e)}")
            raise

    def update(self, hardware_id: str, hardware_data: Dict[str, Any]) -> Hardware:
        """
        Update an existing hardware item.

        Args:
            hardware_id (str): ID of the hardware to update
            hardware_data (Dict[str, Any]): Updated hardware data

        Returns:
            Hardware: Updated hardware item

        Raises:
            SQLAlchemyError: If update fails
        """
        try:
            # Get existing hardware
            hardware = self.get_by_id(hardware_id)
            if not hardware:
                raise ValueError(f"Hardware with ID {hardware_id} not found")

            # Update hardware attributes
            for key, value in hardware_data.items():
                if hasattr(hardware, key):
                    setattr(hardware, key, value)

            # Save changes
            self.session.commit()
            self.session.refresh(hardware)
            return hardware
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error updating hardware with ID {hardware_id}: {str(e)}")
            raise

    def delete(self, hardware_id: str) -> bool:
        """
        Permanently delete a hardware item.

        Args:
            hardware_id (str): ID of the hardware to delete

        Returns:
            bool: True if successful, False otherwise

        Raises:
            SQLAlchemyError: If deletion fails
        """
        try:
            # Get existing hardware
            hardware = self.get_by_id(hardware_id, include_deleted=True)
            if not hardware:
                return False

            # Delete hardware
            self.session.delete(hardware)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"Error deleting hardware with ID {hardware_id}: {str(e)}")
            raise

    def search(self, search_terms: Dict[str, Any]) -> List[Hardware]:
        """
        Search for hardware items based on multiple criteria.

        Args:
            search_terms (Dict[str, Any]): Search criteria

        Returns:
            List[Hardware]: List of matching hardware items
        """
        try:
            query = select(Hardware)
            filters = []

            # Process search terms
            for key, value in search_terms.items():
                if value is None:
                    continue

                # Handle different search fields
                if key == 'name' and value:
                    filters.append(Hardware.name.ilike(f"%{value}%"))
                elif key == 'description' and value:
                    filters.append(Hardware.description.ilike(f"%{value}%"))
                elif key == 'hardware_type' and value:
                    filters.append(Hardware.hardware_type == value)
                elif key == 'material' and value:
                    filters.append(Hardware.material == value)
                elif key == 'finish' and value:
                    filters.append(Hardware.finish == value)
                elif key == 'supplier_id' and value:
                    filters.append(Hardware.supplier_id == value)
                elif key == 'min_price' and value is not None:
                    filters.append(Hardware.price >= float(value))
                elif key == 'max_price' and value is not None:
                    filters.append(Hardware.price <= float(value))
                elif key == 'min_quantity' and value is not None:
                    filters.append(Hardware.quantity >= int(value))
                elif key == 'max_quantity' and value is not None:
                    filters.append(Hardware.quantity <= int(value))
                elif key == 'is_active' and value is not None:
                    filters.append(Hardware.is_active == bool(value))
                elif key == 'status' and value:
                    filters.append(Hardware.status == value)
                elif key == 'include_deleted' and not value:
                    filters.append(Hardware.is_deleted == False)

            # Apply filters
            if filters:
                query = query.where(and_(*filters))

            # Execute query
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error searching hardware: {str(e)}")
            raise

    def get_by_type(self, hardware_type: HardwareType) -> List[Hardware]:
        """
        Get hardware items of a specific type.

        Args:
            hardware_type (HardwareType): Type of hardware to retrieve

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.hardware_type == hardware_type,
                    Hardware.is_deleted == False
                )
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware by type {hardware_type.name}: {str(e)}")
            raise

    def get_by_material(self, material: HardwareMaterial) -> List[Hardware]:
        """
        Get hardware items made of a specific material.

        Args:
            material (HardwareMaterial): Material to filter by

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.material == material,
                    Hardware.is_deleted == False
                )
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware by material {material.name}: {str(e)}")
            raise

    def get_low_stock(self) -> List[Hardware]:
        """
        Get hardware items with quantity below reorder threshold.

        Returns:
            List[Hardware]: List of low stock hardware items
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.quantity <= Hardware.reorder_threshold,
                    Hardware.is_active == True,
                    Hardware.is_deleted == False
                )
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting low stock hardware: {str(e)}")
            raise

    def get_by_supplier(self, supplier_id: str) -> List[Hardware]:
        """
        Get hardware items from a specific supplier.

        Args:
            supplier_id (str): ID of the supplier

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.supplier_id == supplier_id,
                    Hardware.is_deleted == False
                )
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware by supplier ID {supplier_id}: {str(e)}")
            raise

    def get_by_status(self, status: InventoryStatus) -> List[Hardware]:
        """
        Get hardware items with a specific inventory status.

        Args:
            status (InventoryStatus): Inventory status to filter by

        Returns:
            List[Hardware]: List of hardware items
        """
        try:
            query = select(Hardware).where(
                and_(
                    Hardware.status == status,
                    Hardware.is_deleted == False
                )
            )
            result = self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware by status {status.name}: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about hardware inventory.

        Returns:
            Dict[str, Any]: Dictionary with hardware inventory statistics
        """
        try:
            stats = {
                'total_count': 0,
                'active_count': 0,
                'total_value': 0.0,
                'low_stock_count': 0,
                'out_of_stock_count': 0,
                'by_type': {},
                'by_material': {}
            }

            # Get total and active counts
            query_count = select(
                func.count(Hardware.id).label('total'),
                func.count(Hardware.id).filter(Hardware.is_active == True).label('active')
            ).where(Hardware.is_deleted == False)

            result_count = self.session.execute(query_count).first()
            if result_count:
                stats['total_count'] = result_count.total
                stats['active_count'] = result_count.active

            # Get total value
            query_value = select(
                func.sum(Hardware.price * Hardware.quantity).label('total_value')
            ).where(
                and_(
                    Hardware.is_deleted == False,
                    Hardware.is_active == True
                )
            )

            result_value = self.session.execute(query_value).first()
            if result_value and result_value.total_value:
                stats['total_value'] = float(result_value.total_value)

            # Get low stock and out of stock counts
            query_stock = select(
                func.count(Hardware.id).filter(
                    and_(
                        Hardware.quantity <= Hardware.reorder_threshold,
                        Hardware.quantity > 0
                    )
                ).label('low_stock'),
                func.count(Hardware.id).filter(Hardware.quantity == 0).label('out_of_stock')
            ).where(
                and_(
                    Hardware.is_deleted == False,
                    Hardware.is_active == True
                )
            )

            result_stock = self.session.execute(query_stock).first()
            if result_stock:
                stats['low_stock_count'] = result_stock.low_stock
                stats['out_of_stock_count'] = result_stock.out_of_stock

            # Get counts by type
            query_by_type = select(
                Hardware.hardware_type,
                func.count(Hardware.id).label('count')
            ).where(
                and_(
                    Hardware.is_deleted == False,
                    Hardware.is_active == True
                )
            ).group_by(Hardware.hardware_type)

            result_by_type = self.session.execute(query_by_type)
            for row in result_by_type:
                if row.hardware_type:
                    stats['by_type'][row.hardware_type.name] = row.count

            # Get counts by material
            query_by_material = select(
                Hardware.material,
                func.count(Hardware.id).label('count')
            ).where(
                and_(
                    Hardware.is_deleted == False,
                    Hardware.is_active == True
                )
            ).group_by(Hardware.material)

            result_by_material = self.session.execute(query_by_material)
            for row in result_by_material:
                if row.material:
                    stats['by_material'][row.material.name] = row.count

            return stats
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting hardware stats: {str(e)}")
            raise