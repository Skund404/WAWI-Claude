# services/implementations/supplier_service.py
"""
Robust implementation of the Supplier Service for managing supplier-related operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService, SupplierStatus

# Configure specific logger for this module
logger = logging.getLogger(__name__)

class SupplierService(BaseService, ISupplierService):
    """
    Comprehensive Supplier Service implementation with robust error handling.
    """

    def __init__(self):
        """
        Initialize the supplier service with logging and optional in-memory storage.
        """
        super().__init__()
        self._suppliers: Dict[str, Dict[str, Any]] = {}
        logger.info("SupplierService initialized successfully")

    def _safe_import(self, module_path: str):
        """
        Safely import a module with detailed error logging.

        Args:
            module_path (str): Full import path for the module

        Returns:
            Imported module or None if import fails
        """
        try:
            import importlib
            module_name, class_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except ImportError as e:
            logger.error(f"Import error for {module_path}: {e}")
        except AttributeError as e:
            logger.error(f"Attribute error importing {module_path}: {e}")
        return None

    def _get_db_session(self):
        """
        Get a database session with robust error handling.

        Returns:
            SQLAlchemy session or None
        """
        try:
            from database.sqlalchemy.session import get_db_session
            return get_db_session()
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            return None

    def _convert_to_dict(self, supplier) -> Dict[str, Any]:
        """
        Convert a Supplier model to a dictionary with robust handling.

        Args:
            supplier: Supplier model instance

        Returns:
            Dictionary representation of the supplier
        """
        try:
            return {
                'id': getattr(supplier, 'id', None),
                'name': getattr(supplier, 'name', ''),
                'contact_name': getattr(supplier, 'contact_name', ''),
                'email': getattr(supplier, 'email', ''),
                'phone': getattr(supplier, 'phone', ''),
                'address': getattr(supplier, 'address', ''),
                'website': getattr(supplier, 'website', ''),
                'notes': getattr(supplier, 'notes', ''),
                'rating': getattr(supplier, 'rating', 0.0),
                'status': getattr(supplier.status, 'name', str(supplier.status))
                    if hasattr(supplier, 'status') else SupplierStatus.ACTIVE.name,
                'created_at': (supplier.created_at.isoformat()
                    if hasattr(supplier.created_at, 'isoformat')
                    else str(supplier.created_at))
                    if hasattr(supplier, 'created_at') else datetime.now().isoformat(),
                'updated_at': (supplier.updated_at.isoformat()
                    if hasattr(supplier.updated_at, 'isoformat')
                    else str(supplier.updated_at))
                    if hasattr(supplier, 'updated_at') else datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error converting supplier to dict: {e}")
            return {}

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new supplier with comprehensive validation.

        Args:
            supplier_data (Dict[str, Any]): Supplier details

        Returns:
            Dict[str, Any]: Created supplier details
        """
        logger.info("Attempting to create supplier")

        # Basic validation
        if not supplier_data.get('name'):
            raise ValidationError("Supplier name is required")

        try:
            # Try database approach first
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    supplier = Supplier(
                        name=supplier_data['name'],
                        contact_name=supplier_data.get('contact_name', ''),
                        email=supplier_data.get('email', ''),
                        phone=supplier_data.get('phone', ''),
                        address=supplier_data.get('address', ''),
                        website=supplier_data.get('website', ''),
                        status=supplier_data.get('status', SupplierStatus.ACTIVE),
                        notes=supplier_data.get('notes', ''),
                        rating=supplier_data.get('rating', 0.0)
                    )
                    session.add(supplier)
                    session.commit()
                    session.refresh(supplier)
                    return self._convert_to_dict(supplier)
                except Exception as db_err:
                    logger.warning(f"Database creation failed: {db_err}")
                    session.rollback()

            # Fallback to in-memory storage
            supplier_id = str(len(self._suppliers) + 1)
            supplier = {
                'id': supplier_id,
                'name': supplier_data['name'],
                'contact_name': supplier_data.get('contact_name', ''),
                'email': supplier_data.get('email', ''),
                'phone': supplier_data.get('phone', ''),
                'address': supplier_data.get('address', ''),
                'website': supplier_data.get('website', ''),
                'status': supplier_data.get('status', SupplierStatus.ACTIVE.name),
                'notes': supplier_data.get('notes', ''),
                'rating': supplier_data.get('rating', 0.0),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self._suppliers[supplier_id] = supplier
            logger.info(f"Created supplier with ID {supplier_id} in memory")
            return supplier

        except Exception as e:
            logger.error(f"Comprehensive supplier creation failed: {e}")
            raise ValidationError(f"Could not create supplier: {e}")

    def get_all_suppliers(self, status: Optional[SupplierStatus] = None) -> List[Dict[str, Any]]:
        """
        Get all suppliers, with optional status filtering.

        Args:
            status (Optional[SupplierStatus]): Optional status to filter suppliers

        Returns:
            List[Dict[str, Any]]: List of suppliers
        """
        logger.info("Retrieving all suppliers")
        try:
            # Try database approach
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    query = session.query(Supplier)
                    if status is not None:
                        query = query.filter(Supplier.status == status)
                    suppliers = query.all()
                    return [self._convert_to_dict(supplier) for supplier in suppliers]
                except Exception as db_err:
                    logger.warning(f"Database retrieval failed: {db_err}")
                finally:
                    session.close()

            # Fallback to in-memory suppliers
            suppliers = list(self._suppliers.values())
            if status:
                suppliers = [s for s in suppliers if s.get('status') == status.name]
            return suppliers

        except Exception as e:
            logger.error(f"Failed to retrieve suppliers: {e}")
            return list(self._suppliers.values())

    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """
        Get a supplier by their unique identifier.

        Args:
            supplier_id (int): Unique identifier of the supplier

        Returns:
            Dict[str, Any]: Supplier details

        Raises:
            NotFoundError: If supplier is not found
        """
        logger.info(f"Retrieving supplier with ID: {supplier_id}")
        try:
            # Try database approach
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
                    if supplier:
                        return self._convert_to_dict(supplier)
                except Exception as db_err:
                    logger.warning(f"Database retrieval failed: {db_err}")
                finally:
                    session.close()

            # Fallback to in-memory storage
            supplier = self._suppliers.get(str(supplier_id))
            if supplier:
                return supplier

            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        except Exception as e:
            logger.error(f"Failed to retrieve supplier: {e}")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

    def update_supplier(self, supplier_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a supplier's details.

        Args:
            supplier_id (int): ID of the supplier to update
            update_data (Dict[str, Any]): Updated details

        Returns:
            Dict[str, Any]: Updated supplier details

        Raises:
            NotFoundError: If supplier is not found
        """
        logger.info(f"Updating supplier with ID: {supplier_id}")
        try:
            # Try database approach
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
                    if not supplier:
                        raise NotFoundError(f"Supplier with ID {supplier_id} not found")

                    for key, value in update_data.items():
                        if hasattr(supplier, key) and key not in ['id', 'created_at']:
                            setattr(supplier, key, value)

                    session.commit()
                    session.refresh(supplier)
                    return self._convert_to_dict(supplier)
                except Exception as db_err:
                    logger.warning(f"Database update failed: {db_err}")
                    session.rollback()

            # Fallback to in-memory storage
            supplier_str_id = str(supplier_id)
            if supplier_str_id not in self._suppliers:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            supplier = self._suppliers[supplier_str_id]
            for key, value in update_data.items():
                if key not in ['id', 'created_at']:
                    supplier[key] = value
            supplier['updated_at'] = datetime.now().isoformat()
            return supplier

        except Exception as e:
            logger.error(f"Failed to update supplier: {e}")
            raise

    def delete_supplier(self, supplier_id: int) -> bool:
        """
        Delete a supplier.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            bool: Whether deletion was successful

        Raises:
            NotFoundError: If supplier is not found
        """
        logger.info(f"Deleting supplier with ID: {supplier_id}")
        try:
            # Try database approach
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
                    if not supplier:
                        raise NotFoundError(f"Supplier with ID {supplier_id} not found")

                    session.delete(supplier)
                    session.commit()
                    return True
                except Exception as db_err:
                    logger.warning(f"Database deletion failed: {db_err}")
                    session.rollback()

            # Fallback to in-memory storage
            supplier_str_id = str(supplier_id)
            if supplier_str_id not in self._suppliers:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            del self._suppliers[supplier_str_id]
            return True

        except Exception as e:
            logger.error(f"Failed to delete supplier: {e}")
            raise

    def search_suppliers(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for suppliers by name, contact, or other fields.

        Args:
            search_term (str): Term to search for

        Returns:
            List[Dict[str, Any]]: List of matching suppliers
        """
        logger.info(f"Searching suppliers with term: {search_term}")
        try:
            # Try database approach
            Supplier = self._safe_import('database.models.supplier.Supplier')
            session = self._get_db_session()

            if Supplier and session:
                try:
                    from sqlalchemy import or_
                    search_pattern = f"%{search_term}%"
                    suppliers = session.query(Supplier).filter(
                        or_(
                            Supplier.name.ilike(search_pattern),
                            Supplier.contact_name.ilike(search_pattern),
                            Supplier.email.ilike(search_pattern),
                            Supplier.notes.ilike(search_pattern)
                        )
                    ).all()
                    return [self._convert_to_dict(supplier) for supplier in suppliers]
                except Exception as db_err:
                    logger.warning(f"Database search failed: {db_err}")
                finally:
                    session.close()

            # Fallback to in-memory search
            search_lower = search_term.lower()
            return [
                s for s in self._suppliers.values()
                if (search_lower in s.get('name', '').lower() or
                    search_lower in s.get('contact_name', '').lower() or
                    search_lower in s.get('email', '').lower() or
                    search_lower in s.get('notes', '').lower())
            ]

        except Exception as e:
            logger.error(f"Failed to search suppliers: {e}")
            return []

    def get_suppliers_by_status(self, status: SupplierStatus) -> List[Dict[str, Any]]:
        """
        Get suppliers by their status.

        Args:
            status (SupplierStatus): Status to filter suppliers

        Returns:
            List[Dict[str, Any]]: List of suppliers with the given status
        """
        logger.info(f"Getting suppliers with status: {status}")
        return [s for s in self.get_all_suppliers() if s.get('status') == status.name]