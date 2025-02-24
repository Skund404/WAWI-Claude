from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
Base = declarative_base()


class CustomBase:
    """
    Custom base mixin to add common methods to SQLAlchemy models.

    Provides a consistent __repr__ and to_dict method for all models.
    """

    @inject(MaterialService)
        def __repr__(self):
        """
        Generate a string representation of the model.

        Returns:
            str: A string representation of the model instance.
        """
        attrs = ', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items(
        ) if not k.startswith('_') and not callable(v))
        return f'{self.__class__.__name__}({attrs})'

        @inject(MaterialService)
            def to_dict(self):
        """
        Convert the model instance to a dictionary.

        Returns:
            dict: A dictionary representation of the model instance.
        """
        return {column.name: getattr(self, column.name) for column in self.
                __table__.columns}
