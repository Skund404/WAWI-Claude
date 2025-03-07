# services/interfaces/transaction_service.py
"""
Interface for Transaction Services in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from database.models.enums import TransactionType
from database.models.transaction import Transaction, MaterialTransaction, LeatherTransaction, HardwareTransaction


class ITransactionService(ABC):
    """
    Abstract base class defining the core interface for Transaction Services.
    Handles generic transaction operations.
    """

    @abstractmethod
    def create_transaction(
        self,
        transaction_type: TransactionType,
        amount: float,
        description: Optional[str] = None,
        **kwargs
    ) -> Transaction:
        """
        Create a generic transaction.

        Args:
            transaction_type (TransactionType): Type of transaction
            amount (float): Transaction amount
            description (Optional[str]): Transaction description
            **kwargs: Additional transaction attributes

        Returns:
            Transaction: The created transaction
        """
        pass

    @abstractmethod
    def get_transaction_by_id(self, transaction_id: int) -> Transaction:
        """
        Retrieve a transaction by its ID.

        Args:
            transaction_id (int): ID of the transaction

        Returns:
            Transaction: The retrieved transaction
        """
        pass

    @abstractmethod
    def get_transactions_by_type(
        self,
        transaction_type: TransactionType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Retrieve transactions by type and optional date range.

        Args:
            transaction_type (TransactionType): Type of transactions to retrieve
            start_date (Optional[datetime]): Start of date range
            end_date (Optional[datetime]): End of date range

        Returns:
            List[Transaction]: List of transactions matching the criteria
        """
        pass


class IMaterialTransactionService(ITransactionService):
    """
    Interface for Material Transaction specific operations.
    """

    @abstractmethod
    def create_material_transaction(
        self,
        material_id: int,
        quantity: float,
        transaction_type: TransactionType,
        **kwargs
    ) -> MaterialTransaction:
        """
        Create a material-specific transaction.

        Args:
            material_id (int): ID of the material
            quantity (float): Quantity of material in the transaction
            transaction_type (TransactionType): Type of transaction
            **kwargs: Additional transaction attributes

        Returns:
            MaterialTransaction: The created material transaction
        """
        pass


class ILeatherTransactionService(ITransactionService):
    """
    Interface for Leather Transaction specific operations.
    """

    @abstractmethod
    def create_leather_transaction(
        self,
        leather_id: int,
        quantity: float,
        transaction_type: TransactionType,
        **kwargs
    ) -> LeatherTransaction:
        """
        Create a leather-specific transaction.

        Args:
            leather_id (int): ID of the leather
            quantity (float): Quantity of leather in the transaction
            transaction_type (TransactionType): Type of transaction
            **kwargs: Additional transaction attributes

        Returns:
            LeatherTransaction: The created leather transaction
        """
        pass


class IHardwareTransactionService(ITransactionService):
    """
    Interface for Hardware Transaction specific operations.
    """

    @abstractmethod
    def create_hardware_transaction(
        self,
        hardware_id: int,
        quantity: int,
        transaction_type: TransactionType,
        **kwargs
    ) -> HardwareTransaction:
        """
        Create a hardware-specific transaction.

        Args:
            hardware_id (int): ID of the hardware
            quantity (int): Quantity of hardware in the transaction
            transaction_type (TransactionType): Type of transaction
            **kwargs: Additional transaction attributes

        Returns:
            HardwareTransaction: The created hardware transaction
        """
        pass