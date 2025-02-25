# transaction_mixin.py
from typing import Any, Callable, Dict, TypeVar, Generic
from contextlib import contextmanager
from sqlalchemy.orm import Session

from di.core import inject
from services.interfaces import MaterialService

T = TypeVar('T')


class TransactionMixin:
    """Mixin providing transaction handling for complex operations.

    This mixin provides methods to run operations in transactions and handle errors.
    """

    @contextmanager
    def run_in_transaction(self):
        """Run operations in a transaction with error handling.

        Usage:
            with self.run_in_transaction() as session:
                # Perform operations

        Yields:
            SQLAlchemy session
        """
        with self.session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def execute_with_result(self, operation: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute an operation in a transaction and return a standard result.

        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Dictionary with operation result:
            {
                'success': True/False,
                'data': Result data (if successful),
                'error': Error message (if failed)
            }
        """
        try:
            with self.run_in_transaction() as session:
                result = operation(session, *args, **kwargs)
                return {'success': True, 'data': result, 'error': None}
        except Exception as e:
            return {'success': False, 'data': None, 'error': str(e)}