# Path: database/repositories/hardware_repository.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.hardware import (
    Hardware,
    HardwareType,
    HardwareMaterial,
    HardwareFinish
)


class HardwareRepository:
    """
    Repository for managing hardware with advanced querying capabilities.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_hardware(self, hardware_data: Dict[str, Any]) -> Hardware:
        """
        Create a new hardware item with comprehensive validation.

        Args:
            hardware_data (Dict[str, Any]): Hardware creation data

        Returns:
            Hardware: Created hardware instance
        """
        # Convert enum strings to actual enum values
        if 'hardware_type' in hardware_data:
            hardware_data['hardware_type'] = HardwareType[hardware_data['hardware_type']]

        if 'material' in hardware_data:
            hardware_data['material'] = HardwareMaterial[hardware_data['material']]

        if 'finish' in hardware_data:
            hardware_data['finish'] = HardwareFinish[hardware_data['finish']]

        hardware = Hardware(**hardware_data)
        self.session.add(hardware)
        self.session.commit()
        return hardware

    def get_hardware_by_id(self, hardware_id: int) -> Optional[Hardware]:
        """
        Retrieve a hardware item by its ID.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            Optional[Hardware]: Retrieved hardware or None
        """
        return self.session.query(Hardware).filter(Hardware.id == hardware_id).first()

    def search_hardware(
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
        query = self.session.query(Hardware)

        if hardware_type:
            query = query.filter(Hardware.hardware_type == hardware_type)

        if material:
            query = query.filter(Hardware.material == material)

        if finish:
            query = query.filter(Hardware.finish == finish)

        if min_stock is not None:
            query = query.filter(Hardware.current_stock >= min_stock)

        if max_stock is not None:
            query = query.filter(Hardware.current_stock <= max_stock)

        if min_load_capacity is not None:
            query = query.filter(Hardware.load_capacity >= min_load_capacity)

        if max_load_capacity is not None:
            query = query.filter(Hardware.load_capacity <= max_load_capacity)

        return query.all()

    def update_hardware(self, hardware_id: int, update_data: Dict[str, Any]) -> Optional[Hardware]:
        """
        Update an existing hardware item.

        Args:
            hardware_id (int): Hardware identifier
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Hardware]: Updated hardware or None
        """
        hardware = self.get_hardware_by_id(hardware_id)

        if not hardware:
            return None

        # Convert enum strings to actual enum values
        if 'hardware_type' in update_data:
            update_data['hardware_type'] = HardwareType[update_data['hardware_type']]

        if 'material' in update_data:
            update_data['material'] = HardwareMaterial[update_data['material']]

        if 'finish' in update_data:
            update_data['finish'] = HardwareFinish[update_data['finish']]

        # Update hardware attributes
        for key, value in update_data.items():
            setattr(hardware, key, value)

        self.session.commit()
        return hardware

    def delete_hardware(self, hardware_id: int) -> bool:
        """
        Delete a hardware item.

        Args:
            hardware_id (int): Hardware identifier

        Returns:
            bool: Success of deletion
        """
        hardware = self.get_hardware_by_id(hardware_id)

        if not hardware:
            return False

        try:
            self.session.delete(hardware)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting hardware: {e}")
            return False

    def get_low_stock_hardware(self, include_zero_stock: bool = False) -> List[Hardware]:
        """
        Retrieve hardware items with low stock.

        Args:
            include_zero_stock (bool): Whether to include hardware with zero stock

        Returns:
            List[Hardware]: Hardware items below minimum stock level
        """
        query = self.session.query(Hardware)

        if not include_zero_stock:
            query = query.filter(Hardware.current_stock > 0)

        return query.filter(Hardware.current_stock <= Hardware.minimum_stock_level).all()

    def get_hardware_by_supplier(self, supplier_id: int) -> List[Hardware]:
        """
        Retrieve hardware items from a specific supplier.

        Args:
            supplier_id (int): Supplier identifier

        Returns:
            List[Hardware]: Hardware items from the specified supplier
        """
        return self.session.query(Hardware).filter(Hardware.supplier_id == supplier_id).all()

    def generate_hardware_performance_report(self) -> List[Dict[str, Any]]:
        """
        Generate a performance report for hardware items.

        Returns:
            List[Dict[str, Any]]: Performance metrics for hardware
        """
        hardware_report = []

        for hardware in self.session.query(Hardware).all():
            hardware_report.append({
                'hardware_id': hardware.id,
                'name': hardware.name,
                'hardware_type': hardware.hardware_type.name,
                'performance_score': hardware.calculate_hardware_performance(),
                'current_stock': hardware.current_stock,
                'load_capacity': hardware.load_capacity,
                'corrosion_resistance': hardware.corrosion_resistance
            })

        # Sort by performance score in descending order
        return sorted(
            hardware_report,
            key=lambda x: x['performance_score'],
            reverse=True
        )