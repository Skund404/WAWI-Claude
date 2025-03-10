from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.pattern_repository import PatternRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.product_repository import ProductRepository

from database.models.enums import SkillLevel, ProjectType

from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError, BusinessRuleError
from services.dto.pattern_dto import PatternDTO, PatternComponentDTO

from di.inject import inject


class PatternService(BaseService):
    """Implementation of the pattern service interface."""

    @inject
    def __init__(self, session: Session,
                 pattern_repository: Optional[PatternRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 product_repository: Optional[ProductRepository] = None):
        """Initialize the pattern service."""
        super().__init__(session)
        self.pattern_repository = pattern_repository or PatternRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, pattern_id: int) -> Dict[str, Any]:
        """Get pattern by ID."""
        try:
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")
            return PatternDTO.from_model(pattern, include_components=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving pattern {pattern_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all patterns, optionally filtered."""
        try:
            patterns = self.pattern_repository.get_all(filters=filters)
            return [PatternDTO.from_model(pattern).to_dict() for pattern in patterns]
        except Exception as e:
            self.logger.error(f"Error retrieving patterns: {str(e)}")
            raise

    def create(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pattern."""
        try:
            # Validate pattern data
            self._validate_pattern_data(pattern_data)

            # Handle components separately
            component_ids = pattern_data.pop('component_ids', []) if 'component_ids' in pattern_data else []

            # Create pattern
            with self.transaction():
                pattern = self.pattern_repository.create(pattern_data)

                # Add components if provided
                for component_id in component_ids:
                    component = self.component_repository.get_by_id(component_id)
                    if not component:
                        self.logger.warning(f"Component with ID {component_id} not found, skipping association")
                        continue
                    self.pattern_repository.add_component(pattern.id, component_id)

                return PatternDTO.from_model(pattern, include_components=True).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating pattern: {str(e)}")
            raise

    def update(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Validate pattern data
            self._validate_pattern_data(pattern_data, update=True)

            # Update pattern
            with self.transaction():
                updated_pattern = self.pattern_repository.update(pattern_id, pattern_data)
                return PatternDTO.from_model(updated_pattern, include_components=True).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating pattern {pattern_id}: {str(e)}")
            raise

    def delete(self, pattern_id: int) -> bool:
        """Delete a pattern by ID."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Check if pattern is used in any products
            products = self.product_repository.get_by_pattern(pattern_id)
            if products:
                raise BusinessRuleError(f"Cannot delete pattern with ID {pattern_id} because it is used in products")

            # Delete pattern
            with self.transaction():
                return self.pattern_repository.delete(pattern_id)
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting pattern {pattern_id}: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for patterns by name or other properties."""
        try:
            patterns = self.pattern_repository.search(query)
            return [PatternDTO.from_model(pattern).to_dict() for pattern in patterns]
        except Exception as e:
            self.logger.error(f"Error searching patterns with query '{query}': {str(e)}")
            raise

    def get_by_skill_level(self, skill_level: str) -> List[Dict[str, Any]]:
        """Get patterns by skill level."""
        try:
            # Validate skill level
            if not hasattr(SkillLevel, skill_level):
                raise ValidationError(f"Invalid skill level: {skill_level}")

            patterns = self.pattern_repository.get_by_skill_level(skill_level)
            return [PatternDTO.from_model(pattern).to_dict() for pattern in patterns]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving patterns with skill level '{skill_level}': {str(e)}")
            raise

    def get_pattern_components(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get all components for a pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Get components
            components = self.pattern_repository.get_components(pattern_id)
            result = []

            for relationship in components:
                component = getattr(relationship, 'component', None)
                if component:
                    component_data = {
                        'id': component.id,
                        'name': component.name,
                        'component_type': getattr(component, 'component_type', None),
                        'description': getattr(component, 'description', None),
                        'quantity': getattr(relationship, 'quantity', 1),
                        'attributes': getattr(component, 'attributes', {})
                    }
                    result.append(component_data)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving components for pattern {pattern_id}: {str(e)}")
            raise

    def add_component_to_pattern(self, pattern_id: int, component_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Add a component to a pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Check if association already exists
            existing = self.pattern_repository.get_component_relationship(pattern_id, component_id)
            if existing:
                # Update quantity if needed
                if getattr(existing, 'quantity', 1) != quantity:
                    update_data = {'quantity': quantity}
                    self.pattern_repository.update_component_relationship(pattern_id, component_id, update_data)

                pattern = self.pattern_repository.get_by_id(pattern_id)
                return PatternDTO.from_model(pattern, include_components=True).to_dict()

            # Add component to pattern with quantity
            with self.transaction():
                self.pattern_repository.add_component(pattern_id, component_id, quantity)
                updated_pattern = self.pattern_repository.get_by_id(pattern_id)
                return PatternDTO.from_model(updated_pattern, include_components=True).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error adding component {component_id} to pattern {pattern_id}: {str(e)}")
            raise

    def remove_component_from_pattern(self, pattern_id: int, component_id: int) -> bool:
        """Remove a component from a pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Check if component exists
            component = self.component_repository.get_by_id(component_id)
            if not component:
                raise NotFoundError(f"Component with ID {component_id} not found")

            # Remove component from pattern
            with self.transaction():
                result = self.pattern_repository.remove_component(pattern_id, component_id)
                return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing component {component_id} from pattern {pattern_id}: {str(e)}")
            raise

    def get_patterns_by_project_type(self, project_type: str) -> List[Dict[str, Any]]:
        """Get patterns by project type."""
        try:
            # Validate project type
            if not hasattr(ProjectType, project_type):
                raise ValidationError(f"Invalid project type: {project_type}")

            patterns = self.pattern_repository.get_by_project_type(project_type)
            return [PatternDTO.from_model(pattern).to_dict() for pattern in patterns]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving patterns for project type '{project_type}': {str(e)}")
            raise

    def get_material_requirements(self, pattern_id: int) -> Dict[str, Any]:
        """Get material requirements for a pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Get detailed pattern with components and materials
            pattern_dto = PatternDTO.from_model(pattern, include_components=True, include_materials=True)

            material_requirements = pattern_dto.material_requirements or []

            return {
                'pattern_id': pattern_id,
                'pattern_name': pattern.name,
                'material_count': len(material_requirements),
                'materials': material_requirements
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving material requirements for pattern {pattern_id}: {str(e)}")
            raise

    def get_products_using_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get products that use a specific pattern."""
        try:
            # Check if pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            products = self.product_repository.get_by_pattern(pattern_id)
            result = []

            for product in products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'description': getattr(product, 'description', None),
                    'price': getattr(product, 'price', None),
                    'is_active': getattr(product, 'is_active', True)
                }
                result.append(product_data)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving products using pattern {pattern_id}: {str(e)}")
            raise

    def _validate_pattern_data(self, pattern_data: Dict[str, Any], update: bool = False) -> None:
        """Validate pattern data.

        Args:
            pattern_data: Pattern data to validate
            update: Whether this is for an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields for new patterns
        if not update:
            required_fields = ['name']
            for field in required_fields:
                if field not in pattern_data or not pattern_data[field]:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate skill level if provided
        if 'skill_level' in pattern_data and pattern_data['skill_level']:
            skill_level = pattern_data['skill_level']
            if not hasattr(SkillLevel, skill_level):
                raise ValidationError(f"Invalid skill level: {skill_level}")

        # Validate project type if provided
        if 'project_type' in pattern_data and pattern_data['project_type']:
            project_type = pattern_data['project_type']
            if not hasattr(ProjectType, project_type):
                raise ValidationError(f"Invalid project type: {project_type}")

        # Validate component IDs if provided
        if 'component_ids' in pattern_data and pattern_data['component_ids']:
            component_ids = pattern_data['component_ids']
            if not isinstance(component_ids, list):
                raise ValidationError("Component IDs must be a list")