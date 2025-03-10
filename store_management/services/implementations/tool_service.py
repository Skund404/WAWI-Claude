# services/implementations/tool_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.tool import Tool
from database.models.enums import ToolCategory, InventoryStatus
from database.repositories.tool_repository import ToolRepository
from database.repositories.supplier_repository import SupplierRepository
from database.repositories.inventory_repository import InventoryRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.interfaces.tool_service import IToolService

from di.core import inject


class ToolService(BaseService, IToolService):
    """Implementation of the Tool Service interface.

    This service provides functionality for managing leatherworking tools,
    including inventory tracking, maintenance, and usage in projects.
    """

    @inject
    def __init__(self,
                 session: Session,
                 tool_repository: Optional[ToolRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the Tool Service.

        Args:
            session: SQLAlchemy database session
            tool_repository: Optional ToolRepository instance
            supplier_repository: Optional SupplierRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, tool_id: int) -> Dict[str, Any]:
        """Retrieve a tool by its ID.

        Args:
            tool_id: The ID of the tool to retrieve

        Returns:
            A dictionary representation of the tool

        Raises:
            NotFoundError: If the tool does not exist
        """
        try:
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")
            return self._to_dict(tool)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve tool: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all tools with optional filtering.

        Args:
            filters: Optional filters to apply to the tool query

        Returns:
            List of dictionaries representing tools
        """
        try:
            tools = self.tool_repository.get_all(filters)
            return [self._to_dict(tool) for tool in tools]
        except Exception as e:
            self.logger.error(f"Error retrieving tools: {str(e)}")
            raise ServiceError(f"Failed to retrieve tools: {str(e)}")

    def create(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tool.

        Args:
            tool_data: Dictionary containing tool data

        Returns:
            Dictionary representation of the created tool

        Raises:
            ValidationError: If the tool data is invalid
        """
        try:
            # Validate the tool data
            self._validate_tool_data(tool_data)

            # Check supplier if supplier_id is provided
            if 'supplier_id' in tool_data and tool_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(tool_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {tool_data['supplier_id']} not found")

            # Create the tool within a transaction
            with self.transaction():
                tool = Tool(**tool_data)
                created_tool = self.tool_repository.create(tool)

                # Create inventory entry for the tool if initial_quantity is provided
                if 'initial_quantity' in tool_data:
                    initial_quantity = tool_data.get('initial_quantity', 1)
                    inventory_data = {
                        'item_type': 'tool',
                        'item_id': created_tool.id,
                        'quantity': initial_quantity,
                        'status': InventoryStatus.IN_STOCK.value,
                        'storage_location': tool_data.get('storage_location', '')
                    }
                    self.inventory_repository.create(inventory_data)

                return self._to_dict(created_tool)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating tool: {str(e)}")
            raise ServiceError(f"Failed to create tool: {str(e)}")

    def update(self, tool_id: int, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing tool.

        Args:
            tool_id: ID of the tool to update
            tool_data: Dictionary containing updated tool data

        Returns:
            Dictionary representation of the updated tool

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate tool data
            self._validate_tool_data(tool_data, update=True)

            # Check supplier if supplier_id is provided
            if 'supplier_id' in tool_data and tool_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(tool_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {tool_data['supplier_id']} not found")

            # Update the tool within a transaction
            with self.transaction():
                updated_tool = self.tool_repository.update(tool_id, tool_data)
                return self._to_dict(updated_tool)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to update tool: {str(e)}")

    def delete(self, tool_id: int) -> bool:
        """Delete a tool by its ID.

        Args:
            tool_id: ID of the tool to delete

        Returns:
            True if the tool was successfully deleted

        Raises:
            NotFoundError: If the tool does not exist
            ServiceError: If the tool cannot be deleted (e.g., in use)
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Check if tool is currently checked out
            if hasattr(self, 'get_checked_out_tools'):
                checked_out = self.get_checked_out_tools(tool_id=tool_id)
                if checked_out and len(checked_out) > 0:
                    raise ServiceError(f"Cannot delete tool {tool_id} as it is currently checked out")

            # Delete the tool within a transaction
            with self.transaction():
                # Remove inventory entries
                inventory_entries = self.inventory_repository.get_by_item(item_type='tool', item_id=tool_id)
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Remove maintenance records if applicable
                if hasattr(self, 'maintenance_repository'):
                    maintenance_records = self.maintenance_repository.get_by_tool(tool_id)
                    for record in maintenance_records:
                        self.maintenance_repository.delete(record.id)

                # Then delete the tool
                self.tool_repository.delete(tool_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to delete tool: {str(e)}")

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find tools by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching tools
        """
        try:
            tools = self.tool_repository.find_by_name(name)
            return [self._to_dict(tool) for tool in tools]
        except Exception as e:
            self.logger.error(f"Error finding tools by name '{name}': {str(e)}")
            raise ServiceError(f"Failed to find tools by name: {str(e)}")

    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Find tools by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of dictionaries representing tools in the specified category
        """
        try:
            # Validate category
            self._validate_tool_category(category)

            tools = self.tool_repository.find_by_category(category)
            return [self._to_dict(tool) for tool in tools]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding tools by category '{category}': {str(e)}")
            raise ServiceError(f"Failed to find tools by category: {str(e)}")

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Find tools provided by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of dictionaries representing tools from the supplier

        Raises:
            NotFoundError: If the supplier does not exist
        """
        try:
            # Verify supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            tools = self.tool_repository.get_by_supplier(supplier_id)
            return [self._to_dict(tool) for tool in tools]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding tools by supplier {supplier_id}: {str(e)}")
            raise ServiceError(f"Failed to find tools by supplier: {str(e)}")

    def record_maintenance(self, tool_id: int,
                           maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record maintenance performed on a tool.

        Args:
            tool_id: ID of the tool
            maintenance_data: Dictionary containing maintenance information

        Returns:
            Dictionary representing the maintenance record

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the maintenance data is invalid
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate maintenance data
            self._validate_maintenance_data(maintenance_data)

            # Record maintenance within a transaction
            with self.transaction():
                # Add tool_id to maintenance data
                maintenance_data['tool_id'] = tool_id

                # Create maintenance record
                if hasattr(self, 'maintenance_repository'):
                    maintenance_record = self.maintenance_repository.create(maintenance_data)

                    # Update tool condition if provided
                    if 'new_condition' in maintenance_data:
                        self.tool_repository.update(tool_id, {'condition': maintenance_data['new_condition']})

                    return self._to_dict(maintenance_record)
                else:
                    # If maintenance repository is not available, store in tool notes
                    maintenance_note = f"Maintenance: {maintenance_data.get('maintenance_type', 'General')} - "
                    maintenance_note += f"Date: {maintenance_data.get('date', datetime.now().isoformat())} - "
                    maintenance_note += f"Description: {maintenance_data.get('description', 'N/A')}"

                    current_notes = getattr(tool, 'notes', '')
                    updated_notes = f"{current_notes}\n{maintenance_note}" if current_notes else maintenance_note

                    updated_tool = self.tool_repository.update(tool_id, {'notes': updated_notes})
                    return {
                        'tool_id': tool_id,
                        'maintenance_type': maintenance_data.get('maintenance_type', 'General'),
                        'date': maintenance_data.get('date', datetime.now().isoformat()),
                        'description': maintenance_data.get('description', 'N/A'),
                        'performed_by': maintenance_data.get('performed_by', None)
                    }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error recording maintenance for tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to record maintenance: {str(e)}")

    def get_maintenance_history(self, tool_id: int) -> List[Dict[str, Any]]:
        """Get the maintenance history for a tool.

        Args:
            tool_id: ID of the tool

        Returns:
            List of dictionaries containing maintenance records

        Raises:
            NotFoundError: If the tool does not exist
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Get maintenance history
            if hasattr(self, 'maintenance_repository'):
                maintenance_records = self.maintenance_repository.get_by_tool(tool_id)
                return [self._to_dict(record) for record in maintenance_records]
            else:
                # If maintenance repository is not available, parse from tool notes
                notes = getattr(tool, 'notes', '')
                if not notes:
                    return []

                # Simple parsing of maintenance notes (basic implementation)
                maintenance_entries = []
                for line in notes.split('\n'):
                    if line.startswith('Maintenance:'):
                        try:
                            # Parse the maintenance entry (basic implementation)
                            parts = line.split(' - ')
                            maint_type = parts[0].replace('Maintenance:', '').strip()
                            date_str = parts[1].replace('Date:', '').strip()
                            description = parts[2].replace('Description:', '').strip() if len(parts) > 2 else 'N/A'

                            maintenance_entries.append({
                                'tool_id': tool_id,
                                'maintenance_type': maint_type,
                                'date': date_str,
                                'description': description
                            })
                        except Exception:
                            # Skip entries that can't be parsed
                            continue

                return maintenance_entries
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting maintenance history for tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to get maintenance history: {str(e)}")

    def schedule_maintenance(self, tool_id: int,
                             scheduled_date: datetime,
                             maintenance_type: str,
                             notes: Optional[str] = None) -> Dict[str, Any]:
        """Schedule maintenance for a tool.

        Args:
            tool_id: ID of the tool
            scheduled_date: Date when maintenance is scheduled
            maintenance_type: Type of maintenance to perform
            notes: Optional notes about the scheduled maintenance

        Returns:
            Dictionary representing the scheduled maintenance

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the maintenance data is invalid
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate scheduled date
            if scheduled_date < datetime.now():
                raise ValidationError("Scheduled date cannot be in the past")

            # Schedule maintenance within a transaction
            with self.transaction():
                maintenance_data = {
                    'tool_id': tool_id,
                    'maintenance_type': maintenance_type,
                    'scheduled_date': scheduled_date,
                    'status': 'SCHEDULED',
                    'notes': notes
                }

                # Create scheduled maintenance record
                if hasattr(self, 'maintenance_repository'):
                    maintenance_record = self.maintenance_repository.create(maintenance_data)
                    return self._to_dict(maintenance_record)
                else:
                    # If maintenance repository is not available, store in tool notes
                    maintenance_note = f"Scheduled Maintenance: {maintenance_type} - "
                    maintenance_note += f"Date: {scheduled_date.isoformat()} - "
                    maintenance_note += f"Notes: {notes or 'N/A'}"

                    current_notes = getattr(tool, 'notes', '')
                    updated_notes = f"{current_notes}\n{maintenance_note}" if current_notes else maintenance_note

                    updated_tool = self.tool_repository.update(tool_id, {'notes': updated_notes})
                    return {
                        'tool_id': tool_id,
                        'maintenance_type': maintenance_type,
                        'scheduled_date': scheduled_date.isoformat(),
                        'status': 'SCHEDULED',
                        'notes': notes
                    }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance for tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to schedule maintenance: {str(e)}")

    def check_out_tool(self, tool_id: int,
                       project_id: Optional[int] = None,
                       user_id: Optional[int] = None,
                       quantity: int = 1,
                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Check out a tool for use.

        Args:
            tool_id: ID of the tool
            project_id: Optional ID of the project the tool is used for
            user_id: Optional ID of the user checking out the tool
            quantity: Quantity of tools to check out
            notes: Optional notes about the checkout

        Returns:
            Dictionary representing the checkout record

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the checkout data is invalid or insufficient tools available
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate quantity
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero")

            # Check availability
            inventory_entries = self.inventory_repository.get_by_item(item_type='tool', item_id=tool_id)

            if not inventory_entries:
                raise ValidationError(f"Tool {tool_id} has no inventory record")

            inventory = inventory_entries[0]
            available_quantity = inventory.quantity

            if available_quantity < quantity:
                raise ValidationError(
                    f"Insufficient quantity available (requested: {quantity}, available: {available_quantity})")

            # Create checkout record within a transaction
            with self.transaction():
                checkout_data = {
                    'tool_id': tool_id,
                    'project_id': project_id,
                    'user_id': user_id,
                    'checkout_date': datetime.now(),
                    'quantity': quantity,
                    'status': 'CHECKED_OUT',
                    'notes': notes
                }

                # Create checkout record
                if hasattr(self, 'checkout_repository'):
                    checkout_record = self.checkout_repository.create(checkout_data)

                    # Update inventory
                    inventory_data = {
                        'quantity': inventory.quantity - quantity
                    }

                    # Update status if all tools are checked out
                    if inventory.quantity - quantity == 0:
                        inventory_data['status'] = InventoryStatus.OUT_OF_STOCK.value

                    self.inventory_repository.update(inventory.id, inventory_data)

                    return self._to_dict(checkout_record)
                else:
                    # If checkout repository is not available, update inventory and tool notes
                    inventory_data = {
                        'quantity': inventory.quantity - quantity
                    }

                    # Update status if all tools are checked out
                    if inventory.quantity - quantity == 0:
                        inventory_data['status'] = InventoryStatus.OUT_OF_STOCK.value

                    self.inventory_repository.update(inventory.id, inventory_data)

                    # Update tool notes
                    checkout_note = f"Checkout: {quantity} units - "
                    checkout_note += f"Date: {datetime.now().isoformat()} - "
                    if project_id:
                        checkout_note += f"Project: {project_id} - "
                    if user_id:
                        checkout_note += f"User: {user_id} - "
                    checkout_note += f"Notes: {notes or 'N/A'}"

                    current_notes = getattr(tool, 'notes', '')
                    updated_notes = f"{current_notes}\n{checkout_note}" if current_notes else checkout_note

                    updated_tool = self.tool_repository.update(tool_id, {'notes': updated_notes})

                    return {
                        'id': f"checkout-{datetime.now().timestamp()}",  # Generate a pseudo-ID
                        'tool_id': tool_id,
                        'project_id': project_id,
                        'user_id': user_id,
                        'checkout_date': datetime.now().isoformat(),
                        'quantity': quantity,
                        'status': 'CHECKED_OUT',
                        'notes': notes
                    }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error checking out tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to check out tool: {str(e)}")

    def check_in_tool(self, tool_id: int,
                      checkout_id: int,
                      condition_notes: Optional[str] = None,
                      quantity: Optional[int] = None) -> Dict[str, Any]:
        """Check in a previously checked out tool.

        Args:
            tool_id: ID of the tool
            checkout_id: ID of the checkout record
            condition_notes: Optional notes about the condition of the tool
            quantity: Optional quantity to check in (defaults to all checked out)

        Returns:
            Dictionary representing the checkin record

        Raises:
            NotFoundError: If the tool or checkout record does not exist
            ValidationError: If the checkin data is invalid
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Get checkout record
            checkout_record = None
            if hasattr(self, 'checkout_repository'):
                checkout_record = self.checkout_repository.get_by_id(checkout_id)
                if not checkout_record:
                    raise NotFoundError(f"Checkout record with ID {checkout_id} not found")

                # Validate checkout record belongs to the tool
                if checkout_record.tool_id != tool_id:
                    raise ValidationError(f"Checkout record {checkout_id} does not belong to tool {tool_id}")

                # Set quantity to check in
                checked_out_quantity = checkout_record.quantity
                checkin_quantity = quantity if quantity is not None else checked_out_quantity

                # Validate quantity
                if checkin_quantity <= 0:
                    raise ValidationError("Quantity must be greater than zero")

                if checkin_quantity > checked_out_quantity:
                    raise ValidationError(
                        f"Cannot check in more than checked out (checking in: {checkin_quantity}, checked out: {checked_out_quantity})")
            else:
                # If no checkout repository, use the provided quantity
                if quantity is None:
                    raise ValidationError("Quantity must be provided when checking in tools")

                checkin_quantity = quantity

                # Validate quantity
                if checkin_quantity <= 0:
                    raise ValidationError("Quantity must be greater than zero")

            # Check in tool within a transaction
            with self.transaction():
                # Update inventory
                inventory_entries = self.inventory_repository.get_by_item(item_type='tool', item_id=tool_id)

                if not inventory_entries:
                    # If no inventory entry exists, create one
                    inventory_data = {
                        'item_type': 'tool',
                        'item_id': tool_id,
                        'quantity': checkin_quantity,
                        'status': InventoryStatus.IN_STOCK.value,
                    }
                    self.inventory_repository.create(inventory_data)
                else:
                    # Update existing inventory
                    inventory = inventory_entries[0]
                    current_quantity = inventory.quantity
                    new_quantity = current_quantity + checkin_quantity

                    inventory_data = {
                        'quantity': new_quantity,
                        'status': InventoryStatus.IN_STOCK.value
                    }

                    self.inventory_repository.update(inventory.id, inventory_data)

                # Update checkout record if available
                if hasattr(self, 'checkout_repository') and checkout_record:
                    # If checking in all tools, mark as RETURNED
                    if checkin_quantity == checked_out_quantity:
                        checkout_data = {
                            'status': 'RETURNED',
                            'return_date': datetime.now(),
                            'condition_notes': condition_notes
                        }
                    else:
                        # If checking in some tools, update quantity
                        checkout_data = {
                            'quantity': checked_out_quantity - checkin_quantity,
                            'condition_notes': condition_notes
                        }

                    updated_checkout = self.checkout_repository.update(checkout_id, checkout_data)
                    return self._to_dict(updated_checkout)
                else:
                    # If no checkout repository, update tool notes
                    checkin_note = f"Checkin: {checkin_quantity} units - "
                    checkin_note += f"Date: {datetime.now().isoformat()} - "
                    checkin_note += f"Condition: {condition_notes or 'Good'}"

                    current_notes = getattr(tool, 'notes', '')
                    updated_notes = f"{current_notes}\n{checkin_note}" if current_notes else checkin_note

                    updated_tool = self.tool_repository.update(tool_id, {'notes': updated_notes})

                    return {
                        'tool_id': tool_id,
                        'checkin_quantity': checkin_quantity,
                        'checkin_date': datetime.now().isoformat(),
                        'condition_notes': condition_notes
                    }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error checking in tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to check in tool: {str(e)}")

    def get_checked_out_tools(self,
                              project_id: Optional[int] = None,
                              user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get a list of currently checked out tools.

        Args:
            project_id: Optional ID of the project to filter by
            user_id: Optional ID of the user to filter by

        Returns:
            List of dictionaries representing checked out tools
        """
        try:
            # Get checked out tools
            if hasattr(self, 'checkout_repository'):
                filters = {'status': 'CHECKED_OUT'}

                if project_id:
                    filters['project_id'] = project_id

                if user_id:
                    filters['user_id'] = user_id

                checkouts = self.checkout_repository.get_all(filters)

                result = []
                for checkout in checkouts:
                    # Get tool details
                    tool = self.tool_repository.get_by_id(checkout.tool_id)

                    checkout_dict = self._to_dict(checkout)
                    checkout_dict['tool'] = self._to_dict(tool) if tool else {'id': checkout.tool_id}

                    result.append(checkout_dict)

                return result
            else:
                # If no checkout repository, unable to track checked out tools
                self.logger.warning("Checkout repository not available, cannot track checked out tools")
                return []
        except Exception as e:
            self.logger.error(f"Error getting checked out tools: {str(e)}")
            raise ServiceError(f"Failed to get checked out tools: {str(e)}")

    def update_tool_condition(self, tool_id: int,
                              condition: str,
                              notes: Optional[str] = None) -> Dict[str, Any]:
        """Update the condition of a tool.

        Args:
            tool_id: ID of the tool
            condition: New condition of the tool
            notes: Optional notes about the condition

        Returns:
            Dictionary representing the updated tool

        Raises:
            NotFoundError: If the tool does not exist
            ValidationError: If the condition is invalid
        """
        try:
            # Verify tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Validate condition
            valid_conditions = ['NEW', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'NEEDS_REPAIR', 'BROKEN']
            if condition not in valid_conditions:
                raise ValidationError(f"Invalid condition: {condition}. Valid conditions are: {valid_conditions}")

            # Update tool condition within a transaction
            with self.transaction():
                update_data = {
                    'condition': condition
                }

                # If notes provided, add to existing notes
                if notes:
                    current_notes = getattr(tool, 'notes', '')
                    condition_note = f"Condition Update: {condition} - Date: {datetime.now().isoformat()} - Notes: {notes}"
                    updated_notes = f"{current_notes}\n{condition_note}" if current_notes else condition_note
                    update_data['notes'] = updated_notes

                updated_tool = self.tool_repository.update(tool_id, update_data)
                return self._to_dict(updated_tool)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating condition for tool {tool_id}: {str(e)}")
            raise ServiceError(f"Failed to update tool condition: {str(e)}")

    def _validate_tool_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate tool data.

        Args:
            data: Tool data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for new tools
        if not update:
            required_fields = ['name']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate tool category if provided
        if 'tool_category' in data:
            self._validate_tool_category(data['tool_category'])

        # Validate initial_quantity if provided
        if 'initial_quantity' in data:
            try:
                quantity = int(data['initial_quantity'])
                if quantity < 0:
                    raise ValidationError("Initial quantity cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Initial quantity must be a valid integer")

    def _validate_tool_category(self, category: str) -> None:
        """Validate that the tool category is a valid enum value.

        Args:
            category: Tool category to validate

        Raises:
            ValidationError: If the category is invalid
        """
        try:
            # Check if the category is a valid enum value
            ToolCategory[category]
        except (KeyError, ValueError):
            valid_categories = [c.name for c in ToolCategory]
            raise ValidationError(f"Invalid tool category: {category}. Valid categories are: {valid_categories}")

    def _validate_maintenance_data(self, data: Dict[str, Any]) -> None:
        """Validate maintenance data.

        Args:
            data: Maintenance data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for maintenance
        required_fields = ['maintenance_type']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate date if provided
        if 'date' in data and isinstance(data['date'], str):
            try:
                datetime.fromisoformat(data['date'])
            except ValueError:
                raise ValidationError(f"Invalid date format: {data['date']}. Use ISO format.")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, Tool):
            result = {
                'id': obj.id,
                'name': obj.name,
                'description': getattr(obj, 'description', None),
                'tool_category': getattr(obj, 'tool_category', None),
                'condition': getattr(obj, 'condition', None),
                'supplier_id': getattr(obj, 'supplier_id', None),
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'updated_at': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            # Convert tool_category enum to string if it exists
            if hasattr(obj, 'tool_category') and hasattr(obj.tool_category, 'name'):
                result['tool_category'] = obj.tool_category.name

            return result
        elif hasattr(obj, '__dict__'):
            # Generic conversion for other model types
            result = {}
            for k, v in obj.__dict__.items():
                if not k.startswith('_'):
                    # Handle datetime objects
                    if isinstance(v, datetime):
                        result[k] = v.isoformat()
                    # Handle enum objects
                    elif hasattr(v, 'name'):
                        result[k] = v.name
                    else:
                        result[k] = v
            return result
        else:
            # If not a model object, return as is
            return obj