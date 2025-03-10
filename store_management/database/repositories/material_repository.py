# database/repositories/material_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Union, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_

from database.models.material import Material
from database.models.inventory import Inventory
from database.models.enums import MaterialType, MeasurementUnit, QualityGrade, InventoryStatus
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError


class MaterialRepository(BaseRepository[Material]):
    """Repository for material management operations.

    This repository provides specialized methods for accessing and manipulating
    material data, along with business logic operations and GUI-specific functionality.
    """

    def _get_model_class(self) -> Type[Material]:
        """Return the model class this repository manages.

        Returns:
            The Material model class
        """
        return Material

    # Basic query methods

    def get_by_name(self, name: str) -> Optional[Material]:
        """Get material by exact name match.

        Args:
            name: Material name to search for

        Returns:
            Material instance or None if not found
        """
        self.logger.debug(f"Getting material with name '{name}'")
        return self.session.query(Material).filter(Material.name == name).first()

    def get_by_supplier(self, supplier_id: int) -> List[Material]:
        """Get materials from specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of material instances from the specified supplier
        """
        self.logger.debug(f"Getting materials from supplier ID {supplier_id}")
        return self.session.query(Material).filter(Material.supplier_id == supplier_id).all()

    def get_by_material_type(self, material_type: MaterialType) -> List[Material]:
        """Get materials of specific type.

        Args:
            material_type: Material type to filter by

        Returns:
            List of material instances of the specified type
        """
        self.logger.debug(f"Getting materials with type '{material_type.value}'")
        return self.session.query(Material).filter(Material.material_type == material_type).all()

    def search_materials(self, search_term: str, material_types: Optional[List[MaterialType]] = None) -> List[Material]:
        """Search materials by term with optional type filtering.

        Args:
            search_term: Term to search for in name and description
            material_types: Optional list of material types to filter by

        Returns:
            List of matching material instances
        """
        self.logger.debug(f"Searching materials with term '{search_term}' and types {material_types}")
        query = self.session.query(Material).filter(
            or_(
                Material.name.ilike(f"%{search_term}%"),
                Material.description.ilike(f"%{search_term}%") if hasattr(Material, 'description') else False
            )
        )

        if material_types:
            query = query.filter(Material.material_type.in_(material_types))

        return query.all()

    # Inventory-related methods

    def get_with_inventory_status(self) -> List[Dict[str, Any]]:
        """Get materials with current inventory status.

        Returns:
            List of material dictionaries with inventory information
        """
        self.logger.debug("Getting materials with inventory status")
        from database.models.inventory import Inventory

        query = self.session.query(Material, Inventory). \
            outerjoin(Inventory,
                      (Inventory.item_id == Material.id) &
                      (Inventory.item_type == 'material'))

        result = []
        for material, inventory in query.all():
            material_dict = material.to_dict()
            if inventory:
                material_dict['current_stock'] = inventory.quantity
                material_dict['stock_status'] = inventory.status.value
                material_dict['storage_location'] = inventory.storage_location
            else:
                material_dict['current_stock'] = 0
                material_dict['stock_status'] = 'NOT_TRACKED'
                material_dict['storage_location'] = None
            result.append(material_dict)

        return result

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with stock below threshold.

        Args:
            threshold: Optional override for default low stock threshold

        Returns:
            List of materials with inventory details
        """
        self.logger.debug(f"Getting low stock materials (threshold: {threshold})")
        from database.models.inventory import Inventory

        # Join with inventory to get current stock levels
        query = self.session.query(Material, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Material.id) &
                 (Inventory.item_type == 'material'))

        # Apply threshold filtering
        if threshold is not None:
            query = query.filter(Inventory.quantity <= threshold)
        else:
            # Use material-specific thresholds stored in material.min_stock
            query = query.filter(Inventory.quantity <= Material.min_stock)

        result = []
        for material, inventory in query.all():
            material_dict = material.to_dict()
            material_dict['current_stock'] = inventory.quantity
            material_dict['stock_status'] = inventory.status.value
            material_dict['storage_location'] = inventory.storage_location
            result.append(material_dict)

        return result

    def get_out_of_stock_materials(self) -> List[Dict[str, Any]]:
        """Get materials that are out of stock.

        Returns:
            List of out-of-stock material dictionaries with inventory information
        """
        self.logger.debug("Getting out of stock materials")
        from database.models.inventory import Inventory

        query = self.session.query(Material, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Material.id) &
                 (Inventory.item_type == 'material')). \
            filter(or_(
            Inventory.quantity <= 0,
            Inventory.status == InventoryStatus.OUT_OF_STOCK
        ))

        result = []
        for material, inventory in query.all():
            material_dict = material.to_dict()
            material_dict['current_stock'] = inventory.quantity
            material_dict['stock_status'] = inventory.status.value
            material_dict['storage_location'] = inventory.storage_location
            result.append(material_dict)

        return result

    # Business logic methods

    def create_material_with_inventory(self, material_data: Dict[str, Any], inventory_data: Dict[str, Any]) -> Dict[
        str, Any]:
        """Create a new material with associated inventory record.

        Args:
            material_data: Material data dictionary
            inventory_data: Inventory data dictionary

        Returns:
            Created material with inventory information

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Creating new material with inventory")
        from database.models.inventory import Inventory

        try:
            # Create material
            material = Material(**material_data)
            created_material = self.create(material)

            # Create inventory record
            inventory = Inventory(
                item_id=created_material.id,
                item_type='material',
                **inventory_data
            )
            self.session.add(inventory)
            self.session.flush()

            # Prepare result
            result = created_material.to_dict()
            result['inventory'] = inventory.to_dict()

            return result
        except Exception as e:
            self.logger.error(f"Error creating material with inventory: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to create material with inventory: {str(e)}")

    def get_materials_with_supplier_info(self, material_type: Optional[MaterialType] = None) -> List[Dict[str, Any]]:
        """Get materials with supplier information.

        Args:
            material_type: Optional material type to filter by

        Returns:
            List of materials with supplier details
        """
        self.logger.debug(f"Getting materials with supplier info for type {material_type}")
        from database.models.supplier import Supplier

        query = self.session.query(Material, Supplier). \
            outerjoin(Supplier, Material.supplier_id == Supplier.id)

        if material_type:
            query = query.filter(Material.material_type == material_type)

        result = []
        for material, supplier in query.all():
            material_dict = material.to_dict()
            if supplier:
                material_dict['supplier'] = supplier.to_dict()
            result.append(material_dict)

        return result

    def get_material_usage_by_component(self, material_id: int) -> List[Dict[str, Any]]:
        """Get component usage information for a specific material.

        Args:
            material_id: ID of the material

        Returns:
            List of components using this material with quantities

        Raises:
            EntityNotFoundError: If material not found
        """
        self.logger.debug(f"Getting component usage for material ID {material_id}")
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial

        material = self.get_by_id(material_id)
        if not material:
            raise EntityNotFoundError(f"Material with ID {material_id} not found")

        query = self.session.query(
            Component, ComponentMaterial
        ).join(
            ComponentMaterial, ComponentMaterial.component_id == Component.id
        ).filter(
            ComponentMaterial.material_id == material_id
        )

        result = []
        for component, component_material in query.all():
            result.append({
                'component_id': component.id,
                'component_name': component.name,
                'component_type': component.component_type.value,
                'quantity_per_component': component_material.quantity,
                'material_id': material_id,
                'material_name': material.name,
                'material_unit': material.unit.value
            })

        return result

    def calculate_reorder_quantities(self, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
        """Calculate suggested reorder quantities for materials.

        Args:
            threshold_multiplier: Multiplier for min_stock to determine reorder quantity

        Returns:
            List of materials with reorder recommendations
        """
        self.logger.debug(f"Calculating reorder quantities with multiplier {threshold_multiplier}")
        from database.models.inventory import Inventory

        # Get materials that are below or close to min_stock
        query = self.session.query(Material, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Material.id) &
                 (Inventory.item_type == 'material')). \
            filter(Inventory.quantity <= Material.min_stock * 1.2)  # Include those slightly above threshold

        result = []
        for material, inventory in query.all():
            # Skip if quantity is sufficient
            if inventory.quantity > material.min_stock:
                continue

            # Calculate reorder quantity
            deficit = material.min_stock - inventory.quantity
            reorder_quantity = max(deficit, material.min_stock * threshold_multiplier)

            material_dict = material.to_dict()
            material_dict['current_stock'] = inventory.quantity
            material_dict['min_stock'] = material.min_stock
            material_dict['deficit'] = deficit
            material_dict['recommended_reorder'] = round(reorder_quantity, 2)
            material_dict['stock_status'] = inventory.status.value

            result.append(material_dict)

        return result

    # GUI-specific functionality

    def get_material_dashboard_data(self) -> Dict[str, Any]:
        """Get data for material dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting material dashboard data")
        from database.models.inventory import Inventory

        # Get counts by material type
        type_counts = self.session.query(
            Material.material_type,
            func.count().label('count')
        ).group_by(Material.material_type).all()

        type_data = {type_.value: count for type_, count in type_counts}

        # Get inventory status counts
        inventory_status = self.session.query(
            Inventory.status,
            func.count().label('count')
        ).filter(
            Inventory.item_type == 'material'
        ).group_by(Inventory.status).all()

        status_data = {status.value: count for status, count in inventory_status}

        # Get low stock materials
        low_stock_materials = self.get_low_stock()

        # Get out of stock materials
        out_of_stock = self.get_out_of_stock_materials()

        # Get material value by type (joining with inventory)
        value_by_type = self.session.query(
            Material.material_type,
            func.sum(Material.cost_per_unit * Inventory.quantity).label('total_value')
        ).join(
            Inventory,
            (Inventory.item_id == Material.id) & (Inventory.item_type == 'material')
        ).group_by(
            Material.material_type
        ).all()

        type_value = {type_.value: float(value) if value else 0 for type_, value in value_by_type}

        # Combine all data
        return {
            'type_counts': type_data,
            'status_counts': status_data,
            'total_materials': sum(type_data.values()),
            'low_stock_count': len(low_stock_materials),
            'low_stock_materials': low_stock_materials[:5],  # Top 5
            'out_of_stock_count': len(out_of_stock),
            'out_of_stock_materials': out_of_stock[:5],  # Top 5
            'inventory_value_by_type': type_value,
            'total_inventory_value': sum(type_value.values()),
            'materials_by_location': self._get_materials_by_location(),
            'reorder_recommendations': self.calculate_reorder_quantities()[:5]  # Top 5
        }

    def _get_materials_by_location(self) -> Dict[str, int]:
        """Get material counts by storage location.

        Returns:
            Dictionary of location to count
        """
        from database.models.inventory import Inventory

        location_query = self.session.query(
            Inventory.storage_location,
            func.count().label('count')
        ).filter(
            Inventory.item_type == 'material'
        ).group_by(
            Inventory.storage_location
        ).order_by(
            func.count().desc()
        )

        return {loc: count for loc, count in location_query.all() if loc}

    def export_material_data(self, format: str = "csv") -> Dict[str, Any]:
        """Export material data to specified format.

        Args:
            format: Export format ("csv" or "json")

        Returns:
            Dict with export data and metadata
        """
        self.logger.debug(f"Exporting material data in {format} format")
        materials = self.get_with_inventory_status()

        # Create metadata
        metadata = {
            'count': len(materials),
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'material_types': self._get_material_type_counts()
        }

        return {
            'data': materials,
            'metadata': metadata
        }

    def _get_material_type_counts(self) -> Dict[str, int]:
        """Get material counts by type.

        Returns:
            Dictionary of material type to count
        """
        type_counts = self.session.query(
            Material.material_type,
            func.count().label('count')
        ).group_by(Material.material_type).all()

        return {type_.value: count for type_, count in type_counts}

    def filter_materials_for_gui(self,
                                 search_term: Optional[str] = None,
                                 material_types: Optional[List[MaterialType]] = None,
                                 supplier_id: Optional[int] = None,
                                 in_stock_only: bool = False,
                                 sort_by: str = 'name',
                                 sort_dir: str = 'asc',
                                 page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate materials for GUI display.

        Args:
            search_term: Optional search term
            material_types: Optional list of material types to filter by
            supplier_id: Optional supplier ID to filter by
            in_stock_only: Whether to only include in-stock materials
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(
            f"Filtering materials for GUI: search='{search_term}', types={material_types}, supplier={supplier_id}")
        from database.models.inventory import Inventory

        # Start with a query that joins Material and Inventory
        query = self.session.query(Material, Inventory). \
            outerjoin(Inventory,
                      (Inventory.item_id == Material.id) &
                      (Inventory.item_type == 'material'))

        # Apply search filter if provided
        if search_term:
            query = query.filter(
                or_(
                    Material.name.ilike(f"%{search_term}%"),
                    Material.description.ilike(f"%{search_term}%") if hasattr(Material, 'description') else False
                )
            )

        # Apply material type filter if provided
        if material_types:
            query = query.filter(Material.material_type.in_(material_types))

        # Apply supplier filter if provided
        if supplier_id:
            query = query.filter(Material.supplier_id == supplier_id)

        # Apply stock filter if requested
        if in_stock_only:
            query = query.filter(
                (Inventory.quantity > 0) & (Inventory.status != InventoryStatus.OUT_OF_STOCK)
            )

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Material.name.desc())
            else:
                query = query.order_by(Material.name.asc())
        elif sort_by == 'type':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Material.material_type.desc())
            else:
                query = query.order_by(Material.material_type.asc())
        elif sort_by == 'stock':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Inventory.quantity.desc())
            else:
                query = query.order_by(Inventory.quantity.asc())
        elif sort_by == 'cost':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Material.cost_per_unit.desc())
            else:
                query = query.order_by(Material.cost_per_unit.asc())
        else:
            # Default to name
            query = query.order_by(Material.name.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query and format results
        items = []
        for material, inventory in query.all():
            material_dict = material.to_dict()
            if inventory:
                material_dict['current_stock'] = inventory.quantity
                material_dict['stock_status'] = inventory.status.value
                material_dict['storage_location'] = inventory.storage_location
            else:
                material_dict['current_stock'] = 0
                material_dict['stock_status'] = 'NOT_TRACKED'
                material_dict['storage_location'] = None
            items.append(material_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }