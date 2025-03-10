# services/implementations/customer_service.py
# Implementation of the customer service interface

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.customer_repository import CustomerRepository
from database.repositories.sales_repository import SalesRepository
from database.repositories.project_repository import ProjectRepository
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource
from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.customer_dto import CustomerDTO
from services.dto.sales_dto import SalesDTO
from services.dto.project_dto import ProjectDTO

from di.inject import inject


class CustomerService(BaseService):
    """Implementation of the customer service interface."""

    @inject
    def __init__(self, session: Session,
                 customer_repository: Optional[CustomerRepository] = None,
                 sales_repository: Optional[SalesRepository] = None,
                 project_repository: Optional[ProjectRepository] = None):
        """Initialize the customer service.

        Args:
            session: SQLAlchemy database session
            customer_repository: Optional CustomerRepository instance
            sales_repository: Optional SalesRepository instance
            project_repository: Optional ProjectRepository instance
        """
        super().__init__(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, customer_id: int) -> Dict[str, Any]:
        """Get customer by ID.

        Args:
            customer_id: ID of the customer to retrieve

        Returns:
            Dict representing the customer

        Raises:
            NotFoundError: If customer not found
        """
        try:
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")
            return CustomerDTO.from_model(customer).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all customers, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing customers
        """
        try:
            customers = self.customer_repository.get_all(filters)
            return [CustomerDTO.from_model(customer).to_dict() for customer in customers]
        except Exception as e:
            self.logger.error(f"Error retrieving customers: {str(e)}")
            raise

    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer.

        Args:
            customer_data: Dict containing customer properties

        Returns:
            Dict representing the created customer

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate customer data
            self._validate_customer_data(customer_data)

            # Set default status if not provided
            if 'status' not in customer_data:
                customer_data['status'] = CustomerStatus.ACTIVE.value

            # Create customer
            with self.transaction():
                customer = self.customer_repository.create(customer_data)
                return CustomerDTO.from_model(customer).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating customer: {str(e)}")
            raise

    def update(self, customer_id: int, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer.

        Args:
            customer_id: ID of the customer to update
            customer_data: Dict containing updated customer properties

        Returns:
            Dict representing the updated customer

        Raises:
            NotFoundError: If customer not found
            ValidationError: If validation fails
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Validate customer data
            self._validate_customer_data(customer_data, update=True)

            # Update customer
            with self.transaction():
                updated_customer = self.customer_repository.update(customer_id, customer_data)
                return CustomerDTO.from_model(updated_customer).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating customer {customer_id}: {str(e)}")
            raise

    def delete(self, customer_id: int) -> bool:
        """Delete a customer by ID.

        Args:
            customer_id: ID of the customer to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If customer not found
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Check if customer has active sales or projects
            sales = self.sales_repository.get_by_customer(customer_id)
            if sales:
                raise ValidationError(f"Cannot delete customer {customer_id} as they have sales records")

            projects = self.project_repository.get_by_customer(customer_id)
            if projects:
                raise ValidationError(f"Cannot delete customer {customer_id} as they have project records")

            # Delete customer
            with self.transaction():
                self.customer_repository.delete(customer_id)
                return True
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting customer {customer_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for customers by name, email, or other properties.

        Args:
            query: Search query string

        Returns:
            List of customers matching the search query
        """
        try:
            customers = self.customer_repository.search(query)
            return [CustomerDTO.from_model(customer).to_dict() for customer in customers]
        except Exception as e:
            self.logger.error(f"Error searching customers with query '{query}': {str(e)}")
            raise

    def get_sales_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales history for a customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of sales for the customer

        Raises:
            NotFoundError: If customer not found
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Get sales
            sales = self.sales_repository.get_by_customer(customer_id)
            return [SalesDTO.from_model(sale).to_dict() for sale in sales]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving sales history for customer {customer_id}: {str(e)}")
            raise

    def get_project_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get project history for a customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of projects for the customer

        Raises:
            NotFoundError: If customer not found
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Get projects
            projects = self.project_repository.get_by_customer(customer_id)
            return [ProjectDTO.from_model(project).to_dict() for project in projects]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving project history for customer {customer_id}: {str(e)}")
            raise

    def update_status(self, customer_id: int, status: str) -> Dict[str, Any]:
        """Update customer status.

        Args:
            customer_id: ID of the customer
            status: New status

        Returns:
            Dict representing the updated customer

        Raises:
            NotFoundError: If customer not found
            ValidationError: If validation fails
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Validate status
            self._validate_enum_value(CustomerStatus, status, "customer status")

            # Update customer status
            with self.transaction():
                updated_customer = self.customer_repository.update(customer_id, {'status': status})
                return CustomerDTO.from_model(updated_customer).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating status for customer {customer_id}: {str(e)}")
            raise

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get customers by status.

        Args:
            status: Status to filter by

        Returns:
            List of customers with the specified status
        """
        try:
            # Validate status
            self._validate_enum_value(CustomerStatus, status, "customer status")

            # Get customers by status
            customers = self.customer_repository.get_by_status(status)
            return [CustomerDTO.from_model(customer).to_dict() for customer in customers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving customers by status {status}: {str(e)}")
            raise

    def get_by_tier(self, tier: str) -> List[Dict[str, Any]]:
        """Get customers by tier.

        Args:
            tier: Tier to filter by

        Returns:
            List of customers with the specified tier
        """
        try:
            # Validate tier
            self._validate_enum_value(CustomerTier, tier, "customer tier")

            # Get customers by tier
            customers = self.customer_repository.get_by_tier(tier)
            return [CustomerDTO.from_model(customer).to_dict() for customer in customers]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving customers by tier {tier}: {str(e)}")
            raise

    # Helper methods

    def _validate_customer_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate customer data.

        Args:
            data: Customer data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['name', 'email']
        self._validate_required_fields(data, required_fields, update)

        # Validate email format (simple validation)
        if 'email' in data and '@' not in data['email']:
            raise ValidationError(f"Invalid email format: {data['email']}")

        # Validate status
        if 'status' in data:
            self._validate_enum_value(CustomerStatus, data['status'], "customer status")

        # Validate tier
        if 'tier' in data:
            self._validate_enum_value(CustomerTier, data['tier'], "customer tier")

        # Validate source
        if 'source' in data:
            self._validate_enum_value(CustomerSource, data['source'], "customer source")