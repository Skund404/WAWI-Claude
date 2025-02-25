# pattern_service.py
# Relative path: pattern_service.py

from typing import Dict, Any, List, Optional
from decimal import Decimal
from functools import lru_cache
import logging

from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
    IPatternService
)
from models.pattern import (
    Pattern,
    PatternComponent,
    SkillLevel,
    MaterialType
)
from repositories.interfaces import IPatternRepository
from config import PATTERN_CONFIG
from exceptions import ApplicationError, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class PatternService(IPatternService):
    """
    Optimized Pattern Service with advanced configuration and caching mechanisms.

    Provides comprehensive pattern management functionality with performance 
    optimizations and advanced querying capabilities.
    """

    @inject(MaterialService)
    def __init__(
            self,
            pattern_repository: IPatternRepository,
            material_service: MaterialService
    ):
        """
        Initialize the Pattern Service with dependencies and performance optimizations.

        Args:
            pattern_repository (IPatternRepository): Pattern repository for data access
            material_service (MaterialService): Material service for material-related operations
        """
        self._pattern_repository = pattern_repository
        self._material_service = material_service
        self._config = PATTERN_CONFIG

    @lru_cache(maxsize=100)
    def get_by_complexity(
            self,
            skill_level: SkillLevel,
            min_complexity: Optional[float] = None,
            max_complexity: Optional[float] = None
    ) -> List[Pattern]:
        """
        Retrieve patterns with advanced filtering and complexity-based sorting.

        Args:
            skill_level (SkillLevel): Target skill level
            min_complexity (Optional[float]): Minimum complexity threshold
            max_complexity (Optional[float]): Maximum complexity threshold

        Returns:
            List[Pattern]: Sorted list of patterns
        """
        try:
            # Prepare search criteria
            criteria = {'skill_level': skill_level}

            # Add minimum complexity filter if specified
            if min_complexity is not None:
                criteria['min_complexity'] = min_complexity

            # Search patterns based on criteria
            patterns = self._pattern_repository.search_by_criteria(criteria)

            # Apply maximum complexity filter if specified
            if max_complexity is not None:
                patterns = [p for p in patterns if p.complexity <= max_complexity]

            # Sort patterns by complexity
            return sorted(patterns, key=lambda p: p.complexity)

        except Exception as e:
            logger.error(f'Error retrieving patterns by complexity: {e}')
            return []

    def calculate_material_requirements(
            self,
            pattern_id: int,
            override_waste_factor: Optional[float] = None
    ) -> Dict[MaterialType, Decimal]:
        """
        Calculate precise material requirements with configurable waste factors.

        Args:
            pattern_id (int): Unique identifier for the pattern
            override_waste_factor (Optional[float]): Custom waste factor to override configuration

        Returns:
            Dict[MaterialType, Decimal]: Material requirements with quantities

        Raises:
            ApplicationError: If calculation fails
        """
        try:
            # Retrieve pattern by ID
            pattern = self._pattern_repository.get_by_id(pattern_id)

            # Initialize material requirements
            material_requirements: Dict[MaterialType, Decimal] = {}

            # Calculate requirements for each component
            for component in pattern.components:
                # Determine waste factor
                waste_factor = (
                        override_waste_factor or
                        self._config.get_waste_factor(component.material_type.name.lower())
                )

                # Calculate adjusted area with waste factor
                required_area = component.calculate_area()
                adjusted_area = required_area * (1 + waste_factor)

                # Update material requirements
                material_type = component.material_type
                material_requirements[material_type] = (
                        material_requirements.get(material_type, Decimal('0')) +
                        Decimal(str(adjusted_area))
                )

            return material_requirements

        except Exception as e:
            logger.error(f'Error calculating material requirements: {e}')
            raise ApplicationError(f'Could not calculate material requirements: {e}')

    def validate_pattern_components(
            self,
            pattern_id: int,
            strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of pattern components with detailed reporting.

        Args:
            pattern_id (int): Unique identifier for the pattern
            strict_mode (bool): Enable additional rigorous validation

        Returns:
            Dict[str, Any]: Validation results with details

        Raises:
            ValidationError: If critical validation fails
        """
        try:
            # Retrieve pattern by ID
            pattern = self._pattern_repository.get_by_id(pattern_id)

            # Initialize validation results
            validation_results: Dict[str, Any] = {
                'is_valid': True,
                'warnings': [],
                'errors': []
            }

            # Validate each component
            for component in pattern.components:
                try:
                    # Validate individual component
                    component.validate_component()
                except ValidationError as ve:
                    # Record validation errors
                    validation_results['errors'].append(str(ve))
                    validation_results['is_valid'] = False

                # Check material availability
                material = self._material_service.get_material_by_type(component.material_type)
                required_area = component.calculate_area()
                waste_factor = self._config.get_waste_factor(component.material_type.name.lower())
                adjusted_area = required_area * (1 + waste_factor)

                # Check if material stock is sufficient
                if material.stock < adjusted_area:
                    warning = (
                        f'Insufficient {component.material_type.name} for component {component.name}. '
                        f'Required: {adjusted_area:.2f}, Available: {material.stock:.2f}'
                    )

                    # Handle insufficient material based on strict mode
                    if strict_mode:
                        validation_results['errors'].append(warning)
                        validation_results['is_valid'] = False
                    else:
                        validation_results['warnings'].append(warning)

                # Additional strict mode validations
                if strict_mode:
                    # Check component quantity
                    if component.quantity <= 0:
                        validation_results['errors'].append(
                            f'Component {component.name} has invalid quantity'
                        )
                        validation_results['is_valid'] = False

            return validation_results

        except Exception as e:
            logger.error(f'Pattern component validation failed: {e}')
            raise ValidationError(f'Pattern validation error: {e}')

    def duplicate_pattern(
            self,
            pattern_id: int,
            new_name: Optional[str] = None,
            increment_complexity: bool = True
    ) -> Pattern:
        """
        Advanced pattern duplication with optional complexity adjustment.

        Args:
            pattern_id (int): ID of the original pattern
            new_name (Optional[str]): Optional new name for the duplicated pattern
            increment_complexity (bool): Slightly increase complexity of duplicated pattern

        Returns:
            Pattern: Newly created pattern
        """
        try:
            # Retrieve original pattern
            original_pattern = self._pattern_repository.get_by_id(pattern_id)

            # Create duplicated pattern
            duplicated_pattern = Pattern(
                name=new_name or f'{original_pattern.name} (Copy)',
                skill_level=original_pattern.skill_level,
                complexity=(
                    original_pattern.complexity * 1.1
                    if increment_complexity
                    else original_pattern.complexity
                )
            )

            # Duplicate components
            for component in original_pattern.components:
                duplicated_component = component.__class__(
                    name=component.name,
                    material_type=component.material_type,
                    quantity=component.quantity
                )
                duplicated_pattern.components.append(duplicated_component)

            # Add and return the duplicated pattern
            return self._pattern_repository.add(duplicated_pattern)

        except Exception as e:
            logger.error(f'Pattern duplication failed: {e}')
            raise ApplicationError(f'Could not duplicate pattern: {e}')

    def generate_complexity_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report on pattern complexity distribution.

        Returns:
            Dict[str, Any]: Complexity analysis report
        """
        try:
            # Retrieve all patterns
            all_patterns = self._pattern_repository.search_by_criteria({})

            # Initialize complexity report
            complexity_report: Dict[str, Any] = {
                'total_patterns': len(all_patterns),
                'complexity_distribution': {
                    'low': 0,
                    'medium': 0,
                    'high': 0,
                    'very_high': 0
                },
                'avg_complexity': 0,
                'median_complexity': 0
            }

            # Calculate complexity metrics
            complexities = [p.complexity for p in all_patterns]

            # Calculate average complexity
            complexity_report['avg_complexity'] = (
                sum(complexities) / len(complexities)
                if complexities
                else 0
            )

            # Calculate median complexity
            sorted_complexities = sorted(complexities)
            mid = len(sorted_complexities) // 2
            complexity_report['median_complexity'] = (
                sorted_complexities[mid]
                if len(sorted_complexities) % 2
                else (sorted_complexities[mid - 1] + sorted_complexities[mid]) / 2
            )

            # Categorize complexity distribution
            for complexity in complexities:
                if complexity < 3:
                    complexity_report['complexity_distribution']['low'] += 1
                elif complexity < 6:
                    complexity_report['complexity_distribution']['medium'] += 1
                elif complexity < 9:
                    complexity_report['complexity_distribution']['high'] += 1
                else:
                    complexity_report['complexity_distribution']['very_high'] += 1

            return complexity_report

        except Exception as e:
            logger.error(f'Error generating complexity report: {e}')
            raise ApplicationError(f'Could not generate complexity report: {e}')