# services/implementations/customer_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.customer_repository import CustomerRepository
from database.repositories.sales_repository import SalesRepository
from database.models.enums import CustomerStatus, CustomerTier, CustomerSource
from services.base_service import BaseService, ValidationError, NotFoundError


class CustomerService(BaseService):
    """Implementation of the customer service interface."""

    def __init__(self, session: Session, customer_repository: Optional[CustomerRepository] = None,
                 sales_repository: Optional[SalesRepository] = None):
        """Initialize the customer service.

        Args:
            session: SQLAlchemy database session
            customer_repository: Optional CustomerRepository instance
            sales_repository: Optional SalesRepository instance
        """
        super().__init__(session)
        self.customer_repository = customer_repository or CustomerRepository(session)
        self.sales_repository = sales_repository or SalesRepository(session)

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
            return self._to_dict(customer)
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
            return [self._to_dict(customer) for customer in customers]
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

            # Check if email is already in use
            if 'email' in customer_data:
                existing_customer = self.customer_repository.get_by_email(customer_data['email'])
                if existing_customer:
                    raise ValidationError(f"Email {customer_data['email']} is already in use")

            # Set default status if not provided
            if 'status' not in customer_data:
                customer_data['status'] = CustomerStatus.ACTIVE.value

            # Set default tier if not provided
            if 'tier' not in customer_data:
                customer_data['tier'] = CustomerTier.STANDARD.value

            # Create customer
            with self.transaction():
                customer = self.customer_repository.create(customer_data)
                return self._to_dict(customer)
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

            # Check if email is already in use by another customer
            if 'email' in customer_data and customer_data['email'] != customer.email:
                existing_customer = self.customer_repository.get_by_email(customer_data['email'])
                if existing_customer and existing_customer.id != customer_id:
                    raise ValidationError(f"Email {customer_data['email']} is already in use")

            # Update customer
            with self.transaction():
                updated_customer = self.customer_repository.update(customer_id, customer_data)
                return self._to_dict(updated_customer)
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
            ValidationError: If customer has associated sales
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Check if customer has sales
            sales = self.sales_repository.get_by_customer(customer_id)
            if sales:
                raise ValidationError(f"Cannot delete customer {customer_id} as they have associated sales")

            # Delete customer
            with self.transaction():
                self.customer_repository.delete(customer_id)
                return True
        except Exception as e:
            self.logger.error(f"Error deleting customer {customer_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for customers by name or email.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching customers
        """
        try:
            customers = self.customer_repository.search(query)
            return [self._to_dict(customer) for customer in customers]
        except Exception as e:
            self.logger.error(f"Error searching customers: {str(e)}")
            raise

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email address.

        Args:
            email: Email address

        Returns:
            Dict representing the customer, or None if not found
        """
        try:
            customer = self.customer_repository.get_by_email(email)
            if not customer:
                return None
            return self._to_dict(customer)
        except Exception as e:
            self.logger.error(f"Error retrieving customer by email {email}: {str(e)}")
            raise

    def get_sales_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales history for a customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of dicts representing sales for the customer

        Raises:
            NotFoundError: If customer not found
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Get sales for customer
            sales = self.sales_repository.get_by_customer(customer_id)
            return [self._to_dict(sale) for sale in sales]
        except Exception as e:
            self.logger.error(f"Error retrieving sales history for customer {customer_id}: {str(e)}")
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
            ValidationError: If invalid status
        """
        try:
            # Check if customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Validate status
            try:
                CustomerStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid customer status: {status}")

            # Update customer status
            with self.transaction():
                updated_customer = self.customer_repository.update(customer_id, {'status': status})
                return self._to_dict(updated_customer)
        except Exception as e:
            self.logger.error(f"Error updating status for customer {customer_id}: {str(e)}")
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
        # Only check required fields for new customers
        if not update:
            required_fields = ['name', 'email']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate email format if provided
        if 'email' in data:
            email = data['email']
            if not self._is_valid_email(email):
                raise ValidationError(f"Invalid email format: {email}")

        # Validate status if provided
        if 'status' in data:
            try:
                CustomerStatus(data['status'])
            except ValueError:
                raise ValidationError(f"Invalid customer status: {data['status']}")

        # Validate tier if provided
        if 'tier' in data:
            try:
                CustomerTier(data['tier'])
            except ValueError:
                raise ValidationError(f"Invalid customer tier: {data['tier']}")

        # Validate source if provided
        if 'source' in data:
            try:
                CustomerSource(data['source'])
            except ValueError:
                raise ValidationError(f"Invalid customer source: {data['source']}")

    def _is_valid_email(self, email: str) -> bool:
        """Check if an email address is valid.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        # Very basic email validation
        import re
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        return bool(email_pattern.match(email))