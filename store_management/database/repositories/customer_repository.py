# database/repositories/customer_repository.py
from database.models.customer import Customer
from database.models.enums import CustomerStatus, CustomerTier
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, select
from typing import Optional, List, Dict, Any
import logging


class CustomerRepository(BaseRepository):
    def __init__(self, session: Session):
        """
        Initialize the Customer Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Customer)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_by_status(self, status: CustomerStatus) -> List[Customer]:
        """
        Find customers by their status.

        Args:
            status (CustomerStatus): Customer status to filter by

        Returns:
            List of customers matching the status
        """
        try:
            return self.session.execute(select(Customer).filter(Customer.status == status)).scalars().all()
        except Exception as e:
            self.logger.error(f"Error finding customers by status: {e}")
            raise

    def find_by_tier(self, tier: CustomerTier) -> List[Customer]:
        """
        Find customers by their tier.

        Args:
            tier (CustomerTier): Customer tier to filter by

        Returns:
            List of customers matching the tier
        """
        try:
            return self.session.execute(select(Customer).filter(Customer.tier == tier)).scalars().all()
        except Exception as e:
            self.logger.error(f"Error finding customers by tier: {e}")
            raise

    def create_customer(self, customer_data: Dict[str, Any]) -> Customer:
        """
        Create a new customer.

        Args:
            customer_data (Dict[str, Any]): Data for creating a new customer

        Returns:
            Created Customer instance
        """
        try:
            customer = Customer(**customer_data)
            self.session.add(customer)
            self.session.commit()
            return customer
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating customer: {e}")
            raise

    def search_customers(self,
                         name: Optional[str] = None,
                         email: Optional[str] = None,
                         status: Optional[CustomerStatus] = None,
                         tier: Optional[CustomerTier] = None) -> List[Customer]:
        """
        Search customers with multiple optional filters.

        Args:
            name (Optional[str]): Partial name to search
            email (Optional[str]): Partial email to search
            status (Optional[CustomerStatus]): Customer status
            tier (Optional[CustomerTier]): Customer tier

        Returns:
            List of customers matching the search criteria
        """
        try:
            query = select(Customer)

            # Build filter conditions
            conditions = []
            if name:
                conditions.append(Customer.name.ilike(f"%{name}%"))
            if email:
                conditions.append(Customer.email.ilike(f"%{email}%"))
            if status:
                conditions.append(Customer.status == status)
            if tier:
                conditions.append(Customer.tier == tier)

            # Apply filters if any
            if conditions:
                query = query.filter(and_(*conditions))

            return query.all()
        except Exception as e:
            self.logger.error(f"Error searching customers: {e}")
            raise