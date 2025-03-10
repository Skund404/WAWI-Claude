# database/repositories/base_repository.py
from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Optional, List, Type, Dict, Any, Callable, Tuple
import logging

# Generic type variable for entity models
T = TypeVar('T')


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found."""
    pass


class ValidationError(RepositoryError):
    """Raised when entity validation fails."""
    pass


class BaseRepository(Generic[T]):
    """Base repository providing common operations for all entity types.

    This generic class implements common CRUD operations and utilities
    that all entity-specific repositories inherit. It uses generic typing
    to ensure type safety for the entity classes.

    Attributes:
        session: The SQLAlchemy session for database access
        logger: Logger for this repository
        model_class: The SQLAlchemy model class this repository manages
    """

    def __init__(self, session: Session):
        """Initialize repository with session injection.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.model_class: Type[T] = self._get_model_class()

    def _get_model_class(self) -> Type[T]:
        """Return the model class this repository manages.

        Returns:
            The SQLAlchemy model class

        Note:
            Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement _get_model_class")

    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity instance or None if not found
        """
        self.logger.debug(f"Getting {self.model_class.__name__} with ID {id}")
        return self.session.query(self.model_class).filter_by(id=id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of entity instances
        """
        self.logger.debug(f"Getting all {self.model_class.__name__} (skip={skip}, limit={limit})")
        return self.session.query(self.model_class).offset(skip).limit(limit).all()

    def create(self, entity: T) -> T:
        """Create new entity.

        Args:
            entity: Entity instance to create

        Returns:
            Created entity with ID assigned

        Raises:
            ValidationError: If entity validation fails
        """
        try:
            self.logger.debug(f"Creating new {self.model_class.__name__}")
            self.session.add(entity)
            self.session.flush()
            return entity
        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to create {self.model_class.__name__}: {str(e)}")

    def update(self, entity: T) -> T:
        """Update existing entity.

        Args:
            entity: Entity instance to update

        Returns:
            Updated entity

        Raises:
            ValidationError: If entity validation fails
        """
        try:
            self.logger.debug(f"Updating {self.model_class.__name__} with ID {getattr(entity, 'id', None)}")
            self.session.merge(entity)
            self.session.flush()
            return entity
        except Exception as e:
            self.logger.error(f"Error updating {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to update {self.model_class.__name__}: {str(e)}")

    def delete(self, entity: T) -> None:
        """Delete entity.

        Args:
            entity: Entity instance to delete

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            self.logger.debug(f"Deleting {self.model_class.__name__} with ID {getattr(entity, 'id', None)}")
            self.session.delete(entity)
            self.session.flush()
        except Exception as e:
            self.logger.error(f"Error deleting {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to delete {self.model_class.__name__}: {str(e)}")

    def filter_by(self, **kwargs) -> List[T]:
        """Filter entities by exact match criteria.

        Args:
            **kwargs: Filter criteria as field=value pairs

        Returns:
            List of matching entities
        """
        self.logger.debug(f"Filtering {self.model_class.__name__} by {kwargs}")
        return self.session.query(self.model_class).filter_by(**kwargs).all()

    def search(self, search_term: str, fields: List[str]) -> List[T]:
        """Search entities by term across specified fields.

        Args:
            search_term: Term to search for
            fields: Model fields to search in

        Returns:
            List of matching entities
        """
        from sqlalchemy import or_

        self.logger.debug(f"Searching {self.model_class.__name__} for '{search_term}' in fields {fields}")

        if not search_term or not fields:
            return []

        filters = []
        for field in fields:
            if hasattr(self.model_class, field):
                attr = getattr(self.model_class, field)
                filters.append(attr.ilike(f"%{search_term}%"))

        if not filters:
            return []

        return self.session.query(self.model_class).filter(or_(*filters)).all()

    def count(self, **filter_criteria) -> int:
        """Count entities matching criteria.

        Args:
            **filter_criteria: Filter criteria as field=value pairs

        Returns:
            Count of matching entities
        """
        query = self.session.query(self.model_class)
        if filter_criteria:
            query = query.filter_by(**filter_criteria)
        return query.count()

    def exists(self, **filter_criteria) -> bool:
        """Check if entities matching criteria exist.

        Args:
            **filter_criteria: Filter criteria as field=value pairs

        Returns:
            True if matching entities exist, False otherwise
        """
        return self.count(**filter_criteria) > 0

    def find_or_create(self, search_criteria: Dict[str, Any], create_data: Dict[str, Any]) -> Tuple[T, bool]:
        """Find an entity by criteria or create if not found.

        Args:
            search_criteria: Criteria to search for existing entity
            create_data: Data to use for creating a new entity if not found

        Returns:
            Tuple of (entity, created) where created is True if a new entity was created

        Raises:
            ValidationError: If entity creation fails
        """
        # Try to find by search criteria
        entity = self.session.query(self.model_class).filter_by(**search_criteria).first()

        if entity:
            return entity, False

        # Create new entity
        entity = self.model_class(**create_data)
        created_entity = self.create(entity)
        return created_entity, True

    def bulk_create(self, entities: List[T]) -> List[T]:
        """Create multiple entities in a single operation.

        Args:
            entities: List of entity instances to create

        Returns:
            List of created entities with IDs assigned

        Raises:
            ValidationError: If validation fails for any entity
        """
        if not entities:
            return []

        try:
            self.logger.debug(f"Bulk creating {len(entities)} {self.model_class.__name__} instances")
            self.session.add_all(entities)
            self.session.flush()
            return entities
        except Exception as e:
            self.logger.error(f"Error bulk creating {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to bulk create {self.model_class.__name__}: {str(e)}")

    def bulk_update(self, entities: List[T]) -> List[T]:
        """Update multiple entities in a single operation.

        Args:
            entities: List of entity instances to update

        Returns:
            List of updated entities

        Raises:
            ValidationError: If validation fails for any entity
        """
        if not entities:
            return []

        try:
            self.logger.debug(f"Bulk updating {len(entities)} {self.model_class.__name__} instances")
            for entity in entities:
                self.session.merge(entity)
            self.session.flush()
            return entities
        except Exception as e:
            self.logger.error(f"Error bulk updating {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to bulk update {self.model_class.__name__}: {str(e)}")

    def bulk_delete(self, entities: List[T]) -> None:
        """Delete multiple entities in a single operation.

        Args:
            entities: List of entity instances to delete

        Raises:
            RepositoryError: If deletion fails for any entity
        """
        if not entities:
            return

        try:
            self.logger.debug(f"Bulk deleting {len(entities)} {self.model_class.__name__} instances")
            for entity in entities:
                self.session.delete(entity)
            self.session.flush()
        except Exception as e:
            self.logger.error(f"Error bulk deleting {self.model_class.__name__}: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to bulk delete {self.model_class.__name__}: {str(e)}")

    def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID.

        Args:
            id: ID of the entity to delete

        Returns:
            True if entity was deleted, False if entity not found

        Raises:
            RepositoryError: If deletion fails
        """
        entity = self.get_by_id(id)
        if not entity:
            return False

        self.delete(entity)
        return True

    def update_or_create(self, search_criteria: Dict[str, Any], update_data: Dict[str, Any]) -> Tuple[T, bool]:
        """Update an entity by criteria or create if not found.

        Args:
            search_criteria: Criteria to search for existing entity
            update_data: Data to use for updating or creating the entity

        Returns:
            Tuple of (entity, created) where created is True if a new entity was created

        Raises:
            ValidationError: If entity update or creation fails
        """
        # Try to find by search criteria
        entity = self.session.query(self.model_class).filter_by(**search_criteria).first()

        if entity:
            # Update existing entity
            for key, value in update_data.items():
                setattr(entity, key, value)
            updated_entity = self.update(entity)
            return updated_entity, False

        # Create new entity with combined data
        create_data = {**search_criteria, **update_data}
        entity = self.model_class(**create_data)
        created_entity = self.create(entity)
        return created_entity, True

    def paginate(self, page: int = 1, page_size: int = 20, **filter_criteria) -> Dict[str, Any]:
        """Get paginated results with optional filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            **filter_criteria: Optional filter criteria

        Returns:
            Dictionary with paginated results and metadata
        """
        # Build query
        query = self.session.query(self.model_class)

        # Apply filters if provided
        if filter_criteria:
            query = query.filter_by(**filter_criteria)

        # Get total count for pagination
        total_count = query.count()

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        items = query.all()

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }