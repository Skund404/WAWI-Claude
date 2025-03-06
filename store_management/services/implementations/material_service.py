# services/implementations/material_service.py
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import or_, select, inspect, text
from typing import Any, Dict, List, Optional, Union, Tuple

from database.models.enums import InventoryStatus, MaterialType, TransactionType
from database.models.material import Material
from database.models.leather import Leather
from database.models.hardware import Hardware
from database.models.base import ModelValidationError
from database.models.transaction import MaterialTransaction, LeatherTransaction, HardwareTransaction
from database.repositories.material_repository import MaterialRepository
from database.repositories.leather_repository import LeatherRepository
from database.repositories.hardware_repository import HardwareRepository
from database.repositories.transaction_repository import TransactionRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.material_service import IMaterialService, MaterialType as IMaterialType

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from utils.logger import log_debug, log_error, log_info


class MaterialService(BaseService[Material], IMaterialService):
    """Service for material-related operations."""

    def __init__(self, session: Session):
        """Initialize the Material Service.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__()
        self._session = session
        self._repository = MaterialRepository(session)
        self._logger = logging.getLogger(__name__)

        # Initialize additional repositories for different material types
        try:
            self._leather_repository = LeatherRepository(session)
            self._hardware_repository = HardwareRepository(session)
            self._transaction_repository = TransactionRepository(session)
            self._logger.info("MaterialService initialized with all repositories")
        except Exception as e:
            self._logger.warning(f"Could not initialize all repositories: {e}")

    def _ensure_session_active(self) -> Tuple[Session, bool]:
        """
        Ensure the session is active, creating a new one if needed.

        Returns:
            Tuple[Session, bool]: A tuple containing the active session and a boolean
                                 indicating if a new session was created
        """
        try:
            # Check if session exists and is active
            if not hasattr(self, '_session') or self._session is None:
                self._logger.warning("Session is None, creating a new one")
                self._session = get_db_session()
                return self._session, True

            # Test session connection
            try:
                # Simple query to test connection
                self._session.execute(text("SELECT 1")).scalar()
                return self._session, False
            except Exception as e:
                self._logger.warning(f"Session connection test failed: {e}, creating a new one")
                # Close old session if possible
                try:
                    self._session.close()
                except:
                    pass
                # Create new session
                self._session = get_db_session()
                # Update repositories with new session
                self._repository.session = self._session
                if hasattr(self, '_leather_repository'):
                    self._leather_repository.session = self._session
                if hasattr(self, '_hardware_repository'):
                    self._hardware_repository.session = self._session
                if hasattr(self, '_transaction_repository'):
                    self._transaction_repository.session = self._session
                return self._session, True
        except Exception as e:
            self._logger.error(f"Error ensuring active session: {e}")
            # Return a new session as fallback
            return get_db_session(), True

    def debug_table_schema(self, table_name):
        """
        Debug the schema of a specific table, especially checking column types and constraints.

        Args:
            table_name: Name of the table to inspect
        """
        session, is_new_session = self._ensure_session_active()
        logger = logging.getLogger(__name__)

        try:
            # Use SQLAlchemy inspector
            inspector = inspect(session.bind)

            # Get columns
            columns = inspector.get_columns(table_name)
            logger.info(f"Columns in {table_name}:")
            for col in columns:
                logger.info(f"  {col['name']}: {col['type']} (nullable: {col.get('nullable', 'Unknown')})")

            # Try to get table constraints
            try:
                foreign_keys = inspector.get_foreign_keys(table_name)
                logger.info("Foreign Keys:")
                for fk in foreign_keys:
                    logger.info(f"  {fk}")
            except Exception as fk_error:
                logger.warning(f"Could not retrieve foreign keys: {fk_error}")

            # Direct SQL inspection for more details
            try:
                # Get detailed schema information
                result = session.execute(text(f"PRAGMA table_info({table_name})"))
                logger.info(f"PRAGMA table_info for {table_name}:")
                for row in result:
                    logger.info(f"  {row}")
            except Exception as sql_error:
                logger.warning(f"Could not execute PRAGMA for {table_name}: {sql_error}")

        except Exception as e:
            logger.error(f"Error inspecting {table_name} schema: {e}")
        finally:
            # Close the session if we created a new one
            if is_new_session:
                try:
                    session.close()
                except:
                    pass

    # Existing methods remain the same...
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new material.

        Args:
            data: Material creation data

        Returns:
            Created material ID
        """
        return self.create_material(data)

    def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get material by ID.

        Args:
            material_id: ID of the material

        Returns:
            Material data or None if not found
        """
        try:
            return self.get_material_by_id(int(material_id))
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def update(self, material_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material.

        Args:
            material_id: ID of the material
            updates: Update data

        Returns:
            Updated material data or None if not found
        """
        try:
            return self.update_material(int(material_id), updates)
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def delete(self, material_id: str) -> bool:
        """Delete a material.

        Args:
            material_id: ID of the material

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.delete_material(int(material_id))
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def get_materials(self, material_type=None, **kwargs):
        """
        Get materials with the given material type and optional filters.

        Args:
            material_type: The type of material to filter by.
            **kwargs: Additional filters to apply.

        Returns:
            List of materials matching the filters.
        """
        session, is_new_session = self._ensure_session_active()

        try:
            # Debug table schema before query
            self.debug_table_schema('materials')

            self._logger.info(f"get_materials called with material_type={material_type}")

            # Build filter conditions based on keyword arguments
            conditions = []

            # Handle material_type parameter (either as positional or keyword arg)
            if material_type is not None:
                # Handle different ways material_type might be provided
                if hasattr(material_type, 'name'):
                    # It's an enum object, use its name
                    material_type_value = material_type.name
                    self._logger.info(f"Using material_type enum name: {material_type_value}")
                else:
                    # It's something else (string, etc.), use it directly
                    material_type_value = material_type
                    self._logger.info(f"Using material_type value directly: {material_type_value}")

                conditions.append(Material.material_type == material_type_value)

            # Create the base query
            query = select(Material)

            # Apply filters if any
            if conditions:
                query = query.where(*conditions)

            # Execute the query
            materials = session.execute(query).scalars().all()
            self._logger.info(f"Found {len(materials)} materials")

            # Convert materials to dictionaries with serialized enum values
            result = []
            for material in materials:
                material_dict = self.to_dict(material)

                # Serialize enum values
                for key, value in material_dict.items():
                    material_dict[key] = self._serialize_enum_value(value)

                result.append(material_dict)

            return result

        except SQLAlchemyError as e:
            # Log detailed SQLAlchemy error
            self._logger.error(f"Database error in get_materials: {e}")
            # Return empty list instead of raising exception to prevent UI crashes
            return []
        except Exception as e:
            # Log unexpected errors
            self._logger.error(f"Unexpected error in get_materials: {e}")
            # Return empty list instead of raising exception
            return []
        finally:
            # Close the session if we created a new one
            if is_new_session:
                try:
                    session.close()
                except:
                    pass

    def _serialize_enum_value(self, value):
        """
        Safely serialize enum values or return the original value.

        Args:
            value: The value to serialize

        Returns:
            Serialized value (enum name or original value)
        """
        try:
            # If it's an enum, return its name
            if hasattr(value, 'name'):
                return value.name
            # If it's an enum-like object with a string representation
            elif hasattr(value, '__str__'):
                return str(value)
            # Return the original value if no special handling is needed
            return value
        except Exception as e:
            self._logger.warning(f"Error serializing enum value: {e}")
            return str(value)

    # Implement the missing abstract methods that were causing the error

    def calculate_material_cost(self, material_id: int, quantity: float, material_type=None) -> Decimal:
        """
        Calculate the cost of a given quantity of material.

        Args:
            material_id: ID of the material
            quantity: Quantity of the material
            material_type: Type of the material

        Returns:
            Total cost of the specified quantity of material
        """
        session, is_new_session = self._ensure_session_active()

        try:
            self._logger.info(
                f"Calculating cost for material_id={material_id}, quantity={quantity}, type={material_type}")

            # Try to get the material
            material = None

            # Query the appropriate repository based on material_type
            if material_type and material_type == IMaterialType.LEATHER:
                if hasattr(self, '_leather_repository'):
                    self._leather_repository.session = session
                    material = self._leather_repository.get_by_id(material_id)
            elif material_type and material_type == IMaterialType.HARDWARE:
                if hasattr(self, '_hardware_repository'):
                    self._hardware_repository.session = session
                    material = self._hardware_repository.get_by_id(material_id)
            else:
                # Default to generic material
                self._repository.session = session
                material = self._repository.get_by_id(material_id)

            if not material:
                self._logger.warning(f"Material not found: id={material_id}, type={material_type}")
                return Decimal('0.00')

            # Calculate cost based on unit price and quantity
            unit_price = getattr(material, 'unit_price', Decimal('0.00'))
            if not isinstance(unit_price, Decimal):
                unit_price = Decimal(str(unit_price) if unit_price is not None else '0.00')

            total_cost = unit_price * Decimal(str(quantity))
            self._logger.info(f"Calculated cost: {total_cost} (unit_price={unit_price} * quantity={quantity})")

            return total_cost

        except Exception as e:
            self._logger.error(f"Error calculating material cost: {e}")
            return Decimal('0.00')
        finally:
            # Close the session if we created a new one
            if is_new_session:
                try:
                    session.close()
                except:
                    pass

    def get_material_transactions(self, material_id: int, material_type=None, start_date=None, end_date=None) -> List:
        """
        Get a list of transactions for a specific material.

        Args:
            material_id: ID of the material
            material_type: Type of the material
            start_date: Optional start date for filtering transactions
            end_date: Optional end date for filtering transactions

        Returns:
            List of transactions for the specified material
        """
        session, is_new_session = self._ensure_session_active()

        try:
            self._logger.info(f"Getting transactions for material_id={material_id}, type={material_type}")

            # Prepare filters
            filters = {}

            if start_date:
                filters["start_date"] = start_date

            if end_date:
                filters["end_date"] = end_date

            # If transaction repository doesn't exist, return empty list
            if not hasattr(self, '_transaction_repository'):
                self._logger.warning("Transaction repository not initialized")
                return []

            # Update transaction repository session
            self._transaction_repository.session = session

            # Query the appropriate repository based on material_type
            if material_type == IMaterialType.LEATHER:
                filters["leather_id"] = material_id
                return self._transaction_repository.get_leather_transactions(**filters)
            elif material_type == IMaterialType.HARDWARE:
                filters["hardware_id"] = material_id
                return self._transaction_repository.get_hardware_transactions(**filters)
            else:
                filters["material_id"] = material_id
                return self._transaction_repository.get_material_transactions(**filters)

        except Exception as e:
            self._logger.error(f"Error retrieving material transactions: {e}")
            return []
        finally:
            # Close the session if we created a new one
            if is_new_session:
                try:
                    session.close()
                except:
                    pass

    def get_material_types(self) -> List:
        """
        Get a list of available material types.

        Returns:
            List of available material types
        """
        self._logger.info("Getting material types")

        try:
            # Return all material types from the IMaterialType enum
            return list(IMaterialType)
        except Exception as e:
            self._logger.error(f"Error retrieving material types: {e}")
            return []

    def record_material_transaction(self, material_id: int, quantity: float, transaction_type: str,
                                    material_type=None, notes=None) -> Any:
        """
        Record a transaction for a material.

        Args:
            material_id: ID of the material
            quantity: Quantity of material in the transaction
            transaction_type: Type of transaction (e.g., "IN", "OUT")
            material_type: Type of the material
            notes: Optional notes about the transaction

        Returns:
            Created transaction record
        """
        session, is_new_session = self._ensure_session_active()

        try:
            self._logger.info(f"Recording transaction: material_id={material_id}, quantity={quantity}, "
                              f"type={transaction_type}, material_type={material_type}")

            # If transaction repository doesn't exist, raise exception
            if not hasattr(self, '_transaction_repository'):
                self._logger.error("Transaction repository not initialized")
                raise ServiceError("Transaction repository not initialized")

            # Update transaction repository session
            self._transaction_repository.session = session

            # Create transaction data
            transaction_data = {
                "quantity": quantity,
                "transaction_type": transaction_type,
                "transaction_date": datetime.now(),
                "notes": notes or ""
            }

            # Create and add the appropriate transaction type
            if material_type == IMaterialType.LEATHER:
                transaction = LeatherTransaction(leather_id=material_id, **transaction_data)
            elif material_type == IMaterialType.HARDWARE:
                transaction = HardwareTransaction(hardware_id=material_id, **transaction_data)
            else:
                transaction = MaterialTransaction(material_id=material_id, **transaction_data)

            # Add the transaction
            result = self._transaction_repository.add(transaction)
            self._logger.info(f"Transaction recorded successfully: {result.id}")

            # Update material quantity
            self._update_material_quantity(material_id, quantity, transaction_type, material_type, session)

            return result

        except Exception as e:
            self._logger.error(f"Error recording material transaction: {e}")
            raise ServiceError(f"Failed to record transaction: {str(e)}")
        finally:
            # Close the session if we created a new one
            if is_new_session:
                try:
                    session.close()
                except:
                    pass

    def _update_material_quantity(self, material_id: int, quantity: float,
                                  transaction_type: str, material_type=None, session=None) -> None:
        """
        Update material quantity based on transaction.

        Args:
            material_id: ID of the material
            quantity: Transaction quantity
            transaction_type: Type of transaction
            material_type: Type of the material
            session: Optional session to use
        """
        use_session, is_new_session = (session, False) if session else self._ensure_session_active()

        try:
            # Get the material
            material = None

            # Query the appropriate repository based on material_type
            if material_type == IMaterialType.LEATHER:
                if hasattr(self, '_leather_repository'):
                    self._leather_repository.session = use_session
                    material = self._leather_repository.get_by_id(material_id)
            elif material_type == IMaterialType.HARDWARE:
                if hasattr(self, '_hardware_repository'):
                    self._hardware_repository.session = use_session
                    material = self._hardware_repository.get_by_id(material_id)
            else:
                self._repository.session = use_session
                material = self._repository.get_by_id(material_id)

            if not material:
                self._logger.warning(f"Material not found for quantity update: id={material_id}, type={material_type}")
                return

            # Update quantity based on transaction type
            current_quantity = getattr(material, 'quantity', 0)

            if transaction_type == TransactionType.IN.name:
                new_quantity = current_quantity + quantity
            elif transaction_type == TransactionType.OUT.name:
                new_quantity = max(0, current_quantity - quantity)
            else:
                self._logger.warning(f"Unknown transaction type: {transaction_type}")
                return

            # Update the material
            material.quantity = new_quantity
            use_session.commit()

            self._logger.info(f"Updated material quantity: {current_quantity} -> {new_quantity}")

        except Exception as e:
            self._logger.error(f"Error updating material quantity: {e}")
            # Don't raise here to avoid affecting the transaction creation
        finally:
            # Close the session if we created a new one and weren't provided one
            if is_new_session and not session:
                try:
                    use_session.close()
                except:
                    pass