from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from database.repositories.tool_repository import ToolRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.tool_list_repository import ToolListRepository
from database.repositories.tool_maintenance_repository import ToolMaintenanceRepository

from database.models.enums import ToolCategory, InventoryStatus, TransactionType

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.tool_dto import ToolDTO

from di.core import inject


class ToolService(BaseService):
    """Implementation of the tool service interface."""

    @inject
    def __init__(self, session: Session,
                 tool_repository: Optional[ToolRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None,
                 tool_list_repository: Optional[ToolListRepository] = None,
                 tool_maintenance_repository: Optional[ToolMaintenanceRepository] = None):
        """Initialize the tool service."""
        super().__init__(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.tool_list_repository = tool_list_repository or ToolListRepository(session)
        self.tool_maintenance_repository = tool_maintenance_repository or ToolMaintenanceRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, tool_id: int) -> Dict[str, Any]:
        """Get tool by ID."""
        try:
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")
            return ToolDTO.from_model(tool, include_inventory=True, include_supplier=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool {tool_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all tools, optionally filtered."""
        try:
            tools = self.tool_repository.get_all(filters=filters)
            return [ToolDTO.from_model(tool).to_dict() for tool in tools]
        except Exception as e:
            self.logger.error(f"Error retrieving tools: {str(e)}")
            raise

    def create(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool."""
        try:
            # Validate tool data
            self._validate_tool_data(tool_data)

            # Check supplier if provided
            if 'supplier_id' in tool_data and tool_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(tool_data['supplier_id'])
                if not supplier:
                    raise ValidationError(f"Supplier with ID {tool_data['supplier_id']} not found")

            # Create tool
            with self.transaction():
                tool = self.tool_repository.create(tool_data)

                # Create inventory entry if not exists
                inventory_data = {
                    'item_type': 'tool',
                    'item_id': tool.id,
                    'quantity': tool_data.get('initial_quantity', 1),
                    'status': InventoryStatus.IN_STOCK.value,
                    'storage_location': tool_data.get('storage_location', '')
                }
                self.inventory_repository.create(inventory_data)

                return ToolDTO.from_model(tool, include_inventory=True, include_supplier=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating tool: {str(e)}")
            raise

    def update(self, tool_id: int, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate tool data
            self._validate_tool_data(tool_data, update=True)

            # Check supplier if provided
            if 'supplier_id' in tool_data and tool_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(tool_data['supplier_id'])
                if not supplier:
                    raise ValidationError(f"Supplier with ID {tool_data['supplier_id']} not found")

            # Update tool
            with self.transaction():
                updated_tool = self.tool_repository.update(tool_id, tool_data)
                return ToolDTO.from_model(updated_tool, include_inventory=True, include_supplier=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool {tool_id}: {str(e)}")
            raise

    def delete(self, tool_id: int) -> bool:
        """Delete a tool by ID."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Check if tool is being used in any tool lists
            tool_lists = self.tool_list_repository.get_by_tool(tool_id)
            if tool_lists:
                active_tool_lists = [tl for tl in tool_lists if tl.status in ['PENDING', 'IN_PROGRESS']]
                if active_tool_lists:
                    raise ValidationError(
                        f"Cannot delete tool with ID {tool_id} because it is being used in active tool lists")

            # Delete tool
            with self.transaction():
                # Delete inventory entry if exists
                inventory = self.inventory_repository.get_by_item('tool', tool_id)
                if inventory:
                    self.inventory_repository.delete(inventory.id)

                # Delete maintenance records if they exist
                if hasattr(self.tool_maintenance_repository, 'delete_by_tool'):
                    self.tool_maintenance_repository.delete_by_tool(tool_id)

                # Delete the tool
                return self.tool_repository.delete(tool_id)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting tool {tool_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for tools by name or other properties."""
        try:
            tools = self.tool_repository.search(query)
            return [ToolDTO.from_model(tool).to_dict() for tool in tools]
        except Exception as e:
            self.logger.error(f"Error searching tools with query '{query}': {str(e)}")
            raise

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get tools by category."""
        try:
            # Validate category
            if not hasattr(ToolCategory, category):
                raise ValidationError(f"Invalid tool category: {category}")

            tools = self.tool_repository.get_by_category(category)
            return [ToolDTO.from_model(tool).to_dict() for tool in tools]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tools with category '{category}': {str(e)}")
            raise

    def get_inventory_status(self, tool_id: int) -> Dict[str, Any]:
        """Get inventory status for a tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            inventory = self.inventory_repository.get_by_item('tool', tool_id)
            if not inventory:
                return {
                    'tool_id': tool_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': '',
                    'last_update': None
                }

            return {
                'tool_id': tool_id,
                'quantity': inventory.quantity,
                'status': inventory.status,
                'storage_location': inventory.storage_location,
                'last_update': inventory.updated_at
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving inventory status for tool {tool_id}: {str(e)}")
            raise

    def adjust_inventory(self, tool_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Get or create inventory entry
            inventory = self.inventory_repository.get_by_item('tool', tool_id)
            if not inventory:
                inventory_data = {
                    'item_type': 'tool',
                    'item_id': tool_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': ''
                }
                inventory = self.inventory_repository.create(inventory_data)

            # Validate quantity
            new_quantity = inventory.quantity + quantity
            if new_quantity < 0:
                raise ValidationError(f"Cannot adjust inventory to negative quantity: {new_quantity}")

            # Determine transaction type
            transaction_type = TransactionType.ADJUSTMENT.value
            if quantity > 0:
                transaction_type = TransactionType.RESTOCK.value
            elif quantity < 0:
                transaction_type = TransactionType.USAGE.value

            # Update inventory
            with self.transaction():
                # Create transaction record
                transaction_data = {
                    'inventory_id': inventory.id,
                    'transaction_type': transaction_type,
                    'quantity': abs(quantity),
                    'reason': reason,
                    'performed_by': 'system'  # This could be replaced with user info if available
                }
                self.inventory_repository.create_transaction(transaction_data)

                # Update inventory quantity and status
                update_data = {
                    'quantity': new_quantity,
                    'status': InventoryStatus.IN_STOCK.value if new_quantity > 0 else InventoryStatus.OUT_OF_STOCK.value
                }
                updated_inventory = self.inventory_repository.update(inventory.id, update_data)

                return {
                    'tool_id': tool_id,
                    'tool_name': tool.name,
                    'previous_quantity': inventory.quantity,
                    'adjustment': quantity,
                    'new_quantity': updated_inventory.quantity,
                    'status': updated_inventory.status,
                    'transaction_type': transaction_type,
                    'timestamp': datetime.now()
                }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adjusting inventory for tool {tool_id}: {str(e)}")
            raise

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get tools by supplier ID."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            tools = self.tool_repository.get_by_supplier(supplier_id)
            return [ToolDTO.from_model(tool).to_dict() for tool in tools]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tools for supplier {supplier_id}: {str(e)}")
            raise

    def record_maintenance(self, tool_id: int, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record maintenance for a tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate maintenance data
            required_fields = ['maintenance_date', 'maintenance_type', 'description']
            for field in required_fields:
                if field not in maintenance_data or not maintenance_data[field]:
                    raise ValidationError(f"Missing required field for maintenance: {field}")

            # Add tool_id to maintenance data
            maintenance_data['tool_id'] = tool_id

            # Create maintenance record
            with self.transaction():
                maintenance = self.tool_maintenance_repository.create(maintenance_data)

                # Update tool's last_maintenance date
                tool_update = {
                    'last_maintenance': maintenance_data['maintenance_date']
                }
                self.tool_repository.update(tool_id, tool_update)

                # Get updated tool
                updated_tool = self.tool_repository.get_by_id(tool_id)

                # Return the maintenance record and updated tool
                return {
                    'maintenance_id': maintenance.id,
                    'tool_id': tool_id,
                    'tool_name': tool.name,
                    'maintenance_date': maintenance.maintenance_date,
                    'maintenance_type': maintenance.maintenance_type,
                    'description': maintenance.description,
                    'performed_by': getattr(maintenance, 'performed_by', None),
                    'updated_tool': ToolDTO.from_model(updated_tool).to_dict()
                }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error recording maintenance for tool {tool_id}: {str(e)}")
            raise

    def get_maintenance_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get maintenance history for a tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            maintenance_records = self.tool_maintenance_repository.get_by_tool(tool_id)

            result = []
            for record in maintenance_records:
                result.append({
                    'maintenance_id': record.id,
                    'tool_id': tool_id,
                    'maintenance_date': record.maintenance_date,
                    'maintenance_type': record.maintenance_type,
                    'description': record.description,
                    'performed_by': getattr(record, 'performed_by', None),
                    'notes': getattr(record, 'notes', None),
                    'created_at': getattr(record, 'created_at', None)
                })

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving maintenance history for tool {tool_id}: {str(e)}")
            raise

    def get_tools_due_maintenance(self) -> List[Dict[str, Any]]:
        """Get tools that are due for maintenance."""
        try:
            # Get all tools with maintenance interval
            tools = self.tool_repository.get_tools_with_maintenance_interval()

            due_tools = []
            for tool in tools:
                last_maintenance = getattr(tool, 'last_maintenance', None)
                maintenance_interval = getattr(tool, 'maintenance_interval', None)

                # Skip tools without maintenance interval or that have never been maintained
                if not maintenance_interval:
                    continue

                is_due = False
                days_overdue = 0

                if not last_maintenance:
                    # Tool has never been maintained
                    purchase_date = getattr(tool, 'purchase_date', None)
                    if purchase_date and (datetime.now() - purchase_date).days > maintenance_interval:
                        is_due = True
                        days_overdue = (datetime.now() - purchase_date).days - maintenance_interval
                else:
                    # Check if maintenance is due based on last maintenance date
                    next_maintenance = last_maintenance + timedelta(days=maintenance_interval)
                    if next_maintenance < datetime.now():
                        is_due = True
                        days_overdue = (datetime.now() - next_maintenance).days

                if is_due:
                    due_tools.append({
                        'tool_id': tool.id,
                        'tool_name': tool.name,
                        'tool_category': tool.tool_category,
                        'last_maintenance': last_maintenance,
                        'maintenance_interval': maintenance_interval,
                        'days_overdue': days_overdue,
                        'next_maintenance': last_maintenance + timedelta(
                            days=maintenance_interval) if last_maintenance else None
                    })

            # Sort by days overdue, most overdue first
            return sorted(due_tools, key=lambda x: x['days_overdue'], reverse=True)
        except Exception as e:
            self.logger.error(f"Error retrieving tools due for maintenance: {str(e)}")
            raise

    def get_usage_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get usage history for a tool."""
        try:
            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Get tool list items for this tool
            tool_list_items = self.tool_list_repository.get_tool_list_items_by_tool(tool_id)

            result = []
            for item in tool_list_items:
                tool_list = getattr(item, 'tool_list', None)
                if not tool_list:
                    continue

                project = getattr(tool_list, 'project', None)

                usage_record = {
                    'tool_list_item_id': item.id,
                    'tool_list_id': tool_list.id,
                    'quantity': getattr(item, 'quantity', 1),
                    'created_at': getattr(tool_list, 'created_at', None),
                    'status': getattr(tool_list, 'status', None),
                    'project_id': getattr(project, 'id', None) if project else None,
                    'project_name': getattr(project, 'name', None) if project else None,
                    'project_type': getattr(project, 'project_type', None) if project else None,
                    'checked_out': getattr(item, 'checked_out', False),
                    'checked_out_date': getattr(item, 'checked_out_date', None),
                    'returned': getattr(item, 'returned', False),
                    'returned_date': getattr(item, 'returned_date', None)
                }

                result.append(usage_record)

            # Sort by date, most recent first
            return sorted(result, key=lambda x: x['created_at'] or datetime.min, reverse=True)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving usage history for tool {tool_id}: {str(e)}")
            raise

    def _validate_tool_data(self, tool_data: Dict[str, Any], update: bool = False) -> None:
        """Validate tool data.

        Args:
            tool_data: Tool data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new tools
        if not update:
            required_fields = ['name', 'tool_category']
            for field in required_fields:
                if field not in tool_data or not tool_data[field]:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate tool category if provided
        if 'tool_category' in tool_data and tool_data['tool_category']:
            tool_category = tool_data['tool_category']
            if not hasattr(ToolCategory, tool_category):
                raise ValidationError(f"Invalid tool category: {tool_category}")

        # Validate purchase date if provided
        if 'purchase_date' in tool_data and tool_data['purchase_date']:
            purchase_date = tool_data['purchase_date']
            if isinstance(purchase_date, str):
                try:
                    purchase_date = datetime.fromisoformat(purchase_date)
                except ValueError:
                    raise ValidationError("Invalid purchase date format")

            if purchase_date > datetime.now():
                raise ValidationError("Purchase date cannot be in the future")

        # Validate last maintenance date if provided
        if 'last_maintenance' in tool_data and tool_data['last_maintenance']:
            last_maintenance = tool_data['last_maintenance']
            if isinstance(last_maintenance, str):
                try:
                    last_maintenance = datetime.fromisoformat(last_maintenance)
                except ValueError:
                    raise ValidationError("Invalid last maintenance date format")

            if last_maintenance > datetime.now():
                raise ValidationError("Last maintenance date cannot be in the future")

        # Validate maintenance interval if provided
        if 'maintenance_interval' in tool_data:
            maintenance_interval = tool_data['maintenance_interval']
            if maintenance_interval is not None and maintenance_interval <= 0:
                raise ValidationError("Maintenance interval must be positive")

        # Validate purchase price if provided
        if 'purchase_price' in tool_data:
            purchase_price = tool_data['purchase_price']
            if purchase_price is not None and purchase_price < 0:
                raise ValidationError("Purchase price cannot be negative")