# database/repositories/inventory_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Union, Tuple
from sqlalchemy import func, case, and_, or_
from datetime import datetime, timedelta

from database.models.inventory import Inventory
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import InventoryStatus, InventoryAdjustmentType, TransactionType, StorageLocationType


class InventoryRepository(BaseRepository[Inventory]):
    """Repository for inventory operations.

    This repository provides methods for managing inventory records, tracking stock levels,
    and performing inventory adjustments for materials, products, and tools.
    """

    def _get_model_class(self) -> Type[Inventory]:
        """Return the model class this repository manages.

        Returns:
            The Inventory model class
        """
        return Inventory

    # Basic query methods

    def get_by_item_type(self, item_type: str) -> List[Inventory]:
        """Get inventory by item type.

        Args:
            item_type: Type of item ('material', 'product', 'tool')

        Returns:
            List of inventory instances for the specified item type
        """
        self.logger.debug(f"Getting inventory with item type '{item_type}'")
        return self.session.query(Inventory).filter(Inventory.item_type == item_type).all()

    def get_by_status(self, status: InventoryStatus) -> List[Inventory]:
        """Get inventory by status.

        Args:
            status: Inventory status to filter by

        Returns:
            List of inventory instances with the specified status
        """
        self.logger.debug(f"Getting inventory with status '{status.value}'")
        return self.session.query(Inventory).filter(Inventory.status == status).all()

    def get_by_storage_location(self, location: str) -> List[Inventory]:
        """Get inventory by storage location.

        Args:
            location: Storage location to search for

        Returns:
            List of inventory instances in the specified location
        """
        self.logger.debug(f"Getting inventory with storage location '{location}'")
        return self.session.query(Inventory).filter(Inventory.storage_location.ilike(f"%{location}%")).all()

    def get_by_item(self, item_id: int, item_type: str) -> Optional[Inventory]:
        """Get inventory record for a specific item.

        Args:
            item_id: ID of the item
            item_type: Type of the item (material, product, tool)

        Returns:
            Inventory record if found, None otherwise
        """
        self.logger.debug(f"Getting inventory for {item_type} with ID {item_id}")
        return self.session.query(Inventory). \
            filter(Inventory.item_id == item_id). \
            filter(Inventory.item_type == item_type).first()

    def get_or_create_inventory(self, item_id: int, item_type: str, **kwargs) -> Inventory:
        """Get existing inventory record or create a new one if not found.

        Args:
            item_id: ID of the item
            item_type: Type of the item ('material', 'product', 'tool')
            **kwargs: Additional attributes for a new inventory record

        Returns:
            Existing or newly created inventory record
        """
        self.logger.debug(f"Getting or creating inventory for {item_type} with ID {item_id}")
        inventory = self.get_by_item(item_id, item_type)

        if not inventory:
            # Create new inventory record
            inventory = Inventory(
                item_id=item_id,
                item_type=item_type,
                quantity=kwargs.get('quantity', 0),
                status=kwargs.get('status', InventoryStatus.IN_STOCK),
                storage_location=kwargs.get('storage_location', '')
            )
            self.session.add(inventory)
            self.session.flush()

        return inventory

    # Inventory status methods

    def get_low_stock_items(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get items with low stock.

        Args:
            threshold: Optional override threshold (if not specified, uses per-item thresholds)

        Returns:
            List of inventory items with details from related entities
        """
        self.logger.debug(f"Getting low stock items (threshold: {threshold})")
        from database.models.material import Material
        from database.models.product import Product
        from database.models.tool import Tool

        # Prepare query with conditional joins based on item_type
        query = self.session.query(Inventory)

        # Apply threshold filtering
        if threshold is not None:
            query = query.filter(Inventory.quantity <= threshold)
        else:
            # Use the low_stock flag that is updated by inventory triggers/rules
            query = query.filter(Inventory.status == InventoryStatus.LOW_STOCK)

        results = []
        for inv in query.all():
            item_data = inv.to_dict()

            # Add item-specific details based on type
            if inv.item_type == 'material':
                material = self.session.query(Material).get(inv.item_id)
                if material:
                    item_data['name'] = material.name
                    item_data['material_type'] = material.material_type.value if hasattr(material,
                                                                                         'material_type') else None
                    item_data['min_stock'] = material.min_stock if hasattr(material, 'min_stock') else None

            elif inv.item_type == 'product':
                product = self.session.query(Product).get(inv.item_id)
                if product:
                    item_data['name'] = product.name
                    item_data['min_stock'] = product.min_stock if hasattr(product, 'min_stock') else None

            elif inv.item_type == 'tool':
                tool = self.session.query(Tool).get(inv.item_id)
                if tool:
                    item_data['name'] = tool.name
                    item_data['tool_type'] = tool.tool_type.value if hasattr(tool, 'tool_type') else None

            results.append(item_data)

        return results

    def update_inventory_status(self) -> Dict[str, int]:
        """Update inventory status based on quantity thresholds.

        Returns:
            Dictionary with counts of updated records by status
        """
        self.logger.debug("Updating inventory status based on thresholds")
        from database.models.material import Material
        from database.models.product import Product

        updates = {
            'out_of_stock': 0,
            'low_stock': 0,
            'in_stock': 0
        }

        # Get all inventory items
        inventory_items = self.get_all(limit=10000)

        for inv in inventory_items:
            old_status = inv.status

            # Determine the appropriate status based on quantity
            if inv.quantity <= 0:
                inv.status = InventoryStatus.OUT_OF_STOCK
                updates['out_of_stock'] += 1
            else:
                # Check threshold based on item type
                if inv.item_type == 'material':
                    material = self.session.query(Material).get(inv.item_id)
                    if material and hasattr(material, 'min_stock') and material.min_stock is not None:
                        if inv.quantity <= material.min_stock:
                            inv.status = InventoryStatus.LOW_STOCK
                            updates['low_stock'] += 1
                        else:
                            inv.status = InventoryStatus.IN_STOCK
                            updates['in_stock'] += 1
                elif inv.item_type == 'product':
                    product = self.session.query(Product).get(inv.item_id)
                    if product and hasattr(product, 'min_stock') and product.min_stock is not None:
                        if inv.quantity <= product.min_stock:
                            inv.status = InventoryStatus.LOW_STOCK
                            updates['low_stock'] += 1
                        else:
                            inv.status = InventoryStatus.IN_STOCK
                            updates['in_stock'] += 1
                else:
                    # Default logic for other types
                    if inv.quantity <= 2:  # Default threshold
                        inv.status = InventoryStatus.LOW_STOCK
                        updates['low_stock'] += 1
                    else:
                        inv.status = InventoryStatus.IN_STOCK
                        updates['in_stock'] += 1

            # Only update if status changed
            if old_status != inv.status:
                self.update(inv)

        return updates

    # Inventory manipulation methods

    def adjust_inventory(self, inventory_id: int, quantity_change: float,
                         adjustment_type: InventoryAdjustmentType,
                         reason: Optional[str] = None) -> Dict[str, Any]:
        """Adjust inventory with audit trail.

        Args:
            inventory_id: ID of the inventory record
            quantity_change: Amount to adjust (positive or negative)
            adjustment_type: Type of adjustment
            reason: Optional reason for the adjustment

        Returns:
            Updated inventory data

        Raises:
            EntityNotFoundError: If inventory not found
            ValidationError: If adjustment would result in negative inventory
        """
        self.logger.debug(f"Adjusting inventory {inventory_id} by {quantity_change}")
        from database.models.inventory_transaction import InventoryTransaction

        inventory = self.get_by_id(inventory_id)
        if not inventory:
            raise EntityNotFoundError(f"Inventory with ID {inventory_id} not found")

        # Calculate new quantity
        old_quantity = inventory.quantity
        new_quantity = old_quantity + quantity_change

        # Don't allow negative inventory unless explicitly allowed
        if new_quantity < 0:
            raise ValidationError(f"Adjustment would result in negative inventory: {new_quantity}")

        # Update inventory
        inventory.quantity = new_quantity

        # Update status based on new quantity
        self._update_item_status(inventory)

        # Create transaction record
        transaction = InventoryTransaction(
            inventory_id=inventory_id,
            quantity_before=old_quantity,
            quantity_after=new_quantity,
            quantity_change=quantity_change,
            adjustment_type=adjustment_type,
            transaction_date=datetime.now(),
            reason=reason
        )

        # Save changes
        self.session.add(transaction)
        self.update(inventory)

        # Return updated data
        result = inventory.to_dict()
        result['adjustment'] = {
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'change': quantity_change,
            'type': adjustment_type.value,
            'timestamp': transaction.transaction_date.isoformat(),
            'reason': reason
        }

        return result

    def _update_item_status(self, inventory: Inventory) -> None:
        """Update inventory status based on quantity and item thresholds.

        Args:
            inventory: Inventory record to update
        """
        from database.models.material import Material
        from database.models.product import Product

        # Update status based on thresholds
        if inventory.quantity <= 0:
            inventory.status = InventoryStatus.OUT_OF_STOCK
        elif inventory.item_type == 'material':
            material = self.session.query(Material).get(inventory.item_id)
            if material and hasattr(material, 'min_stock') and material.min_stock is not None:
                if inventory.quantity <= material.min_stock:
                    inventory.status = InventoryStatus.LOW_STOCK
                else:
                    inventory.status = InventoryStatus.IN_STOCK
            else:
                # Default threshold
                if inventory.quantity <= 5:
                    inventory.status = InventoryStatus.LOW_STOCK
                else:
                    inventory.status = InventoryStatus.IN_STOCK
        elif inventory.item_type == 'product':
            product = self.session.query(Product).get(inventory.item_id)
            if product and hasattr(product, 'min_stock') and product.min_stock is not None:
                if inventory.quantity <= product.min_stock:
                    inventory.status = InventoryStatus.LOW_STOCK
                else:
                    inventory.status = InventoryStatus.IN_STOCK
            else:
                # Default threshold
                if inventory.quantity <= 2:
                    inventory.status = InventoryStatus.LOW_STOCK
                else:
                    inventory.status = InventoryStatus.IN_STOCK
        else:
            # Default logic for other types
            if inventory.quantity <= 2:  # Default threshold
                inventory.status = InventoryStatus.LOW_STOCK
            else:
                inventory.status = InventoryStatus.IN_STOCK

    def track_inventory_movement(self, inventory_id: int,
                                 from_location: str, to_location: str) -> Dict[str, Any]:
        """Track movement of inventory.

        Args:
            inventory_id: ID of the inventory record
            from_location: Current storage location
            to_location: New storage location

        Returns:
            Updated inventory data

        Raises:
            EntityNotFoundError: If inventory not found
            ValidationError: If current location doesn't match
        """
        self.logger.debug(f"Tracking inventory movement from {from_location} to {to_location}")
        from database.models.location_history import LocationHistory

        inventory = self.get_by_id(inventory_id)
        if not inventory:
            raise EntityNotFoundError(f"Inventory with ID {inventory_id} not found")

        # Verify current location
        if inventory.storage_location != from_location:
            raise ValidationError(
                f"Current location mismatch: expected {from_location}, found {inventory.storage_location}")

        # Record movement history
        history = LocationHistory(
            inventory_id=inventory_id,
            from_location=from_location,
            to_location=to_location,
            move_date=datetime.now()
        )

        # Update location
        inventory.storage_location = to_location

        # Save changes
        self.session.add(history)
        self.update(inventory)

        return inventory.to_dict()

    def create_inventory_record(self, inventory_data: Dict[str, Any]) -> Inventory:
        """Create a new inventory record.

        Args:
            inventory_data: Inventory data dictionary

        Returns:
            Created inventory record

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Creating new inventory record")
        try:
            # Check required fields
            required_fields = ['item_id', 'item_type', 'quantity']
            for field in required_fields:
                if field not in inventory_data:
                    raise ValidationError(f"Missing required field: {field}")

            # Create inventory record
            inventory = Inventory(**inventory_data)

            # Set default status if not provided
            if not inventory.status:
                if inventory.quantity <= 0:
                    inventory.status = InventoryStatus.OUT_OF_STOCK
                else:
                    inventory.status = InventoryStatus.IN_STOCK

            # Add to session
            self.session.add(inventory)
            self.session.flush()

            return inventory
        except Exception as e:
            self.logger.error(f"Error creating inventory record: {str(e)}")
            raise ValidationError(f"Failed to create inventory record: {str(e)}")

    # Analysis and reporting methods

    def calculate_inventory_value(self, item_type: Optional[str] = None) -> Dict[str, Any]:
        """Calculate total inventory value.

        Args:
            item_type: Optional item type to filter by

        Returns:
            Dict with inventory valuation information
        """
        self.logger.debug(f"Calculating inventory value for item type: {item_type}")
        from database.models.material import Material
        from database.models.product import Product

        # Material inventory value
        material_query = self.session.query(
            func.sum(Inventory.quantity * Material.cost_per_unit).label('total_value'),
            func.count().label('item_count')
        ).join(
            Material,
            (Material.id == Inventory.item_id) & (Inventory.item_type == 'material')
        )

        # Product inventory value
        product_query = self.session.query(
            func.sum(Inventory.quantity * Product.price).label('total_value'),
            func.count().label('item_count')
        ).join(
            Product,
            (Product.id == Inventory.item_id) & (Inventory.item_type == 'product')
        )

        # Apply item type filter if specified
        if item_type == 'material':
            product_result = {'total_value': 0, 'item_count': 0}
            material_result = material_query.first()
        elif item_type == 'product':
            material_result = {'total_value': 0, 'item_count': 0}
            product_result = product_query.first()
        else:
            material_result = material_query.first()
            product_result = product_query.first()

        # Extract results (handle None values)
        material_value = material_result.total_value or 0 if material_result else 0
        material_count = material_result.item_count or 0 if material_result else 0

        product_value = product_result.total_value or 0 if product_result else 0
        product_count = product_result.item_count or 0 if product_result else 0

        # Total value
        total_value = material_value + product_value
        total_count = material_count + product_count

        return {
            'total_value': total_value,
            'total_items': total_count,
            'material_value': material_value,
            'material_items': material_count,
            'product_value': product_value,
            'product_items': product_count,
            'valuation_date': datetime.now().isoformat()
        }

    def get_stock_by_category(self) -> Dict[str, Dict[str, float]]:
        """Get stock levels by category for each item type.

        Returns:
            Dictionary with stock by category for each item type
        """
        self.logger.debug("Getting stock levels by category")
        from database.models.material import Material
        from database.models.product import Product
        from database.models.tool import Tool

        # Materials by material type
        material_query = self.session.query(
            Material.material_type,
            func.sum(Inventory.quantity).label('total_quantity')
        ).join(
            Inventory,
            (Inventory.item_id == Material.id) & (Inventory.item_type == 'material')
        ).group_by(
            Material.material_type
        )

        # Tools by tool type
        tool_query = self.session.query(
            Tool.tool_type,
            func.sum(Inventory.quantity).label('total_quantity')
        ).join(
            Inventory,
            (Inventory.item_id == Tool.id) & (Inventory.item_type == 'tool')
        ).group_by(
            Tool.tool_type
        )

        # Products by product type (assuming product_type field exists)
        product_query = self.session.query(
            Product.type if hasattr(Product, 'type') else func.literal('product'),
            func.sum(Inventory.quantity).label('total_quantity')
        ).join(
            Inventory,
            (Inventory.item_id == Product.id) & (Inventory.item_type == 'product')
        )

        if hasattr(Product, 'type'):
            product_query = product_query.group_by(Product.type)

        # Process results
        materials = {str(type_.value): float(quantity) for type_, quantity in material_query.all()}
        tools = {str(type_.value): float(quantity) for type_, quantity in tool_query.all()}
        products = {str(type_.value) if hasattr(type_, 'value') else 'product': float(quantity)
                    for type_, quantity in product_query.all()}

        return {
            'material': materials,
            'tool': tools,
            'product': products
        }

    # GUI-specific functionality

    def get_inventory_dashboard_data(self) -> Dict[str, Any]:
        """Get data for inventory dashboard.

        Returns:
            Dict with inventory dashboard data
        """
        self.logger.debug("Getting inventory dashboard data")

        # Get current inventory counts by status
        status_counts = self.session.query(
            Inventory.status,
            func.count().label('count')
        ).group_by(Inventory.status).all()

        status_data = {status.value: count for status, count in status_counts}

        # Get inventory value
        inventory_value = self.calculate_inventory_value()

        # Get low stock items
        low_stock = self.get_low_stock_items()

        # Get recent movements (last 7 days)
        from database.models.location_history import LocationHistory
        recent_date = datetime.now() - timedelta(days=7)

        movements = self.session.query(LocationHistory). \
            filter(LocationHistory.move_date >= recent_date). \
            order_by(LocationHistory.move_date.desc()).all()

        movement_data = [m.to_dict() for m in movements]

        # Get counts by item type
        item_type_counts = self.session.query(
            Inventory.item_type,
            func.count().label('count')
        ).group_by(Inventory.item_type).all()

        item_type_data = {item_type: count for item_type, count in item_type_counts}

        # Get inventory by location
        location_counts = self.session.query(
            Inventory.storage_location,
            func.count().label('count')
        ).filter(Inventory.storage_location != None). \
            filter(Inventory.storage_location != ''). \
            group_by(Inventory.storage_location).all()

        location_data = {loc: count for loc, count in location_counts}

        # Combine all data
        return {
            'status_counts': status_data,
            'item_type_counts': item_type_data,
            'location_counts': location_data,
            'valuation': inventory_value,
            'low_stock_count': len(low_stock),
            'low_stock_items': low_stock[:10],  # Top 10 for preview
            'recent_movements': movement_data[:10],  # Top 10 recent movements
            'total_items': sum(status_data.values()),
            'stock_by_category': self.get_stock_by_category()
        }

    def generate_inventory_report(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate inventory report.

        Args:
            filters: Optional filters to apply to the report

        Returns:
            Dict with report data and metadata
        """
        self.logger.debug(f"Generating inventory report with filters: {filters}")
        from database.models.material import Material
        from database.models.product import Product
        from database.models.tool import Tool

        # Start with base query
        query = self.session.query(Inventory)

        # Apply filters if provided
        if filters:
            if 'item_type' in filters:
                query = query.filter(Inventory.item_type == filters['item_type'])

            if 'status' in filters:
                query = query.filter(Inventory.status == filters['status'])

            if 'location' in filters:
                query = query.filter(Inventory.storage_location.ilike(f"%{filters['location']}%"))

        # Execute query
        inventory_items = query.all()

        # Transform to report data
        report_data = []
        for item in inventory_items:
            # Basic inventory data
            item_data = item.to_dict()

            # Add item-specific details based on type
            if item.item_type == 'material':
                material = self.session.query(Material).get(item.item_id)
                if material:
                    item_data['name'] = material.name
                    item_data['material_type'] = material.material_type.value if hasattr(material,
                                                                                         'material_type') else None
                    item_data['cost'] = material.cost_per_unit if hasattr(material, 'cost_per_unit') else None
                    item_data['value'] = material.cost_per_unit * item.quantity if hasattr(material,
                                                                                           'cost_per_unit') else None

            elif item.item_type == 'product':
                product = self.session.query(Product).get(item.item_id)
                if product:
                    item_data['name'] = product.name
                    item_data['price'] = product.price if hasattr(product, 'price') else None
                    item_data['value'] = product.price * item.quantity if hasattr(product, 'price') else None

            elif item.item_type == 'tool':
                tool = self.session.query(Tool).get(item.item_id)
                if tool:
                    item_data['name'] = tool.name
                    item_data['tool_type'] = tool.tool_type.value if hasattr(tool, 'tool_type') else None

            report_data.append(item_data)

        # Create report metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'item_count': len(report_data),
            'filters_applied': filters or {}
        }

        return {
            'data': report_data,
            'metadata': metadata
        }

    def filter_inventory_for_gui(self,
                                 search_term: Optional[str] = None,
                                 item_types: Optional[List[str]] = None,
                                 statuses: Optional[List[InventoryStatus]] = None,
                                 location: Optional[str] = None,
                                 sort_by: str = 'name',
                                 sort_dir: str = 'asc',
                                 page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate inventory items for GUI display.

        Args:
            search_term: Optional search term for item name
            item_types: Optional list of item types to filter by
            statuses: Optional list of statuses to filter by
            location: Optional storage location to filter by
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(
            f"Filtering inventory for GUI: search='{search_term}', types={item_types}, statuses={statuses}")
        from database.models.material import Material
        from database.models.product import Product
        from database.models.tool import Tool

        # Base query - this is complex as we need to join with different tables based on item_type
        # and we need to include names from the respective tables

        # Material items query
        material_query = self.session.query(
            Inventory.id.label('inventory_id'),
            Inventory.item_id,
            Inventory.item_type,
            Inventory.quantity,
            Inventory.status,
            Inventory.storage_location,
            Material.name.label('name')
        ).join(
            Material, (Material.id == Inventory.item_id) & (Inventory.item_type == 'material')
        )

        # Product items query
        product_query = self.session.query(
            Inventory.id.label('inventory_id'),
            Inventory.item_id,
            Inventory.item_type,
            Inventory.quantity,
            Inventory.status,
            Inventory.storage_location,
            Product.name.label('name')
        ).join(
            Product, (Product.id == Inventory.item_id) & (Inventory.item_type == 'product')
        )

        # Tool items query
        tool_query = self.session.query(
            Inventory.id.label('inventory_id'),
            Inventory.item_id,
            Inventory.item_type,
            Inventory.quantity,
            Inventory.status,
            Inventory.storage_location,
            Tool.name.label('name')
        ).join(
            Tool, (Tool.id == Inventory.item_id) & (Inventory.item_type == 'tool')
        )

        # Filter by item types if provided
        if item_types:
            if 'material' not in item_types:
                material_query = material_query.filter(False)  # Exclude materials
            if 'product' not in item_types:
                product_query = product_query.filter(False)  # Exclude products
            if 'tool' not in item_types:
                tool_query = tool_query.filter(False)  # Exclude tools

        # Apply status filter if provided
        if statuses:
            material_query = material_query.filter(Inventory.status.in_(statuses))
            product_query = product_query.filter(Inventory.status.in_(statuses))
            tool_query = tool_query.filter(Inventory.status.in_(statuses))

        # Apply location filter if provided
        if location:
            material_query = material_query.filter(Inventory.storage_location.ilike(f"%{location}%"))
            product_query = product_query.filter(Inventory.storage_location.ilike(f"%{location}%"))
            tool_query = tool_query.filter(Inventory.storage_location.ilike(f"%{location}%"))

        # Apply search filter if provided
        if search_term:
            material_query = material_query.filter(Material.name.ilike(f"%{search_term}%"))
            product_query = product_query.filter(Product.name.ilike(f"%{search_term}%"))
            tool_query = tool_query.filter(Tool.name.ilike(f"%{search_term}%"))

        # Union all queries
        from sqlalchemy import union_all
        union_query = union_all(material_query, product_query, tool_query).alias('combined')

        # Create a query from the union
        final_query = self.session.query(union_query)

        # Get total count for pagination
        total_count = final_query.count()

        # Apply sorting (sorting by name is complex with the union)
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                final_query = final_query.order_by(union_query.c.name.desc())
            else:
                final_query = final_query.order_by(union_query.c.name.asc())
        elif sort_by == 'quantity':
            if sort_dir.lower() == 'desc':
                final_query = final_query.order_by(union_query.c.quantity.desc())
            else:
                final_query = final_query.order_by(union_query.c.quantity.asc())
        elif sort_by == 'status':
            if sort_dir.lower() == 'desc':
                final_query = final_query.order_by(union_query.c.status.desc())
            else:
                final_query = final_query.order_by(union_query.c.status.asc())
        elif sort_by == 'location':
            if sort_dir.lower() == 'desc':
                final_query = final_query.order_by(union_query.c.storage_location.desc())
            else:
                final_query = final_query.order_by(union_query.c.storage_location.asc())
        elif sort_by == 'type':
            if sort_dir.lower() == 'desc':
                final_query = final_query.order_by(union_query.c.item_type.desc())
            else:
                final_query = final_query.order_by(union_query.c.item_type.asc())
        else:
            # Default to name ascending
            final_query = final_query.order_by(union_query.c.name.asc())

        # Apply pagination
        final_query = final_query.offset((page - 1) * page_size).limit(page_size)

        # Execute query and format results
        results = final_query.all()
        items = [
            {
                'inventory_id': row.inventory_id,
                'item_id': row.item_id,
                'item_type': row.item_type,
                'name': row.name,
                'quantity': row.quantity,
                'status': row.status.value,
                'storage_location': row.storage_location
            }
            for row in results
        ]

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

    def bulk_update_locations(self, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update storage locations for multiple inventory items.

        Args:
            items_data: List of items with inventory_id and new_location

        Returns:
            Dict with update results

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug(f"Bulk updating storage locations for {len(items_data)} items")
        from database.models.location_history import LocationHistory

        updates = []
        history_records = []

        try:
            for item in items_data:
                inventory_id = item.get('inventory_id')
                new_location = item.get('new_location')

                if not inventory_id or not new_location:
                    raise ValidationError(f"Missing inventory_id or new_location in item data")

                inventory = self.get_by_id(inventory_id)
                if not inventory:
                    raise ValidationError(f"Inventory with ID {inventory_id} not found")

                old_location = inventory.storage_location
                inventory.storage_location = new_location

                # Create history record
                history = LocationHistory(
                    inventory_id=inventory_id,
                    from_location=old_location or '',
                    to_location=new_location,
                    move_date=datetime.now()
                )
                history_records.append(history)

                # Update inventory
                self.update(inventory)

                updates.append({
                    'inventory_id': inventory_id,
                    'item_id': inventory.item_id,
                    'item_type': inventory.item_type,
                    'old_location': old_location,
                    'new_location': new_location
                })

            # Add history records
            self.session.add_all(history_records)

            return {
                'success': True,
                'updated_count': len(updates),
                'updates': updates
            }
        except Exception as e:
            self.logger.error(f"Error updating locations: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to update locations: {str(e)}")