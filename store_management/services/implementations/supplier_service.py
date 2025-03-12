from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from database.repositories.supplier_repository import SupplierRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.tool_repository import ToolRepository
from database.repositories.purchase_repository import PurchaseRepository

from database.models.enums import SupplierStatus
from di import inject

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.supplier_dto import SupplierDTO
from services.dto.material_dto import MaterialDTO
from services.dto.tool_dto import ToolDTO




class SupplierService(BaseService):
    """Implementation of the supplier service interface."""

    @inject
    def __init__(self, session: Session,
                 supplier_repository: Optional[SupplierRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 tool_repository: Optional[ToolRepository] = None,
                 purchase_repository: Optional[PurchaseRepository] = None):
        """Initialize the supplier service."""
        super().__init__(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.tool_repository = tool_repository or ToolRepository(session)
        self.purchase_repository = purchase_repository or PurchaseRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier by ID."""
        try:
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")
            return SupplierDTO.from_model(supplier, include_counts=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving supplier {supplier_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all suppliers, optionally filtered."""
        try:
            suppliers = self.supplier_repository.get_all(filters=filters)
            return [SupplierDTO.from_model(supplier).to_dict() for supplier in suppliers]
        except Exception as e:
            self.logger.error(f"Error retrieving suppliers: {str(e)}")
            raise

    def create(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier."""
        try:
            # Validate supplier data
            self._validate_supplier_data(supplier_data)

            # Create supplier
            with self.transaction():
                supplier = self.supplier_repository.create(supplier_data)
                return SupplierDTO.from_model(supplier).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating supplier: {str(e)}")
            raise

    def update(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            # Validate supplier data
            self._validate_supplier_data(supplier_data, update=True)

            # Update supplier
            with self.transaction():
                updated_supplier = self.supplier_repository.update(supplier_id, supplier_data)
                return SupplierDTO.from_model(updated_supplier).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
            raise

    def delete(self, supplier_id: int) -> bool:
        """Delete a supplier by ID."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            # Check if supplier has associated materials or tools
            if hasattr(supplier, 'materials') and supplier.materials:
                raise ValidationError(
                    f"Cannot delete supplier with ID {supplier_id} because it has associated materials")

            if hasattr(supplier, 'tools') and supplier.tools:
                raise ValidationError(f"Cannot delete supplier with ID {supplier_id} because it has associated tools")

            # Delete supplier
            with self.transaction():
                return self.supplier_repository.delete(supplier_id)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting supplier {supplier_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for suppliers by name or other properties."""
        try:
            suppliers = self.supplier_repository.search(query)
            return [SupplierDTO.from_model(supplier).to_dict() for supplier in suppliers]
        except Exception as e:
            self.logger.error(f"Error searching suppliers with query '{query}': {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get suppliers by status."""
        try:
            # Validate status
            if not hasattr(SupplierStatus, status):
                raise ValidationError(f"Invalid supplier status: {status}")

            suppliers = self.supplier_repository.get_by_status(status)
            return [SupplierDTO.from_model(supplier).to_dict() for supplier in suppliers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving suppliers with status '{status}': {str(e)}")
            raise

    def get_materials_from_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all materials supplied by a specific supplier."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            materials = self.material_repository.get_by_supplier(supplier_id)
            return [MaterialDTO.from_model(material).to_dict() for material in materials]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving materials for supplier {supplier_id}: {str(e)}")
            raise

    def get_tools_from_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all tools supplied by a specific supplier."""
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

    def get_purchase_history(self, supplier_id: int,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get purchase history for a supplier."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            purchases = self.purchase_repository.get_by_supplier(
                supplier_id=supplier_id,
                start_date=start_date,
                end_date=end_date
            )
            return [purchase.to_dict() for purchase in purchases]  # Assuming Purchase has a to_dict method
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving purchase history for supplier {supplier_id}: {str(e)}")
            raise

    def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get performance metrics for a supplier."""
        try:
            # Check if supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            # Get purchases
            purchases = self.purchase_repository.get_by_supplier(supplier_id)

            # Calculate performance metrics
            total_purchases = len(purchases)
            total_amount = sum(p.total_amount for p in purchases)

            on_time_deliveries = sum(1 for p in purchases
                                     if p.status == 'DELIVERED' and p.delivery_date <= p.expected_delivery_date)
            on_time_rate = on_time_deliveries / total_purchases if total_purchases > 0 else 0

            delivery_times = [(p.delivery_date - p.order_date).days for p in purchases if p.delivery_date]
            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0

            # Last 6 months analysis
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_purchases = [p for p in purchases if p.order_date >= six_months_ago]
            recent_total = sum(p.total_amount for p in recent_purchases)

            return {
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'total_purchases': total_purchases,
                'total_spent': total_amount,
                'on_time_delivery_rate': on_time_rate,
                'average_delivery_time_days': avg_delivery_time,
                'last_6_months': {
                    'purchase_count': len(recent_purchases),
                    'total_amount': recent_total
                }
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving performance metrics for supplier {supplier_id}: {str(e)}")
            raise

    def _validate_supplier_data(self, supplier_data: Dict[str, Any], update: bool = False) -> None:
        """Validate supplier data.

        Args:
            supplier_data: Supplier data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['name']
        if not update:
            for field in required_fields:
                if field not in supplier_data or not supplier_data[field]:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate status if provided
        if 'status' in supplier_data:
            status = supplier_data['status']
            if not hasattr(SupplierStatus, status):
                raise ValidationError(f"Invalid supplier status: {status}")

        # Validate email format if provided
        if 'contact_email' in supplier_data and supplier_data['contact_email']:
            email = supplier_data['contact_email']
            if '@' not in email or '.' not in email:
                raise ValidationError(f"Invalid email format: {email}")