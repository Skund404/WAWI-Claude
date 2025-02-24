from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Base model classes for the store management system.

This module defines the base classes for all database models in the system.
It includes the SQLAlchemy declarative base class and a BaseModel class with
common functionality for all models.
"""
T = TypeVar('T', bound='BaseModel')


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base class for all models.
    """
    pass


class BaseModel:
    """
    Base model class that provides common functionality for all models.
    
    This class includes methods for converting models to dictionaries,
    getting primary key values, and basic CRUD operations.
    """

        @inject(MaterialService)
        def __repr__(self) ->str:
        """
        Get a string representation of the model.
        
        Returns:
            str: String representation of the model
        """
        cls_name = self.__class__.__name__
        try:
            pk_value = self.get_primary_key_value()
            return f'<{cls_name} id={pk_value}>'
        except Exception:
            return f'<{cls_name}>'

        @inject(MaterialService)
        def get_primary_key_value(self) ->Any:
        """
        Get the primary key value of the model.
        
        Returns:
            Any: The primary key value
            
        Raises:
            ValueError: If primary key can't be determined
        """
        try:
            inspector = inspect(self.__class__)
            pk_column = inspector.primary_key[0]
            return getattr(self, pk_column.name)
        except (IndexError, AttributeError) as e:
            raise ValueError(
                f'Could not determine primary key for {self.__class__.__name__}'
                ) from e

        @inject(MaterialService)
        def to_dict(self, exclude_fields: Optional[List[str]]=None) ->Dict[str, Any
        ]:
        """
        Convert the model to a dictionary.
        
        Args:
            exclude_fields: List of field names to exclude
            
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        if exclude_fields is None:
            exclude_fields = []
        result = {}
        for column in inspect(self.__class__).columns:
            if column.name not in exclude_fields:
                result[column.name] = getattr(self, column.name)
        return result

        @inject(MaterialService)
        def update(self) ->None:
        """
        Update the model in the database.
        
        This is a placeholder method that should be implemented by specific
        database integration code.
        """
        pass

        @classmethod
    def create(cls: Type[T]) ->T:
        """
        Create a new instance of the model.
        
        This is a placeholder method that should be implemented by specific
        database integration code.
        
        Returns:
            T: A new instance of the model
        """
        return cls()
