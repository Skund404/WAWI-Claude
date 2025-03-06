# database/repositories/transaction_repository.py
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Type, TypeVar, Union

from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.models.transaction import (
    BaseTransaction,
    MaterialTransaction,
    LeatherTransaction,
    HardwareTransaction
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseTransaction)


class TransactionRepository:
    """
    Repository for handling database operations related to transactions.
    """

    def __init__(self, session: Session):
        """
        Initialize the transaction repository with a database session.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def add(self, transaction: T) -> T:
        """
        Add a new transaction to the database.

        Args:
            transaction: Transaction object to add

        Returns:
            Added transaction with ID assigned
        """
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def get_transactions(
            self,
            model_class: Type[T],
            **filters
    ) -> List[T]:
        """
        Generic method to get transactions by type with filters.

        Args:
            model_class: Transaction model class to query
            **filters: Additional filters to apply

        Returns:
            List of transactions matching the filters
        """
        query = self.session.query(model_class)

        # Apply filters
        if "material_id" in filters:
            query = query.filter(model_class.material_id == filters["material_id"])

        if "leather_id" in filters:
            query = query.filter(model_class.leather_id == filters["leather_id"])

        if "hardware_id" in filters:
            query = query.filter(model_class.hardware_id == filters["hardware_id"])

        if "transaction_type" in filters:
            query = query.filter(model_class.transaction_type == filters["transaction_type"])

        # Date range filters
        date_filters = []

        if "start_date" in filters:
            date_filters.append(model_class.transaction_date >= filters["start_date"])

        if "end_date" in filters:
            date_filters.append(model_class.transaction_date <= filters["end_date"])

        if date_filters:
            query = query.filter(and_(*date_filters))

        # Sort by transaction date, most recent first
        query = query.order_by(model_class.transaction_date.desc())

        return query.all()

    def get_material_transactions(self, **filters) -> List[MaterialTransaction]:
        """
        Get material transactions with optional filters.

        Args:
            **filters: Filters to apply

        Returns:
            List of material transactions matching the filters
        """
        return self.get_transactions(MaterialTransaction, **filters)

    def get_leather_transactions(self, **filters) -> List[LeatherTransaction]:
        """
        Get leather transactions with optional filters.

        Args:
            **filters: Filters to apply

        Returns:
            List of leather transactions matching the filters
        """
        return self.get_transactions(LeatherTransaction, **filters)

    def get_hardware_transactions(self, **filters) -> List[HardwareTransaction]:
        """
        Get hardware transactions with optional filters.

        Args:
            **filters: Filters to apply

        Returns:
            List of hardware transactions matching the filters
        """
        return self.get_transactions(HardwareTransaction, **filters)

    def get_transaction_by_id(self, transaction_id: int, model_class: Type[T]) -> Optional[T]:
        """
        Get a transaction by its ID and type.

        Args:
            transaction_id: ID of the transaction to retrieve
            model_class: Transaction model class to query

        Returns:
            Transaction if found, None otherwise
        """
        return self.session.query(model_class).filter(model_class.id == transaction_id).first()

    def update_transaction(self, transaction_id: int, model_class: Type[T], update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update a transaction by ID.

        Args:
            transaction_id: ID of the transaction to update
            model_class: Transaction model class to query
            update_data: Dictionary of fields to update

        Returns:
            Updated transaction if found, None otherwise
        """
        transaction = self.get_transaction_by_id(transaction_id, model_class)
        if transaction:
            for key, value in update_data.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)

            self.session.commit()
            self.session.refresh(transaction)

        return transaction

    def delete_transaction(self, transaction_id: int, model_class: Type[T]) -> bool:
        """
        Delete a transaction by ID.

        Args:
            transaction_id: ID of the transaction to delete
            model_class: Transaction model class to query

        Returns:
            True if the transaction was deleted, False otherwise
        """
        transaction = self.get_transaction_by_id(transaction_id, model_class)
        if transaction:
            self.session.delete(transaction)
            self.session.commit()
            return True

        return False