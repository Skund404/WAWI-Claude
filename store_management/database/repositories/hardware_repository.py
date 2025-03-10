# database/repositories/hardware_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_

from database.models.material import Hardware
from database.repositories.material_repository import MaterialRepository
from database.models.enums import HardwareType, HardwareMaterial, HardwareFinish, InventoryStatus
from database.repositories.base_repository import EntityNotFoundError, ValidationError, RepositoryError


class HardwareRepository(MaterialRepository):
    """Repository for hardware-specific operations.

    This repository extends the MaterialRepository to provide specialized methods
    for hardware materials, including hardware type, material, and finish.
    """

    def _get_model_class(self) -> Type[Hardware]:
        """Return the model class this repository manages.

        Returns:
            The Hardware model class
        """
        return Hardware

    # Hardware-specific query methods

    def get_by_hardware_type(self, hardware_type: HardwareType) -> List[Hardware]:
        """Get hardware by type.

        Args:
            hardware_type: Hardware type to filter by

        Returns:
            List of hardware instances of the specified type
        """
        self.logger.debug(f"Getting hardware with type '{hardware_type.value}'")
        return self.session.query(Hardware).filter(Hardware.hardware_type == hardware_type).all()

    def get_by_hardware_material(self, material: HardwareMaterial) -> List[Hardware]:
        """Get hardware by material.

        Args:
            material: Hardware material to filter by

        Returns:
            List of hardware instances with the specified material
        """
        self.logger.debug(f"Getting hardware with material '{material.value}'")
        return self.session.query(Hardware).filter(Hardware.hardware_material == material).all()

    def get_by_finish(self, finish: HardwareFinish) -> List[Hardware]:
        """Get hardware by finish.

        Args:
            finish: Hardware finish to filter by

        Returns:
            List of hardware instances with the specified finish
        """
        self.logger.debug(f"Getting hardware with finish '{finish.value}'")
        return self.session.query(Hardware).filter(Hardware.finish == finish).all()

    def get_by_size(self, size: str) -> List[Hardware]:
        """Get hardware by size.

        Args:
            size: Hardware size to filter by

        Returns:
            List of hardware instances with the specified size
        """
        self.logger.debug(f"Getting hardware with size '{size}'")
        return self.session.query(Hardware).filter(Hardware.size == size).all()

    # Business logic methods

    def get_compatible_hardware(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get hardware compatible with a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of compatible hardware with details

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Finding compatible hardware for pattern {pattern_id}")
        from database.models.pattern import Pattern
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial

        pattern = self.session.query(Pattern).get(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # Get components in this pattern
        components = pattern.components

        # Get hardware types needed for these components
        hardware_types = set()
        for component in components:
            for cm in component.materials:
                material = self.session.query(Hardware).get(cm.material_id)
                if material and isinstance(material, Hardware):
                    hardware_types.add(material.hardware_type)

        # Find compatible hardware
        compatible_hardware = []
        for hardware_type in hardware_types:
            hardware_items = self.get_by_hardware_type(hardware_type)
            for item in hardware_items:
                hardware_dict = item.to_dict()

                # Add inventory information
                from database.models.inventory import Inventory
                inventory = self.session.query(Inventory).filter(
                    Inventory.item_id == item.id,
                    Inventory.item_type == 'material'
                ).first()

                if inventory:
                    hardware_dict['in_stock'] = inventory.quantity
                    hardware_dict['status'] = inventory.status.value
                else:
                    hardware_dict['in_stock'] = 0
                    hardware_dict['status'] = InventoryStatus.OUT_OF_STOCK.value

                compatible_hardware.append(hardware_dict)

        return compatible_hardware

    def get_hardware_sets(self) -> List[Dict[str, Any]]:
        """Get hardware grouped into functional sets (e.g., closures, rivets).

        Returns:
            List of hardware sets with items
        """
        self.logger.debug("Getting hardware sets")
        # Get all hardware
        all_hardware = self.get_all(limit=1000)

        # Group by hardware type
        hardware_sets = {}
        for hardware in all_hardware:
            set_name = hardware.hardware_type.value
            if set_name not in hardware_sets:
                hardware_sets[set_name] = {
                    'name': set_name,
                    'items': []
                }

            hardware_dict = hardware.to_dict()
            # Add inventory information
            from database.models.inventory import Inventory
            inventory = self.session.query(Inventory).filter(
                Inventory.item_id == hardware.id,
                Inventory.item_type == 'material'
            ).first()

            if inventory:
                hardware_dict['in_stock'] = inventory.quantity
                hardware_dict['status'] = inventory.status.value
            else:
                hardware_dict['in_stock'] = 0
                hardware_dict['status'] = InventoryStatus.OUT_OF_STOCK.value

            hardware_sets[set_name]['items'].append(hardware_dict)

        # Convert to list and sort by name
        result = list(hardware_sets.values())
        result.sort(key=lambda x: x['name'])

        return result

    # GUI-specific functionality

    def get_hardware_dashboard_data(self) -> Dict[str, Any]:
        """Get data for hardware dashboard in GUI.

        Returns:
            Dictionary with dashboard data specific to hardware
        """
        self.logger.debug("Getting hardware dashboard data")

        # Get base material dashboard data
        base_data = self.get_material_dashboard_data()

        # Add hardware-specific stats

        # Count by hardware type
        hardware_type_counts = self.session.query(
            Hardware.hardware_type,
            func.count().label('count')
        ).group_by(Hardware.hardware_type).all()

        type_data = {type_.value: count for type_, count in hardware_type_counts}

        # Count by material
        material_counts = self.session.query(
            Hardware.hardware_material,
            func.count().label('count')
        ).group_by(Hardware.hardware_material).all()

        material_data = {material.value: count for material, count in material_counts}

        # Count by finish
        finish_counts = self.session.query(
            Hardware.finish,
            func.count().label('count')
        ).group_by(Hardware.finish).all()

        finish_data = {finish.value: count for finish, count in finish_counts}

        # Get low stock hardware
        from database.models.inventory import Inventory
        low_stock_query = self.session.query(Hardware, Inventory).join(
            Inventory,
            and_(
                Inventory.item_id == Hardware.id,
                Inventory.item_type == 'material',
                Inventory.status == InventoryStatus.LOW_STOCK
            )
        )

        low_stock_items = []
        for hardware, inventory in low_stock_query.all():
            item = hardware.to_dict()
            item['in_stock'] = inventory.quantity
            item['status'] = inventory.status.value
            low_stock_items.append(item)

        # Combine with base data
        hardware_data = {
            **base_data,
            'hardware_type_counts': type_data,
            'hardware_material_counts': material_data,
            'hardware_finish_counts': finish_data,
            'low_stock_count': len(low_stock_items),
            'low_stock_items': low_stock_items[:10]  # Top 10 for preview
        }

        return hardware_data