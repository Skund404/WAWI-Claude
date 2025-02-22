from typing import Optional, Dict, Any, Type, TypeVar, Generic, Callable
from contextlib import contextmanager
from database.sqlalchemy.session import get_db_session

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
        with get_db_session() as session:
            yield session

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
                return {
                    'success': True,
                    'data': result
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }