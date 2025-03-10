# database/repositories/leather_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_

from database.models.material import Leather
from database.repositories.material_repository import MaterialRepository
from database.models.enums import LeatherType, LeatherFinish, MaterialType, InventoryStatus
from database.repositories.base_repository import EntityNotFoundError, ValidationError, RepositoryError


class LeatherRepository(MaterialRepository):
    """Repository for leather-specific operations.

    This repository extends the MaterialRepository to provide specialized methods
    for leather materials, including thickness, area, and leather-specific attributes.
    """

    def _get_model_class(self) -> Type[Leather]:
        """Return the model class this repository manages.

        Returns:
            The Leather model class
        """
        return Leather

    # Leather-specific query methods

    def get_by_leather_type(self, leather_type: LeatherType) -> List[Leather]:
        """Get leather by type.

        Args:
            leather_type: Leather type to filter by

        Returns:
            List of leather instances of the specified type
        """
        self.logger.debug(f"Getting leather with type '{leather_type.value}'")
        return self.session.query(Leather).filter(Leather.leather_type == leather_type).all()

    def get_by_finish(self, finish: LeatherFinish) -> List[Leather]:
        """Get leather by finish.

        Args:
            finish: Leather finish to filter by

        Returns:
            List of leather instances with the specified finish
        """
        self.logger.debug(f"Getting leather with finish '{finish.value}'")
        return self.session.query(Leather).filter(Leather.finish == finish).all()

    def get_by_thickness(self, min_thickness: float, max_thickness: float) -> List[Leather]:
        """Get leather within thickness range.

        Args:
            min_thickness: Minimum thickness in mm
            max_thickness: Maximum thickness in mm

        Returns:
            List of leather instances within the thickness range
        """
        self.logger.debug(f"Getting leather with thickness between {min_thickness} and {max_thickness}")
        return self.session.query(Leather). \
            filter(Leather.thickness >= min_thickness). \
            filter(Leather.thickness <= max_thickness).all()

    def get_full_hides(self) -> List[Leather]:
        """Get all full hides in inventory.

        Returns:
            List of leather instances that are full hides
        """
        self.logger.debug("Getting all full hides")
        return self.session.query(Leather).filter(Leather.is_full_hide == True).all()

    def get_by_area(self, min_area: float, max_area: float) -> List[Leather]:
        """Get leather by area range.

        Args:
            min_area: Minimum area in square feet/meters
            max_area: Maximum area in square feet/meters

        Returns:
            List of leather instances within the area range
        """
        self.logger.debug(f"Getting leather with area between {min_area} and {max_area}")
        return self.session.query(Leather). \
            filter(Leather.area >= min_area). \
            filter(Leather.area <= max_area).all()

    # Business logic methods

    def calculate_cutting_yield(self, leather_id: int, pattern_id: int) -> Dict[str, Any]:
        """Calculate expected yield for pattern from leather.

        Args:
            leather_id: ID of the leather to use
            pattern_id: ID of the pattern to calculate yield for

        Returns:
            Dict with yield information

        Raises:
            EntityNotFoundError: If leather or pattern not found
        """
        self.logger.debug(f"Calculating cutting yield for leather {leather_id} and pattern {pattern_id}")
        from database.models.pattern import Pattern

        leather = self.get_by_id(leather_id)
        if not leather:
            raise EntityNotFoundError(f"Leather with ID {leather_id} not found")

        pattern = self.session.query(Pattern).get(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # Calculate yield based on pattern requirements and leather dimensions
        # This is a simplified example - real implementation would be more complex
        total_area_needed = 0
        components = pattern.components

        for component in components:
            # Calculate component area needed
            # (simplified - would need actual component dimensions)
            component_area = component.length * component.width if hasattr(component, 'length') and hasattr(component,
                                                                                                            'width') else 0.25
            total_area_needed += component_area * component.quantity

        pieces_possible = int(leather.area / total_area_needed)
        wastage = leather.area - (pieces_possible * total_area_needed)
        efficiency = (pieces_possible * total_area_needed) / leather.area * 100

        return {
            'leather_id': leather_id,
            'pattern_id': pattern_id,
            'leather_area': leather.area,
            'area_per_piece': total_area_needed,
            'pieces_possible': pieces_possible,
            'wastage_area': wastage,
            'efficiency_percent': efficiency
        }

    def track_hide_usage(self, leather_id: int, area_used: float) -> Dict[str, Any]:
        """Track usage of leather hide.

        Args:
            leather_id: ID of the leather to track
            area_used: Area of leather used

        Returns:
            Dict with updated leather information

        Raises:
            EntityNotFoundError: If leather not found
            ValidationError: If usage exceeds available area
        """
        self.logger.debug(f"Tracking hide usage for leather {leather_id}, area used: {area_used}")
        leather = self.get_by_id(leather_id)
        if not leather:
            raise EntityNotFoundError(f"Leather with ID {leather_id} not found")

        # Update remaining area
        if leather.area < area_used:
            raise ValidationError(f"Usage area ({area_used}) exceeds available area ({leather.area})")

        leather.area -= area_used

        # Check if hide is now "used up"
        if leather.area < 0.01:  # Small threshold to account for floating point
            leather.area = 0

        self.update(leather)

        # Update inventory if needed
        from database.models.inventory import Inventory
        inventory = self.session.query(Inventory). \
            filter(Inventory.item_id == leather_id). \
            filter(Inventory.item_type == 'material').first()

        if inventory:
            # For leather, we might need to update inventory based on area changes
            # This depends on how inventory is tracked (by area or by count)
            # For simplicity, let's assume leather inventory is tracked by area
            inventory.quantity = leather.area

            # Update status if needed
            if inventory.quantity <= 0:
                inventory.status = InventoryStatus.OUT_OF_STOCK
            elif inventory.quantity <= leather.min_stock:
                inventory.status = InventoryStatus.LOW_STOCK

            self.session.add(inventory)
            self.session.flush()

        # Add usage history record (if implemented)
        # self._record_hide_usage(leather_id, area_used)

        return leather.to_dict()

    def split_hide(self, leather_id: int, new_areas: List[float]) -> List[Dict[str, Any]]:
        """Split a leather hide into multiple pieces.

        Args:
            leather_id: ID of the leather hide to split
            new_areas: List of areas for the new pieces

        Returns:
            List of new leather pieces created

        Raises:
            EntityNotFoundError: If leather not found
            ValidationError: If areas exceed available area
        """
        self.logger.debug(f"Splitting hide {leather_id} into {len(new_areas)} pieces")
        leather = self.get_by_id(leather_id)
        if not leather:
            raise EntityNotFoundError(f"Leather with ID {leather_id} not found")

        # Validate total area
        total_new_area = sum(new_areas)
        if total_new_area > leather.area:
            raise ValidationError(f"Total new area ({total_new_area}) exceeds available area ({leather.area})")

        # Create new leather pieces
        new_leathers = []
        remaining_area = leather.area

        try:
            for i, area in enumerate(new_areas):
                # Create new leather piece
                new_leather_data = leather.to_dict()
                # Remove id and set new name
                new_leather_data.pop('id', None)
                new_leather_data['name'] = f"{leather.name} - Piece {i + 1}"
                new_leather_data['area'] = area
                new_leather_data['is_full_hide'] = False

                new_leather = Leather(**new_leather_data)
                self.session.add(new_leather)
                self.session.flush()  # Flush to get the new ID

                # Create inventory record for the new piece
                from database.models.inventory import Inventory
                inventory = Inventory(
                    item_id=new_leather.id,
                    item_type='material',
                    quantity=area,
                    status=InventoryStatus.IN_STOCK,
                    storage_location=self._get_leather_storage_location(leather_id)
                )
                self.session.add(inventory)

                remaining_area -= area
                new_leathers.append(new_leather.to_dict())

            # Update original leather
            if remaining_area > 0.01:  # Keep original with remaining area
                leather.area = remaining_area
                leather.is_full_hide = False
                self.update(leather)
            else:  # Delete original if used up
                self.delete(leather)

                # Remove inventory for original
                from database.models.inventory import Inventory
                original_inventory = self.session.query(Inventory). \
                    filter(Inventory.item_id == leather_id). \
                    filter(Inventory.item_type == 'material').first()

                if original_inventory:
                    self.session.delete(original_inventory)

            return new_leathers

        except Exception as e:
            self.logger.error(f"Error splitting hide: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to split hide: {str(e)}")

    def _get_leather_storage_location(self, leather_id: int) -> str:
        """Get storage location for a leather hide.

        Args:
            leather_id: ID of the leather

        Returns:
            Storage location or empty string if not found
        """
        from database.models.inventory import Inventory
        inventory = self.session.query(Inventory). \
            filter(Inventory.item_id == leather_id). \
            filter(Inventory.item_type == 'material').first()

        return inventory.storage_location if inventory else ""

    # GUI-specific functionality

    def get_leather_with_images(self) -> List[Dict[str, Any]]:
        """Get leather data with associated images.

        Returns:
            List of leather dictionaries with image information
        """
        self.logger.debug("Getting leather with images")
        # In a real implementation, this would join with an images table
        # For now, we'll simulate this with placeholder data

        leathers = self.get_all(limit=1000)
        result = []

        for leather in leathers:
            leather_dict = leather.to_dict()

            # Add placeholder image data
            # In a real implementation, you would query the images table
            leather_dict['images'] = [
                {
                    'id': f"img_{leather.id}_1",
                    'url': f"/static/images/leather_{leather.id}_1.jpg",
                    'is_primary': True,
                    'filename': f"leather_{leather.id}_1.jpg"
                }
            ]

            result.append(leather_dict)

        return result

    def get_leather_dashboard_data(self) -> Dict[str, Any]:
        """Get data for leather dashboard in GUI.

        Returns:
            Dictionary with dashboard data specific to leather
        """
        self.logger.debug("Getting leather dashboard data")

        # Get base material dashboard data
        base_data = self.get_material_dashboard_data()

        # Add leather-specific stats

        # Count by leather type
        leather_type_counts = self.session.query(
            Leather.leather_type,
            func.count().label('count')
        ).group_by(Leather.leather_type).all()

        type_data = {type_.value: count for type_, count in leather_type_counts}

        # Get full hide count
        full_hide_count = self.session.query(func.count()). \
                              filter(Leather.is_full_hide == True).scalar() or 0

        # Get thickness distribution
        thickness_ranges = [
            (0, 1.0),
            (1.0, 2.0),
            (2.0, 3.0),
            (3.0, 4.0),
            (4.0, 999)
        ]

        thickness_distribution = {}
        for min_val, max_val in thickness_ranges:
            count = self.session.query(func.count()). \
                        filter(Leather.thickness >= min_val). \
                        filter(Leather.thickness < max_val).scalar() or 0

            label = f"{min_val}-{max_val if max_val < 999 else '+'} mm"
            thickness_distribution[label] = count

        # Combine with base data
        leather_data = {
            **base_data,
            'leather_type_counts': type_data,
            'full_hide_count': full_hide_count,
            'thickness_distribution': thickness_distribution,
            'leather_by_finish': self._get_leather_by_finish()
        }

        return leather_data

    def _get_leather_by_finish(self) -> Dict[str, int]:
        """Get leather counts by finish.

        Returns:
            Dictionary of finish to count
        """
        finish_counts = self.session.query(
            Leather.finish,
            func.count().label('count')
        ).group_by(Leather.finish).all()

        return {finish.value: count for finish, count in finish_counts}