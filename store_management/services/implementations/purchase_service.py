from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from database.repositories.purchase_repository import PurchaseRepository
from database.repositories.purchase_item_repository import PurchaseItemRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.tool_repository import ToolRepository
from database.repositories.inventory_repository import InventoryRepository

from database.models.enums import PurchaseStatus, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from services.dto.purchase_dto import PurchaseDTO, PurchaseItemDTO

from di.core import inject


class PurchaseService(BaseService):
    """Implementation of the purchase service interface."""

    @inject
    def __init__(self, session: Session,
                 purchase_repository: Optional[PurchaseRepository] = None,
                 purchase_item_repository: Optional[PurchaseItemRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 tool_repository: Optional[ToolRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the purchase service."""
        super().__init__(session)
        self.purchase_repository = purchase_repository or PurchaseRepository(session)
        self.purchase_item_repository = purchase_item_repository or PurchaseItemRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, purchase_id: int) -> Dict[str, Any]:
        """Get purchase by ID."""
        try:
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")
            return PurchaseDTO.from_model(purchase, include_supplier=True, include_items=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving purchase {purchase_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all purchases, optionally filtered."""
        try:
            purchases = self.purchase_repository.get_all(filters=filters)
            return [PurchaseDTO.from_model(purchase, include_supplier=True).to_dict() for purchase in purchases]
        except Exception as e:
            self.logger.error(f"Error retrieving purchases: {str(e)}")
            raise

    def create(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase."""
        try:
            # Validate purchase data
            self._validate_purchase_data(purchase_data)

            # Set default status if not provided
            if 'status' not in purchase_data:
                purchase_data['status'] = PurchaseStatus.DRAFT.value

            # Handle items separately if provided
            items = purchase_data.pop('items', []) if 'items' in purchase_data else []

            # Create purchase
            with self.transaction():
                purchase = self.purchase_repository.create(purchase_data)

                # Add items if provided
                for item_data in items:
                    item_data['purchase_id'] = purchase.id
                    self._validate_purchase_item_data(item_data)
                    self.purchase_item_repository.create(item_data)

                # Calculate total amount
                self._update_purchase_total(purchase.id)

                # Get the complete purchase with items
                result = self.purchase_repository.get_by_id(purchase.id)
                return PurchaseDTO.from_model(result, include_supplier=True, include_items=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating purchase: {str(e)}")
            raise

    def update(self, purchase_id: int, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Validate purchase data
            self._validate_purchase_data(purchase_data, update=True)

            # Prevent updating delivered purchases
            if purchase.status == PurchaseStatus.DELIVERED.value:
                raise BusinessRuleError(f"Cannot update a delivered purchase")

            # Prevent changing supplier for orders that are already placed
            if ('supplier_id' in purchase_data and
                    purchase_data['supplier_id'] != purchase.supplier_id and
                    purchase.status not in [PurchaseStatus.DRAFT.value, PurchaseStatus.PENDING.value]):
                raise BusinessRuleError(f"Cannot change supplier for a purchase with status {purchase.status}")

            # Update purchase
            with self.transaction():
                updated_purchase = self.purchase_repository.update(purchase_id, purchase_data)

                # Recalculate total if needed
                if any(field in purchase_data for field in ['shipping_cost', 'tax_amount']):
                    self._update_purchase_total(purchase_id)
                    updated_purchase = self.purchase_repository.get_by_id(purchase_id)

                return PurchaseDTO.from_model(updated_purchase, include_supplier=True, include_items=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating purchase {purchase_id}: {str(e)}")
            raise

    def delete(self, purchase_id: int) -> bool:
        """Delete a purchase by ID."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Prevent deleting purchases that are not in draft status
            if purchase.status != PurchaseStatus.DRAFT.value:
                raise BusinessRuleError(f"Cannot delete a purchase with status {purchase.status}")

            # Delete purchase
            with self.transaction():
                # Delete all items first
                items = self.purchase_item_repository.get_by_purchase(purchase_id)
                for item in items:
                    self.purchase_item_repository.delete(item.id)

                # Then delete the purchase
                return self.purchase_repository.delete(purchase_id)
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting purchase {purchase_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for purchases by properties."""
        try:
            purchases = self.purchase_repository.search(query)
            return [PurchaseDTO.from_model(purchase, include_supplier=True).to_dict() for purchase in purchases]
        except Exception as e:
            self.logger.error(f"Error searching purchases with query '{query}': {str(e)}")
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get purchases by supplier ID."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            purchases = self.purchase_repository.get_by_supplier(supplier_id)
            return [PurchaseDTO.from_model(purchase).to_dict() for purchase in purchases]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving purchases for supplier {supplier_id}: {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get purchases by status."""
        try:
            # Validate status
            if not hasattr(PurchaseStatus, status):
                raise ValidationError(f"Invalid purchase status: {status}")

            purchases = self.purchase_repository.get_by_status(status)
            return [PurchaseDTO.from_model(purchase, include_supplier=True).to_dict() for purchase in purchases]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving purchases with status '{status}': {str(e)}")
            raise

    def add_item(self, purchase_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Validate item data
            self._validate_purchase_item_data(item_data)

            # Prevent modifying purchases that are not in draft status
            if purchase.status != PurchaseStatus.DRAFT.value:
                raise BusinessRuleError(f"Cannot add items to a purchase with status {purchase.status}")

            # Add purchase ID to item data
            item_data['purchase_id'] = purchase_id

            # Add item to purchase
            with self.transaction():
                item = self.purchase_item_repository.create(item_data)

                # Update purchase total
                self._update_purchase_total(purchase_id)

                return PurchaseItemDTO.from_model(item, include_item_details=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding item to purchase {purchase_id}: {str(e)}")
            raise

    def update_item(self, purchase_id: int, item_id: int, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item in a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Check if item exists
            item = self.purchase_item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Purchase item with ID {item_id} not found")

            # Ensure item belongs to the specified purchase
            if item.purchase_id != purchase_id:
                raise ValidationError(f"Item {item_id} does not belong to purchase {purchase_id}")

            # Validate item data
            self._validate_purchase_item_data(item_data, update=True)

            # Prevent modifying delivered purchases
            if purchase.status == PurchaseStatus.DELIVERED.value:
                # Allow updating quantity_received only
                allowed_fields = ['quantity_received', 'notes']
                if any(field in item_data for field in item_data if field not in allowed_fields):
                    raise BusinessRuleError(f"Can only update received quantity for delivered purchases")

            # Prevent modifying other purchase statuses except DRAFT
            elif purchase.status != PurchaseStatus.DRAFT.value:
                raise BusinessRuleError(f"Cannot update items for a purchase with status {purchase.status}")

            # Update item
            with self.transaction():
                updated_item = self.purchase_item_repository.update(item_id, item_data)

                # Recalculate total if price or quantity changed
                if 'price' in item_data or 'quantity' in item_data:
                    self._update_purchase_total(purchase_id)

                return PurchaseItemDTO.from_model(updated_item, include_item_details=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating item {item_id} in purchase {purchase_id}: {str(e)}")
            raise

    def remove_item(self, purchase_id: int, item_id: int) -> bool:
        """Remove an item from a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Check if item exists
            item = self.purchase_item_repository.get_by_id(item_id)
            if not item:
                raise NotFoundError(f"Purchase item with ID {item_id} not found")

            # Ensure item belongs to the specified purchase
            if item.purchase_id != purchase_id:
                raise ValidationError(f"Item {item_id} does not belong to purchase {purchase_id}")

            # Prevent modifying purchases that are not in draft status
            if purchase.status != PurchaseStatus.DRAFT.value:
                raise BusinessRuleError(f"Cannot remove items from a purchase with status {purchase.status}")

            # Remove item
            with self.transaction():
                result = self.purchase_item_repository.delete(item_id)

                # Update purchase total
                self._update_purchase_total(purchase_id)

                return result
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error removing item {item_id} from purchase {purchase_id}: {str(e)}")
            raise

    def get_items(self, purchase_id: int) -> List[Dict[str, Any]]:
        """Get all items in a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            items = self.purchase_item_repository.get_by_purchase(purchase_id)
            return [PurchaseItemDTO.from_model(item, include_item_details=True).to_dict() for item in items]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving items for purchase {purchase_id}: {str(e)}")
            raise

    def place_order(self, purchase_id: int) -> Dict[str, Any]:
        """Place an order for a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Check if purchase has items
            items = self.purchase_item_repository.get_by_purchase(purchase_id)
            if not items:
                raise ValidationError(f"Purchase {purchase_id} has no items")

            # Check if purchase is in draft status
            if purchase.status != PurchaseStatus.DRAFT.value:
                raise BusinessRuleError(f"Cannot place order for a purchase with status {purchase.status}")

            # Update purchase status to ordered
            with self.transaction():
                order_date = datetime.now()

                # Default expected delivery date to 14 days from now if not set
                expected_delivery_date = purchase.expected_delivery_date
                if not expected_delivery_date:
                    expected_delivery_date = order_date + timedelta(days=14)

                update_data = {
                    'status': PurchaseStatus.ORDERED.value,
                    'order_date': order_date,
                    'expected_delivery_date': expected_delivery_date
                }

                updated_purchase = self.purchase_repository.update(purchase_id, update_data)
                return PurchaseDTO.from_model(updated_purchase, include_supplier=True, include_items=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error placing order for purchase {purchase_id}: {str(e)}")
            raise

    def receive_order(self, purchase_id: int, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Receive an order for a purchase."""
        try:
            # Check if purchase exists
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Validate receipt data
            if 'items' not in receipt_data or not receipt_data['items']:
                raise ValidationError("Receipt data must include items")

            # Check if purchase is in an appropriate status
            valid_statuses = [PurchaseStatus.ORDERED.value, PurchaseStatus.PARTIALLY_RECEIVED.value]
            if purchase.status not in valid_statuses:
                raise BusinessRuleError(f"Cannot receive order for a purchase with status {purchase.status}")

            # Process receipt
            with self.transaction():
                delivery_date = receipt_data.get('delivery_date', datetime.now())

                # Process each item
                items = self.purchase_item_repository.get_by_purchase(purchase_id)
                item_map = {item.id: item for item in items}

                all_received = True
                for item_receipt in receipt_data['items']:
                    item_id = item_receipt.get('item_id')
                    quantity_received = item_receipt.get('quantity_received', 0)

                    if item_id not in item_map:
                        self.logger.warning(f"Item {item_id} not found in purchase {purchase_id}")
                        continue

                    item = item_map[item_id]
                    previous_received = getattr(item, 'quantity_received', 0) or 0
                    total_received = previous_received + quantity_received

                    # Update item received quantity
                    self.purchase_item_repository.update(item_id, {
                        'quantity_received': total_received,
                        'notes': item_receipt.get('notes', getattr(item, 'notes', None))
                    })

                    # Update inventory
                    if quantity_received > 0:
                        self._update_inventory_for_received_item(item, quantity_received)

                    # Check if all items are fully received
                    if total_received < item.quantity:
                        all_received = False

                # Update purchase status
                new_status = PurchaseStatus.DELIVERED.value if all_received else PurchaseStatus.PARTIALLY_RECEIVED.value

                self.purchase_repository.update(purchase_id, {
                    'status': new_status,
                    'delivery_date': delivery_date,
                    'notes': receipt_data.get('notes', purchase.notes)
                })

                # Get updated purchase
                updated_purchase = self.purchase_repository.get_by_id(purchase_id)
                return PurchaseDTO.from_model(updated_purchase, include_supplier=True, include_items=True).to_dict()
        except (NotFoundError, ValidationError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error receiving order for purchase {purchase_id}: {str(e)}")
            raise

    def get_purchase_history(self, start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get purchase history between dates."""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Default to last 90 days

            purchases = self.purchase_repository.get_by_date_range(start_date, end_date)
            return [PurchaseDTO.from_model(purchase, include_supplier=True).to_dict() for purchase in purchases]
        except Exception as e:
            self.logger.error(f"Error retrieving purchase history: {str(e)}")
            raise

    def generate_purchase_report(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate purchase report between dates."""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Default to last 90 days

            # Get purchases within date range
            purchases = self.purchase_repository.get_by_date_range(start_date, end_date)

            # Calculate totals
            total_spent = sum(purchase.total_amount for purchase in purchases if purchase.total_amount)
            total_orders = len(purchases)
            delivered_orders = sum(1 for p in purchases if p.status == PurchaseStatus.DELIVERED.value)
            pending_orders = sum(1 for p in purchases if p.status in [
                PurchaseStatus.ORDERED.value, PurchaseStatus.PARTIALLY_RECEIVED.value
            ])

            # Group by supplier
            supplier_summary = {}
            for purchase in purchases:
                supplier_id = purchase.supplier_id
                if supplier_id not in supplier_summary:
                    supplier = self.supplier_repository.get_by_id(supplier_id)
                    supplier_summary[supplier_id] = {
                        'supplier_id': supplier_id,
                        'supplier_name': supplier.name if supplier else f"Unknown Supplier ({supplier_id})",
                        'total_spent': 0,
                        'order_count': 0
                    }

                supplier_summary[supplier_id]['total_spent'] += purchase.total_amount or 0
                supplier_summary[supplier_id]['order_count'] += 1

            # Group by item type
            item_type_summary = {}
            for purchase in purchases:
                items = self.purchase_item_repository.get_by_purchase(purchase.id)
                for item in items:
                    item_type = item.item_type
                    if item_type not in item_type_summary:
                        item_type_summary[item_type] = {
                            'item_type': item_type,
                            'total_spent': 0,
                            'item_count': 0
                        }

                    item_cost = (item.price or 0) * item.quantity
                    item_type_summary[item_type]['total_spent'] += item_cost
                    item_type_summary[item_type]['item_count'] += 1

            return {
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_spent': total_spent,
                    'total_orders': total_orders,
                    'delivered_orders': delivered_orders,
                    'pending_orders': pending_orders,
                    'average_order_value': total_spent / total_orders if total_orders > 0 else 0
                },
                'supplier_summary': list(supplier_summary.values()),
                'item_type_summary': list(item_type_summary.values())
            }
        except Exception as e:
            self.logger.error(f"Error generating purchase report: {str(e)}")
            raise

    def auto_generate_for_low_stock(self) -> Dict[str, Any]:
        """Auto-generate purchase orders for low stock items."""
        try:
            # Get low stock items
            low_stock_materials = self.material_repository.get_low_stock()
            low_stock_tools = self.tool_repository.get_low_stock()

            if not (low_stock_materials or low_stock_tools):
                return {
                    'message': 'No low stock items found',
                    'purchases_created': 0
                }

            # Group items by supplier
            supplier_items = {}

            # Add materials
            for material in low_stock_materials:
                supplier_id = getattr(material, 'supplier_id', None)
                if not supplier_id:
                    continue

                if supplier_id not in supplier_items:
                    supplier_items[supplier_id] = {
                        'materials': [],
                        'tools': []
                    }

                # Calculate quantity to order
                inventory = self.inventory_repository.get_by_item('material', material.id)
                current_quantity = inventory.quantity if inventory else 0
                min_stock = getattr(material, 'min_stock_level', 1)
                max_stock = getattr(material, 'max_stock_level', min_stock * 3)
                order_quantity = max_stock - current_quantity

                if order_quantity <= 0:
                    continue

                supplier_items[supplier_id]['materials'].append({
                    'item_id': material.id,
                    'item_type': 'material',
                    'name': material.name,
                    'quantity': order_quantity,
                    'price': getattr(material, 'cost_price', None)
                })

            # Add tools
            for tool in low_stock_tools:
                supplier_id = getattr(tool, 'supplier_id', None)
                if not supplier_id:
                    continue

                if supplier_id not in supplier_items:
                    supplier_items[supplier_id] = {
                        'materials': [],
                        'tools': []
                    }

                # Calculate quantity to order
                inventory = self.inventory_repository.get_by_item('tool', tool.id)
                current_quantity = inventory.quantity if inventory else 0
                min_stock = getattr(tool, 'min_stock_level', 1)
                max_stock = getattr(tool, 'max_stock_level', min_stock * 2)
                order_quantity = max_stock - current_quantity

                if order_quantity <= 0:
                    continue

                supplier_items[supplier_id]['tools'].append({
                    'item_id': tool.id,
                    'item_type': 'tool',
                    'name': tool.name,
                    'quantity': order_quantity,
                    'price': getattr(tool, 'purchase_price', None)
                })

            # Create purchases for each supplier
            purchases_created = 0
            purchase_ids = []

            with self.transaction():
                for supplier_id, items in supplier_items.items():
                    all_items = items['materials'] + items['tools']
                    if not all_items:
                        continue

                    # Create purchase
                    purchase_data = {
                        'supplier_id': supplier_id,
                        'status': PurchaseStatus.DRAFT.value,
                        'notes': 'Auto-generated for low stock items'
                    }

                    purchase = self.purchase_repository.create(purchase_data)
                    purchases_created += 1
                    purchase_ids.append(purchase.id)

                    # Add items to purchase
                    for item in all_items:
                        item_data = {
                            'purchase_id': purchase.id,
                            'item_id': item['item_id'],
                            'item_type': item['item_type'],
                            'quantity': item['quantity'],
                            'price': item['price'],
                            'quantity_received': 0
                        }
                        self.purchase_item_repository.create(item_data)

                    # Update purchase total
                    self._update_purchase_total(purchase.id)

            return {
                'message': f'Created {purchases_created} purchase orders for low stock items',
                'purchases_created': purchases_created,
                'purchase_ids': purchase_ids
            }
        except Exception as e:
            self.logger.error(f"Error auto-generating purchases for low stock items: {str(e)}")
            raise

    def _update_purchase_total(self, purchase_id: int) -> None:
        """Update purchase total amount based on items and fees.

        Args:
            purchase_id: Purchase ID to update
        """
        try:
            # Get purchase
            purchase = self.purchase_repository.get_by_id(purchase_id)
            if not purchase:
                raise NotFoundError(f"Purchase with ID {purchase_id} not found")

            # Get items
            items = self.purchase_item_repository.get_by_purchase(purchase_id)

            # Calculate items total
            items_total = sum((item.price or 0) * item.quantity for item in items)

            # Add shipping and tax
            shipping_cost = getattr(purchase, 'shipping_cost', 0) or 0
            tax_amount = getattr(purchase, 'tax_amount', 0) or 0

            total_amount = items_total + shipping_cost + tax_amount

            # Update purchase
            self.purchase_repository.update(purchase_id, {'total_amount': total_amount})
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating purchase total for {purchase_id}: {str(e)}")
            raise

    def _update_inventory_for_received_item(self, item, quantity_received: float) -> None:
        """Update inventory for a received item.

        Args:
            item: Purchase item entity
            quantity_received: Quantity received
        """
        try:
            item_type = item.item_type
            item_id = item.item_id

            # Get or create inventory entry
            inventory = self.inventory_repository.get_by_item(item_type, item_id)

            if inventory:
                # Update existing inventory
                new_quantity = inventory.quantity + quantity_received
                status = InventoryStatus.IN_STOCK.value if new_quantity > 0 else InventoryStatus.OUT_OF_STOCK.value

                # Record transaction
                transaction_data = {
                    'inventory_id': inventory.id,
                    'transaction_type': TransactionType.RESTOCK.value,
                    'quantity': quantity_received,
                    'reason': f"Received from purchase {item.purchase_id}",
                    'performed_by': 'system'
                }
                self.inventory_repository.create_transaction(transaction_data)

                # Update inventory
                self.inventory_repository.update(inventory.id, {
                    'quantity': new_quantity,
                    'status': status
                })
            else:
                # Create new inventory entry
                inventory_data = {
                    'item_type': item_type,
                    'item_id': item_id,
                    'quantity': quantity_received,
                    'status': InventoryStatus.IN_STOCK.value if quantity_received > 0 else InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': ''
                }
                inventory = self.inventory_repository.create(inventory_data)

                # Record transaction
                transaction_data = {
                    'inventory_id': inventory.id,
                    'transaction_type': TransactionType.INITIAL_STOCK.value,
                    'quantity': quantity_received,
                    'reason': f"Initial stock from purchase {item.purchase_id}",
                    'performed_by': 'system'
                }
                self.inventory_repository.create_transaction(transaction_data)
        except Exception as e:
            self.logger.error(f"Error updating inventory for received item: {str(e)}")
            raise

    def _validate_purchase_data(self, purchase_data: Dict[str, Any], update: bool = False) -> None:
        """Validate purchase data.

        Args:
            purchase_data: Purchase data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check supplier_id if present
        if 'supplier_id' in purchase_data:
            supplier_id = purchase_data['supplier_id']
            if supplier_id:
                supplier = self.supplier_repository.get_by_id(supplier_id)
                if not supplier:
                    raise ValidationError(f"Supplier with ID {supplier_id} not found")
            elif not update:
                raise ValidationError("Supplier ID is required")
        elif not update:
            raise ValidationError("Supplier ID is required")

        # Validate status if provided
        if 'status' in purchase_data and purchase_data['status']:
            status = purchase_data['status']
            if not hasattr(PurchaseStatus, status):
                raise ValidationError(f"Invalid purchase status: {status}")

        # Validate dates if provided
        for date_field in ['order_date', 'expected_delivery_date', 'delivery_date']:
            if date_field in purchase_data and purchase_data[date_field]:
                date_value = purchase_data[date_field]
                if isinstance(date_value, str):
                    try:
                        datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValidationError(f"Invalid date format for {date_field}")

        # Validate numeric fields
        for numeric_field in ['shipping_cost', 'tax_amount', 'total_amount']:
            if numeric_field in purchase_data and purchase_data[numeric_field] is not None:
                value = purchase_data[numeric_field]
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValidationError(f"{numeric_field} must be a non-negative number")

    def _validate_purchase_item_data(self, item_data: Dict[str, Any], update: bool = False) -> None:
        """Validate purchase item data.

        Args:
            item_data: Purchase item data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new items
        if not update:
            required_fields = ['item_type', 'item_id', 'quantity']
            for field in required_fields:
                if field not in item_data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate item_type if provided
        if 'item_type' in item_data:
            item_type = item_data['item_type']
            if item_type not in ['material', 'tool']:
                raise ValidationError(f"Invalid item type: {item_type}")

        # Check item_id if provided based on item_type
        if 'item_id' in item_data and 'item_type' in item_data:
            item_id = item_data['item_id']
            item_type = item_data['item_type']

            if item_type == 'material':
                material = self.material_repository.get_by_id(item_id)
                if not material:
                    raise ValidationError(f"Material with ID {item_id} not found")
            elif item_type == 'tool':
                tool = self.tool_repository.get_by_id(item_id)
                if not tool:
                    raise ValidationError(f"Tool with ID {item_id} not found")

        # Validate quantity if provided
        if 'quantity' in item_data:
            quantity = item_data['quantity']
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                raise ValidationError("Quantity must be a positive number")

        # Validate price if provided
        if 'price' in item_data and item_data['price'] is not None:
            price = item_data['price']
            if not isinstance(price, (int, float)) or price < 0:
                raise ValidationError("Price cannot be negative")

        # Validate quantity_received if provided
        if 'quantity_received' in item_data:
            quantity_received = item_data['quantity_received']
            if not isinstance(quantity_received, (int, float)) or quantity_received < 0:
                raise ValidationError("Quantity received cannot be negative")

            # If both quantity and quantity_received are provided, make sure received doesn't exceed ordered
            if 'quantity' in item_data and 'quantity_received' in item_data:
                if item_data['quantity_received'] > item_data['quantity']:
                    raise ValidationError("Quantity received cannot exceed quantity ordered")