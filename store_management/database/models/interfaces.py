from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Interface definitions for the store management system.

This module defines abstract base classes that serve as interfaces for the models
in the system. These interfaces define the methods that model classes must implement.
"""


class IModel(ABC):
    """
    Interface for all model classes.

    Defines common methods that all models should implement.
    """

    @abstractmethod
    @inject(MaterialService)
        def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any
                                                                          ]:
        """
        Convert the model to a dictionary.

        Args:
            exclude_fields: List of field names to exclude

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        pass


class IProject(IModel):
    """
    Interface for project models.

    Defines methods that project models should implement.
    """

    @abstractmethod
    @inject(MaterialService)
        def calculate_complexity(self) -> float:
        """
        Calculate the complexity score of the project.

        Returns:
            float: The calculated complexity score
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the project.

        Returns:
            float: The total estimated cost
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def update_status(self, new_status) -> None:
        """
        Update the project status.

        Args:
            new_status: The new status to set for the project
        """
        pass

        @abstractmethod
    @inject(MaterialService)
        def validate(self) -> List[str]:
        """
        Validate the project data.

        Returns:
            List[str]: List of validation error messages, empty if valid
        """
        pass
