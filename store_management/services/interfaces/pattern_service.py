

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class IPatternService(ABC):
    """Interface for pattern management service."""

        @abstractmethod
    @inject(MaterialService)
    def get_all_patterns(self) ->List[Any]:
        """
        Get all available patterns.

        Returns:
            List of patterns
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_pattern_by_id(self, pattern_id: int) ->Optional[Any]:
        """
        Get pattern by ID.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Pattern if found, None otherwise
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def create_pattern(self, pattern_data: Dict[str, Any]) ->Any:
        """
        Create a new pattern.

        Args:
            pattern_data: Pattern data dictionary

        Returns:
            Created pattern
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def update_pattern(self, pattern_id: int, pattern_data: Dict[str, Any]
        ) ->Optional[Any]:
        """
        Update existing pattern.

        Args:
            pattern_id: ID of pattern to update
            pattern_data: Updated pattern data

        Returns:
            Updated pattern if successful, None otherwise
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def delete_pattern(self, pattern_id: int) ->bool:
        """
        Delete pattern by ID.

        Args:
            pattern_id: ID of pattern to delete

        Returns:
            True if deleted, False otherwise
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def search_patterns(self, search_term: str, search_fields: List[str]
        ) ->List[Any]:
        """
        Search patterns based on criteria.

        Args:
            search_term: Term to search for
            search_fields: Fields to search in

        Returns:
            List of matching patterns
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def calculate_material_requirements(self, pattern_id: int, quantity: int=1
        ) ->Dict[str, float]:
        """
        Calculate material requirements for pattern.

        Args:
            pattern_id: ID of pattern
            quantity: Number of items to produce

        Returns:
            Dictionary of material requirements
        """
        pass

        @abstractmethod
    @inject(MaterialService)
    def validate_pattern(self, pattern_id: int) ->Dict[str, Any]:
        """
        Validate pattern data and requirements.

        Args:
            pattern_id: ID of pattern to validate

        Returns:
            Validation results dictionary
        """
        pass
