# services/implementations/customer_service.py
"""
Implementation of the customer service interface for managing customer operations.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast
import datetime

from database.models.customer import Customer
from database.repositories.customer_repository import CustomerRepository
from database.sqlalchemy.session import get_db_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from services.base_service import BaseService, NotFoundError, ServiceError, ValidationError
from services.interfaces.customer_service import ICustomerService, CustomerStatus, CustomerTier, CustomerSource
from utils.logger import log_debug, log_error, log_info
from utils.validators import validate_string, validate_email


class CustomerService(BaseService, ICustomerService):
    """
    Implementation of the customer service interface for managing customer operations.
    Provides business logic for creating, retrieving, updating, and deleting customer records.
    """

    def __init__(self, session: Optional[Session] = None,
                 customer_repository: Optional[CustomerRepository] = None):
        """
        Initialize the Customer Service with repository and database session.

        Args:
            session: SQLAlchemy database session
            customer_repository: Repository for customer data access
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.session = session or get_db_session()
        self.customer_repository = customer_repository or CustomerRepository(self.session)

    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer record.

        Args:
            customer_data: Dictionary containing customer information

        Returns:
            Dictionary representing the created customer

        Raises:
            ValidationError: If customer data is invalid
            ServiceError: If an error occurs during creation
        """
        try:
            # Validate required fields
            if 'name' not in customer_data or not customer_data['name']:
                raise ValidationError("Customer name is required")

            if 'email' in customer_data and customer_data['email']:
                validate_email(customer_data['email'])

            # Create customer record
            customer = self.customer_repository.create(customer_data)
            self.session.commit()

            log_info(f"Created new customer: {customer.id} - {customer.name}")
            return self._serialize_customer(customer)

        except ValidationError as e:
            log_error(f"Validation error creating customer: {str(e)}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error creating customer: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Failed to create customer: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error creating customer: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Unexpected error creating customer: {str(e)}")

    def get_customer(self, customer_id: Union[str, int]) -> Dict[str, Any]:
        """
        Retrieve a customer by ID.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            Dictionary with customer information

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during retrieval
        """
        try:
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            return self._serialize_customer(customer)

        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error retrieving customer {customer_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve customer: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error retrieving customer {customer_id}: {str(e)}")
            raise ServiceError(f"Unexpected error retrieving customer: {str(e)}")

    def update_customer(self, customer_id: Union[str, int], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing customer record.

        Args:
            customer_id: Unique identifier for the customer
            customer_data: Dictionary containing updated customer information

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If updated data is invalid
            ServiceError: If an error occurs during update
        """
        try:
            # Verify customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Validate email if provided
            if 'email' in customer_data and customer_data['email']:
                validate_email(customer_data['email'])

            # Update customer
            updated_customer = self.customer_repository.update(customer_id, customer_data)
            self.session.commit()

            log_info(f"Updated customer: {customer_id}")
            return self._serialize_customer(updated_customer)

        except NotFoundError:
            raise
        except ValidationError as e:
            log_error(f"Validation error updating customer {customer_id}: {str(e)}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error updating customer {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Failed to update customer: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error updating customer {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Unexpected error updating customer: {str(e)}")

    def delete_customer(self, customer_id: Union[str, int]) -> bool:
        """
        Delete a customer record.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            True if deletion was successful

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during deletion
        """
        try:
            # Verify customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Check if customer has associated sales
            if customer.sales and len(customer.sales) > 0:
                # Instead of deleting, mark as archived
                log_info(f"Customer {customer_id} has sales records. Marking as archived instead of deleting.")
                self.update_customer_status(customer_id, CustomerStatus.ARCHIVED)
                return True

            # Delete the customer
            result = self.customer_repository.delete(customer_id)
            self.session.commit()

            log_info(f"Deleted customer: {customer_id}")
            return result

        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error deleting customer {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Failed to delete customer: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error deleting customer {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Unexpected error deleting customer: {str(e)}")

    def list_customers(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of customers with optional filtering.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            List of dictionaries representing customers

        Raises:
            ServiceError: If an error occurs during retrieval
        """
        try:
            filters = filters or {}
            customers = self.customer_repository.get_all(filters)
            return [self._serialize_customer(customer) for customer in customers]

        except SQLAlchemyError as e:
            log_error(f"Database error listing customers: {str(e)}")
            raise ServiceError(f"Failed to list customers: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error listing customers: {str(e)}")
            raise ServiceError(f"Unexpected error listing customers: {str(e)}")

    def get_customer_sales_history(self, customer_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve the sales history for a customer.

        Args:
            customer_id: Unique identifier for the customer

        Returns:
            List of dictionaries representing sales

        Raises:
            NotFoundError: If customer does not exist
            ServiceError: If an error occurs during retrieval
        """
        try:
            # Verify customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Load sales with eager loading of items
            sales = []
            for sale in customer.sales:
                sale_dict = {
                    "id": sale.id,
                    "created_at": sale.created_at,
                    "total_amount": sale.total_amount,
                    "status": sale.status.value if hasattr(sale.status, 'value') else sale.status,
                    "payment_status": sale.payment_status.value if hasattr(sale.payment_status,
                                                                           'value') else sale.payment_status,
                    "items": []
                }

                # Add sales items if available
                if hasattr(sale, 'items') and sale.items:
                    for item in sale.items:
                        item_dict = {
                            "id": item.id,
                            "quantity": item.quantity,
                            "price": item.price,
                            "product_id": item.product_id,
                            "product_name": item.product.name if hasattr(item,
                                                                         'product') and item.product else "Unknown"
                        }
                        sale_dict["items"].append(item_dict)

                sales.append(sale_dict)

            return sales

        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error retrieving sales for customer {customer_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve customer sales history: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error retrieving sales for customer {customer_id}: {str(e)}")
            raise ServiceError(f"Unexpected error retrieving customer sales history: {str(e)}")

    def update_customer_status(self, customer_id: Union[str, int], status: CustomerStatus) -> Dict[str, Any]:
        """
        Update the status of a customer.

        Args:
            customer_id: Unique identifier for the customer
            status: New customer status

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If status is invalid
            ServiceError: If an error occurs during update
        """
        try:
            # Verify customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Update status
            customer.status = status
            self.session.commit()

            log_info(f"Updated status for customer {customer_id} to {status.value}")
            return self._serialize_customer(customer)

        except NotFoundError:
            raise
        except ValidationError as e:
            log_error(f"Validation error updating customer status {customer_id}: {str(e)}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error updating customer status {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Failed to update customer status: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error updating customer status {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Unexpected error updating customer status: {str(e)}")

    def update_customer_tier(self, customer_id: Union[str, int], tier: CustomerTier) -> Dict[str, Any]:
        """
        Update the tier/level of a customer.

        Args:
            customer_id: Unique identifier for the customer
            tier: New customer tier

        Returns:
            Dictionary representing the updated customer

        Raises:
            NotFoundError: If customer does not exist
            ValidationError: If tier is invalid
            ServiceError: If an error occurs during update
        """
        try:
            # Verify customer exists
            customer = self.customer_repository.get_by_id(customer_id)
            if not customer:
                raise NotFoundError(f"Customer with ID {customer_id} not found")

            # Update tier
            customer.tier = tier
            self.session.commit()

            log_info(f"Updated tier for customer {customer_id} to {tier.value}")
            return self._serialize_customer(customer)

        except NotFoundError:
            raise
        except ValidationError as e:
            log_error(f"Validation error updating customer tier {customer_id}: {str(e)}")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            log_error(f"Database error updating customer tier {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Failed to update customer tier: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error updating customer tier {customer_id}: {str(e)}")
            self.session.rollback()
            raise ServiceError(f"Unexpected error updating customer tier: {str(e)}")

    def search_customers(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for customers by name, email, or other attributes.

        Args:
            query: Search query string

        Returns:
            List of dictionaries representing matching customers

        Raises:
            ServiceError: If an error occurs during search
        """
        try:
            # Prepare search query
            search_term = f"%{query}%"

            # Search in repository
            customers = self.session.query(Customer).filter(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.notes.ilike(search_term)
                )
            ).all()

            return [self._serialize_customer(customer) for customer in customers]

        except SQLAlchemyError as e:
            log_error(f"Database error searching customers: {str(e)}")
            raise ServiceError(f"Failed to search customers: {str(e)}")
        except Exception as e:
            log_error(f"Unexpected error searching customers: {str(e)}")
            raise ServiceError(f"Unexpected error searching customers: {str(e)}")

    def _serialize_customer(self, customer: Customer) -> Dict[str, Any]:
        """
        Serialize a customer model instance to a dictionary.

        Args:
            customer: Customer model instance

        Returns:
            Dictionary representation of the customer
        """
        result = {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone if hasattr(customer, 'phone') else None,
            "status": customer.status.value if hasattr(customer.status, 'value') else customer.status,
            "tier": customer.tier.value if hasattr(customer, 'tier') and hasattr(customer.tier, 'value') else None,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
            "source": customer.source.value if hasattr(customer, 'source') and hasattr(customer.source,
                                                                                       'value') else None,
            "notes": customer.notes if hasattr(customer, 'notes') else None,
        }

        # Add additional serializable fields as needed
        if hasattr(customer, 'address') and customer.address:
            result["address"] = customer.address

        if hasattr(customer, 'sales_count'):
            result["sales_count"] = customer.sales_count
        else:
            result["sales_count"] = len(customer.sales) if hasattr(customer, 'sales') else 0

        return result