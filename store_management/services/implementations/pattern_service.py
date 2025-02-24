# services/implementations/pattern_service.py

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database.models import Pattern, PatternComponent
from services.interfaces.pattern_service import IPatternService
from utils.error_handler import ApplicationError, ValidationError

logger = logging.getLogger(__name__)


class PatternService(IPatternService):
    """Implementation of pattern management service."""

    def __init__(self, session_factory):
        """
        Initialize service with database session factory.

        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory

    def get_all_patterns(self) -> List[Pattern]:
        """Get all patterns."""
        try:
            with self.session_factory() as session:
                return session.query(Pattern).all()
        except Exception as e:
            logger.error(f"Failed to get patterns: {str(e)}")
            raise ApplicationError("Failed to retrieve patterns", str(e))

    def get_pattern_by_id(self, pattern_id: int) -> Optional[Pattern]:
        """Get pattern by ID."""
        try:
            with self.session_factory() as session:
                return session.query(Pattern).filter(Pattern.id == pattern_id).first()
        except Exception as e:
            logger.error(f"Failed to get pattern {pattern_id}: {str(e)}")
            raise ApplicationError(f"Failed to retrieve pattern {pattern_id}", str(e))

    def create_pattern(self, pattern_data: Dict[str, Any]) -> Pattern:
        """Create new pattern."""
        try:
            with self.session_factory() as session:
                # Validate data
                self._validate_pattern_data(pattern_data)

                # Create pattern
                pattern = Pattern()
                for key, value in pattern_data.items():
                    setattr(pattern, key, value)

                pattern.created_at = datetime.now()
                pattern.updated_at = datetime.now()

                session.add(pattern)
                session.commit()
                return pattern

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create pattern: {str(e)}")
            raise ApplicationError("Failed to create pattern", str(e))

    def update_pattern(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Optional[Pattern]:
        """Update existing pattern."""
        try:
            with self.session_factory() as session:
                pattern = session.query(Pattern).filter(Pattern.id == pattern_id).first()
                if not pattern:
                    return None

                # Validate data
                self._validate_pattern_data(pattern_data)

                # Update pattern
                for key, value in pattern_data.items():
                    setattr(pattern, key, value)

                pattern.updated_at = datetime.now()

                session.commit()
                return pattern

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update pattern {pattern_id}: {str(e)}")
            raise ApplicationError(f"Failed to update pattern {pattern_id}", str(e))

    def delete_pattern(self, pattern_id: int) -> bool:
        """Delete pattern by ID."""
        try:
            with self.session_factory() as session:
                pattern = session.query(Pattern).filter(Pattern.id == pattern_id).first()
                if not pattern:
                    return False

                session.delete(pattern)
                session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern_id}: {str(e)}")
            raise ApplicationError(f"Failed to delete pattern {pattern_id}", str(e))

    def search_patterns(self, search_term: str, search_fields: List[str]) -> List[Pattern]:
        """Search patterns."""
        try:
            with self.session_factory() as session:
                query = session.query(Pattern)

                # Build search criteria
                criteria = []
                for field in search_fields:
                    if hasattr(Pattern, field):
                        criteria.append(getattr(Pattern, field).ilike(f"%{search_term}%"))

                if criteria:
                    query = query.filter(or_(*criteria))

                return query.all()

        except Exception as e:
            logger.error(f"Failed to search patterns: {str(e)}")
            raise ApplicationError("Failed to search patterns", str(e))

    def calculate_material_requirements(self, pattern_id: int, quantity: int = 1) -> Dict[str, float]:
        """Calculate material requirements."""
        try:
            with self.session_factory() as session:
                pattern = session.query(Pattern).filter(Pattern.id == pattern_id).first()
                if not pattern:
                    raise ValidationError(f"Pattern {pattern_id} not found")

                requirements = {}
                for component in pattern.components:
                    material_type = component.material_type.name
                    required_quantity = component.quantity * quantity

                    if material_type in requirements:
                        requirements[material_type] += required_quantity
                    else:
                        requirements[material_type] = required_quantity

                return requirements

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate requirements for pattern {pattern_id}: {str(e)}")
            raise ApplicationError(f"Failed to calculate pattern requirements", str(e))

    def validate_pattern(self, pattern_id: int) -> Dict[str, Any]:
        """Validate pattern data."""
        try:
            with self.session_factory() as session:
                pattern = session.query(Pattern).filter(Pattern.id == pattern_id).first()
                if not pattern:
                    raise ValidationError(f"Pattern {pattern_id} not found")

                validation_results = {
                    'is_valid': True,
                    'errors': [],
                    'warnings': []
                }

                # Validate basic data
                if not pattern.name:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append("Pattern name is required")

                if not pattern.components:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append("Pattern must have at least one component")

                # Validate components
                for component in pattern.components:
                    if component.quantity <= 0:
                        validation_results['errors'].append(
                            f"Invalid quantity for component {component.name}")
                        validation_results['is_valid'] = False

                    if component.unit_cost < 0:
                        validation_results['errors'].append(
                            f"Invalid unit cost for component {component.name}")
                        validation_results['is_valid'] = False

                return validation_results

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate pattern {pattern_id}: {str(e)}")
            raise ApplicationError(f"Failed to validate pattern", str(e))

    def _validate_pattern_data(self, pattern_data: Dict[str, Any]) -> None:
        """
        Validate pattern data before creation/update.

        Args:
            pattern_data: Pattern data to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if 'name' not in pattern_data or not pattern_data['name']:
            errors.append("Pattern name is required")

        if 'base_labor_hours' in pattern_data:
            try:
                hours = float(pattern_data['base_labor_hours'])
                if hours < 0:
                    errors.append("Base labor hours must be positive")
            except ValueError:
                errors.append("Invalid base labor hours value")

        if errors:
            raise ValidationError("Pattern validation failed", errors)