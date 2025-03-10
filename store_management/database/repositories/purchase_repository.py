# database/repositories/purchase_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.models.purchase import Purchase
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import PurchaseStatus


class PurchaseRepository(BaseRepository[Purchase]):
    """Repository for purchase operations.

    This repository provides methods for querying and manipulating purchase data,
    including relationships with suppliers, materials, and inventory.
    """

    def _get_model_class(self) -> Type[Purchase]:
        """Return the model class this repository manages.

        Returns:
            The Purchase model class
        """
        return Purchase

    # Purchase-specific query methods

    def get_by_status(self, status: PurchaseStatus) -> List[Purchase]:
        """Get purchases by status.

        Args:
            status: Purchase status to filter by

        Returns:
            List of purchase instances with the specified status
        """
        self.logger.debug(f"Getting purchases with status '{status.value}'")
        return self.session.query(Purchase).filter(Purchase.status == status).all()

    def get_by_supplier(self, supplier_id: int) -> List[Purchase]:
        """Get purchases for a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of purchase instances for the specified supplier
        """
        self.logger.debug(f"Getting purchases for supplier {supplier_id}")
        return self.session.query(Purchase).filter(Purchase.supplier_id == supplier_id).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Purchase]:
        """Get purchases within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of purchase instances within the date range
        """
        self.logger.debug(f"Getting purchases between {start_date} and {end_date}")
        return self.session.query(Purchase). \
            filter(Purchase.created_at >= start_date). \
            filter(Purchase.created_at <= end_date).all()

    def get_recent_purchases(self, days: int = 30) -> List[Purchase]:
        """Get purchases from the last X days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent purchase instances
        """
        start_date = datetime.now() - timedelta(days=days)
        self.logger.debug(f"Getting purchases from the last {days} days")
        return self.session.query(Purchase). \
            filter(Purchase.created_at >= start_date). \
            order_by(Purchase.created_at.desc()).all()

    def get_purchase_with_items(self, purchase_id: int) -> Optional[Dict[str, Any]]:
        """Get purchase with its items.

        Args:
            purchase_id: ID of the purchase

        Returns:
            Purchase with items or None if not found
        """
        self.logger.debug(f"Getting purchase {purchase_id} with items")
        from database.models.purchase_item import PurchaseItem
        from database.models.material import Material
        from database.models.tool import Tool

        purchase = self.get_by_id(purchase_id)
        if not purchase:
            return None

        # Get purchase data
        result = purchase.to_dict()

        # Get items
        items = self.session.query(PurchaseItem).filter(
            PurchaseItem.purchase_id == purchase_id
        ).all()

        result['items'] = []
        for item in items:
            item_dict = item.to_dict()

            # Add item details based on type
            if item.item_type == 'material':
                material = self.session.query(Material).get(item.item_id)
                if material:
                    item_dict['name'] = material.name
                    item_dict['material_type'] = material.material_type.value
            elif item.item_type == 'tool':
                tool = self.session.query(Tool).get(item.item_id)
                if tool:
                    item_dict['name'] = tool.name
                    item_dict['tool_type'] = tool.tool_type.value

            result['items'].append(item_dict)

        # Get supplier name
        from database.models.supplier import Supplier
        supplier = self.session.query(Supplier).get(purchase.supplier_id)
        if supplier:
            result['supplier_name'] = supplier.name

        return result

    # Business logic methods

    def create_purchase_with_items(self, purchase_data: Dict[str, Any],
                                   items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a purchase with items.

        Args:
            purchase_data: Purchase data dictionary
            items: List of item dictionaries with item_type, item_id, quantity, and price

        Returns:
            Created purchase with items
        """
        self.logger.debug("Creating purchase with items")
        from database.models.purchase_item import PurchaseItem

        try:
            # Calculate total amount
            total_amount = sum(item['quantity'] * item['price'] for item in items)
            purchase_data['total_amount'] = total_amount

            # Create purchase
            purchase = Purchase(**purchase_data)
            created_purchase = self.create(purchase)

            # Add items
            purchase_items = []
            for item_data in items:
                purchase_item = PurchaseItem(
                    purchase_id=created_purchase.id,
                    item_id=item_data['item_id'],
                    item_type=item_data['item_type'],
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )
                self.session.add(purchase_item)
                purchase_items.append(purchase_item)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = created_purchase.to_dict()
            result['items'] = [item.to_dict() for item in purchase_items]

            return result

        except Exception as e:
            self.logger.error(f"Error creating purchase with items: {str(e)}")
            raise ValidationError(f"Failed to create purchase with items: {str(e)}")

    def update_purchase_status(self, purchase_id: int,
                               status: PurchaseStatus,
                               notes: Optional[str] = None) -> Dict[str, Any]:
        """Update purchase status.

        Args:
            purchase_id: ID of the purchase
            status: New status
            notes: Optional notes about the status change

        Returns:
            Updated purchase data

        Raises:
            EntityNotFoundError: If purchase not found
        """
        self.logger.debug(f"Updating status for purchase {purchase_id} to {status.value}")

        purchase = self.get_by_id(purchase_id)
        if not purchase:
            raise EntityNotFoundError(f"Purchase with ID {purchase_id} not found")

        try:
            # Update status
            purchase.status = status

            # Add notes if provided
            if notes:
                # Append to existing notes or create new ones
                if purchase.notes:
                    purchase.notes += f"\n\n{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"
                else:
                    purchase.notes = f"{datetime.now().isoformat()}: Status changed to {status.value}\n{notes}"

            # Special handling for status changes
            if status == PurchaseStatus.DELIVERED:
                purchase.delivery_date = datetime.now()

                # Update inventory when purchase is marked as delivered
                # This would typically be done in a service layer with transaction management
                from database.models.purchase_item import PurchaseItem
                from database.models.inventory import Inventory
                from database.models.enums import InventoryStatus, InventoryAdjustmentType

                # Get purchase items
                items = self.session.query(PurchaseItem).filter(
                    PurchaseItem.purchase_id == purchase_id
                ).all()

                for item in items:
                    # Find or create inventory record
                    inventory = self.session.query(Inventory).filter(
                        Inventory.item_id == item.item_id,
                        Inventory.item_type == item.item_type
                    ).first()

                    if inventory:
                        # Update existing inventory
                        inventory.quantity += item.quantity

                        # Update status based on new quantity
                        if inventory.quantity > 0:
                            if hasattr(item, 'min_stock') and inventory.quantity <= item.min_stock:
                                inventory.status = InventoryStatus.LOW_STOCK
                            else:
                                inventory.status = InventoryStatus.IN_STOCK
                    else:
                        # Create new inventory record
                        inventory = Inventory(
                            item_id=item.item_id,
                            item_type=item.item_type,
                            quantity=item.quantity,
                            status=InventoryStatus.IN_STOCK
                        )
                        self.session.add(inventory)

                    # Record inventory transaction history (if implemented)
                    # self._record_inventory_transaction(...)

            # Update purchase
            self.update(purchase)

            return purchase.to_dict()

        except Exception as e:
            self.logger.error(f"Error updating purchase status: {str(e)}")
            raise ValidationError(f"Failed to update purchase status: {str(e)}")

    def get_purchases_for_material(self, material_id: int, period_days: int = 365) -> List[Dict[str, Any]]:
        """Get purchase history for a specific material.

        Args:
            material_id: ID of the material
            period_days: Number of days to look back

        Returns:
            List of purchases with quantities and prices
        """
        self.logger.debug(f"Getting purchase history for material {material_id} over last {period_days} days")
        from database.models.purchase_item import PurchaseItem

        # Calculate start date
        start_date = datetime.now() - timedelta(days=period_days)

        # Query for purchases containing this material
        purchase_items = self.session.query(PurchaseItem, Purchase).join(
            Purchase,
            Purchase.id == PurchaseItem.purchase_id
        ).filter(
            PurchaseItem.item_id == material_id,
            PurchaseItem.item_type == 'material',
            Purchase.created_at >= start_date
        ).order_by(
            Purchase.created_at.desc()
        ).all()

        # Format result
        result = []
        for item, purchase in purchase_items:
            result.append({
                'purchase_id': purchase.id,
                'date': purchase.created_at.isoformat(),
                'supplier_id': purchase.supplier_id,
                'quantity': item.quantity,
                'price': item.price,
                'total_cost': item.quantity * item.price,
                'status': purchase.status.value
            })

        return result

    # GUI-specific functionality

    def get_purchase_dashboard_data(self) -> Dict[str, Any]:
        """Get data for purchase dashboard in GUI.

        Returns:
            Dictionary with dashboard data for purchases
        """
        self.logger.debug("Getting purchase dashboard data")

        # Count by status
        status_counts = self.session.query(
            Purchase.status,
            func.count().label('count')
        ).group_by(Purchase.status).all()

        status_data = {s.value: count for s, count in status_counts}

        # Get total spent this month
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_total = self.session.query(
            func.sum(Purchase.total_amount)
        ).filter(
            Purchase.created_at >= first_of_month
        ).scalar() or 0

        # Get pending deliveries
        pending_deliveries = self.session.query(Purchase).filter(
            Purchase.status.in_([
                PurchaseStatus.PENDING,
                PurchaseStatus.PROCESSING,
                PurchaseStatus.SHIPPED
            ])
        ).order_by(Purchase.created_at).all()

        # Get recent purchases
        recent_purchases = self.get_recent_purchases(days=30)

        # Count purchases by month for the last 12 months
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_counts = []
        monthly_amounts = []

        for i in range(11, -1, -1):
            month_start = current_month - timedelta(days=30 * i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(seconds=1)

            count = self.session.query(func.count(Purchase.id)).filter(
                Purchase.created_at >= month_start,
                Purchase.created_at <= month_end
            ).scalar() or 0

            amount = self.session.query(func.sum(Purchase.total_amount)).filter(
                Purchase.created_at >= month_start,
                Purchase.created_at <= month_end
            ).scalar() or 0

            monthly_counts.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })

            monthly_amounts.append({
                'month': month_start.strftime('%Y-%m'),
                'amount': float(amount)
            })

        return {
            'status_counts': status_data,
            'this_month_total': float(this_month_total),
            'pending_deliveries_count': len(pending_deliveries),
            'pending_deliveries': [p.to_dict() for p in pending_deliveries[:5]],  # Top 5
            'recent_purchases': [p.to_dict() for p in recent_purchases[:5]],  # Top 5
            'monthly_counts': monthly_counts,
            'monthly_amounts': monthly_amounts
        }

    def generate_purchase_report(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 supplier_id: Optional[int] = None,
                                 item_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate purchase report with filtering options.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            supplier_id: Optional supplier ID for filtering
            item_type: Optional item type for filtering ('material', 'tool')

        Returns:
            Dict with purchase report data
        """
        self.logger.debug(
            f"Generating purchase report (start: {start_date}, end: {end_date}, supplier: {supplier_id}, item_type: {item_type})")
        from database.models.purchase_item import PurchaseItem
        from database.models.supplier import Supplier

        # Default date range is last 12 months if not specified
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Base query
        query = self.session.query(Purchase).filter(
            Purchase.created_at >= start_date,
            Purchase.created_at <= end_date
        )

        # Apply supplier filter if specified
        if supplier_id is not None:
            query = query.filter(Purchase.supplier_id == supplier_id)

        # Apply item type filter if specified
        if item_type:
            query = query.join(
                PurchaseItem,
                PurchaseItem.purchase_id == Purchase.id
            ).filter(
                PurchaseItem.item_type == item_type
            ).distinct()

        # Execute query
        purchases = query.order_by(Purchase.created_at.desc()).all()

        # Get supplier information for these purchases
        supplier_ids = {p.supplier_id for p in purchases}
        suppliers = self.session.query(Supplier).filter(
            Supplier.id.in_(supplier_ids)
        ).all()
        supplier_map = {s.id: s.to_dict() for s in suppliers}

        # Calculate summary statistics
        total_spent = sum(p.total_amount for p in purchases)
        avg_order_value = total_spent / len(purchases) if purchases else 0

        # Count by status
        status_counts = {}
        for purchase in purchases:
            status = purchase.status.value
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        # Count by supplier
        supplier_counts = {}
        supplier_amounts = {}
        for purchase in purchases:
            supplier_id = purchase.supplier_id
            if supplier_id not in supplier_counts:
                supplier_counts[supplier_id] = 0
                supplier_amounts[supplier_id] = 0
            supplier_counts[supplier_id] += 1
            supplier_amounts[supplier_id] += purchase.total_amount

        # Format purchases for report
        purchase_list = []
        for purchase in purchases:
            purchase_dict = purchase.to_dict()
            purchase_dict['supplier_name'] = supplier_map.get(purchase.supplier_id, {}).get('name', 'Unknown')
            purchase_list.append(purchase_dict)

        # Create report
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'filters': {
                'supplier_id': supplier_id,
                'item_type': item_type
            },
            'summary': {
                'total_purchases': len(purchases),
                'total_spent': float(total_spent),
                'average_order_value': float(avg_order_value),
                'status_counts': status_counts
            },
            'supplier_metrics': [
                {
                    'supplier_id': supplier_id,
                    'supplier_name': supplier_map.get(supplier_id, {}).get('name', 'Unknown'),
                    'purchase_count': count,
                    'total_spent': float(supplier_amounts[supplier_id])
                }
                for supplier_id, count in supplier_counts.items()
            ],
            'purchases': purchase_list
        }