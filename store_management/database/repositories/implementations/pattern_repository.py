from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from sqlalchemy import Index, and_
from sqlalchemy.orm import joinedload
from functools import lru_cache
from cachetools import SimpleCache
from typing import Dict, Any, List

"""
Optimized Pattern Repository Implementation for Leatherworking Store Management System.

Includes performance optimizations, caching, and indexed queries.
"""
logger = get_logger(__name__)

class PatternRepository(IPatternRepository, IBaseRepository):
    """
    Optimized Pattern Repository with caching and performance enhancements.
    """

    @inject(MaterialService)
    def __init__(self, session: Session):
        """
        Initialize the Pattern Repository with database session and caching.

        Args:
        session (Session): SQLAlchemy database session
        """
        self._session = session
        self._create_indexes()
        self._cache = SimpleCache() if PATTERN_CONFIG.cache_enabled else None

    @inject(MaterialService)
    def _create_indexes(self):
        """
        Create database indexes for performance optimization.
        """
        try:
            Index('idx_pattern_skill_level', Pattern.skill_level)
            Index('idx_pattern_name', Pattern.name)
            Index('idx_pattern_complexity', Pattern.complexity)
            self._session.commit()
        except Exception as e:
            logger.warning(f'Could not create indexes: {e}')
            self._session.rollback()

    @lru_cache(maxsize=PATTERN_CONFIG.cache_max_size)
    @inject(MaterialService)
    def get_by_id(self, pattern_id: int) -> Pattern:
        """
        Retrieve a pattern by its unique identifier with caching and prefetching.

        Args:
        pattern_id (int): Unique identifier for the pattern

        Returns:
        Pattern: Retrieved pattern instance

        Raises:
        ApplicationError: If pattern is not found
        """
        if self._cache:
            cached_pattern = self._cache.get(f'pattern_{pattern_id}')
            if cached_pattern:
                return cached_pattern

        try:
            pattern = self._session.query(Pattern).options(joinedload(Pattern.components)).filter(Pattern.id == pattern_id).first()
            if not pattern:
                raise ApplicationError(f'Pattern with ID {pattern_id} not found')

            if self._cache:
                self._cache.set(f'pattern_{pattern_id}', pattern, timeout=PATTERN_CONFIG.cache_ttl_seconds)
            return pattern
        except Exception as e:
            logger.error(f'Error retrieving pattern: {e}')
            raise ApplicationError(f'Could not retrieve pattern: {e}')

    @inject(MaterialService)
    def get_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        """
        Retrieve patterns matching a specific skill level with pagination and caching.

        Args:
        skill_level (SkillLevel): Skill level enum

        Returns:
        List[Pattern]: List of patterns matching the skill level
        """
        cache_key = f'patterns_skill_{skill_level}'
        if self._cache:
            cached_patterns = self._cache.get(cache_key)
            if cached_patterns:
                return cached_patterns

        try:
            patterns = self._session.query(Pattern).filter(Pattern.skill_level == skill_level).options(joinedload(Pattern.components)).limit(PATTERN_CONFIG.query_prefetch_limit).all()
            if self._cache:
                self._cache.set(cache_key, patterns, timeout=PATTERN_CONFIG.cache_ttl_seconds)
            return patterns
        except Exception as e:
            logger.error(f'Error retrieving patterns by skill level: {e}')
            return []

    @inject(MaterialService)
    def search_by_criteria(self, criteria: Dict[str, Any]) -> List[Pattern]:
        """
        Search patterns using flexible criteria with performance optimizations.

        Args:
        criteria (Dict[str, Any]): Search parameters

        Returns:
        List[Pattern]: Matching patterns
        """
        cache_key = f'pattern_search_{hash(frozenset(criteria.items()))}'
        if self._cache:
            cached_results = self._cache.get(cache_key)
            if cached_results:
                return cached_results

        try:
            query = self._session.query(Pattern)
            conditions = []
            if 'name' in criteria:
                conditions.append(Pattern.name.ilike(f"%{criteria['name']}%"))
            if 'skill_level' in criteria:
                conditions.append(Pattern.skill_level == criteria['skill_level'])
            if 'min_complexity' in criteria:
                conditions.append(Pattern.complexity >= criteria['min_complexity'])

            if conditions:
                query = query.filter(and_(*conditions))
            results = query.options(joinedload(Pattern.components)).limit(PATTERN_CONFIG.query_prefetch_limit).all()

            if self._cache:
                self._cache.set(cache_key, results, timeout=PATTERN_CONFIG.cache_ttl_seconds)
            return results
        except Exception as e:
            logger.error(f'Error searching patterns: {e}')
            return []

    @inject(MaterialService)
    def add(self, pattern: Pattern) -> Pattern:
        """
        Add a new pattern to the database with cache invalidation.

        Args:
        pattern (Pattern): Pattern to be added

        Returns:
        Pattern: Added pattern with assigned ID

        Raises:
        ValidationError: If pattern validation fails
        """
        try:
            self._validate_pattern(pattern)
            self._session.add(pattern)
            self._session.commit()

            if self._cache:
                self._cache.delete_many([
                    f'patterns_skill_{pattern.skill_level}',
                    'all_patterns'
                ])
            return pattern
        except ValidationError as ve:
            logger.warning(f'Pattern validation failed: {ve}')
            raise
        except Exception as e:
            self._session.rollback()
            logger.error(f'Error adding pattern: {e}')
            raise ApplicationError(f'Could not add pattern: {e}')

    @inject(MaterialService)
    def _validate_pattern(self, pattern: Pattern) -> None:
        """
        Validate pattern data before database operations with enhanced complexity checks.

        Args:
        pattern (Pattern): Pattern to validate

        Raises:
        ValidationError: If validation fails
        """
        errors = []
        if not pattern.name or len(pattern.name) < 3:
            errors.append('Pattern name must be at least 3 characters long')

        complexity_calc = self._calculate_pattern_complexity(pattern)
        if complexity_calc < 0 or complexity_calc > 10:
            errors.append(f'Calculated complexity {complexity_calc} is out of acceptable range')

        if pattern.skill_level is None:
            errors.append('Skill level must be specified')

        if errors:
            raise ValidationError('\n'.join(errors))

    @inject(MaterialService)
    def _calculate_pattern_complexity(self, pattern: Pattern) -> float:
        """
        Calculate pattern complexity using configurable weights.

        Args:
        pattern (Pattern): Pattern to assess

        Returns:
        float: Calculated complexity score
        """
        config = PATTERN_CONFIG
        components_complexity = len(pattern.components) * config.complexity_components_weight

        skill_level_map = {
            SkillLevel.BEGINNER: 1,
            SkillLevel.INTERMEDIATE: 5,
            SkillLevel.ADVANCED: 8,
            SkillLevel.EXPERT: 10
        }
        skill_level_complexity = skill_level_map.get(pattern.skill_level, 1) * config.complexity_skill_level_weight

        material_types = set(component.material_type for component in pattern.components)
        material_diversity = len(material_types) * config.complexity_material_diversity_weight

        return (components_complexity + skill_level_complexity + material_diversity)