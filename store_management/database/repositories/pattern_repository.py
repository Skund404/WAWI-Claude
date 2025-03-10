# database/repositories/pattern_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_, distinct

from database.models.pattern import Pattern
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import SkillLevel, ComponentType, ProjectType


class PatternRepository(BaseRepository[Pattern]):
    """Repository for pattern management operations.

    This repository provides methods for managing pattern data, including
    components, measurements, and relationships with materials and products.
    """

    def _get_model_class(self) -> Type[Pattern]:
        """Return the model class this repository manages.

        Returns:
            The Pattern model class
        """
        return Pattern

    # Basic query methods

    def get_by_name(self, name: str) -> Optional[Pattern]:
        """Get pattern by exact name match.

        Args:
            name: Pattern name to search for

        Returns:
            Pattern instance or None if not found
        """
        self.logger.debug(f"Getting pattern with name '{name}'")
        return self.session.query(Pattern).filter(Pattern.name == name).first()

    def get_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        """Get patterns by skill level.

        Args:
            skill_level: Skill level to filter by

        Returns:
            List of pattern instances with the specified skill level
        """
        self.logger.debug(f"Getting patterns with skill level '{skill_level.value}'")
        return self.session.query(Pattern).filter(Pattern.skill_level == skill_level).all()

    def get_by_type(self, pattern_type: ProjectType) -> List[Pattern]:
        """Get patterns by project type.

        Args:
            pattern_type: Project type to filter by

        Returns:
            List of pattern instances with the specified type
        """
        self.logger.debug(f"Getting patterns with type '{pattern_type.value}'")
        if hasattr(Pattern, 'type'):
            return self.session.query(Pattern).filter(Pattern.type == pattern_type).all()
        else:
            # If Pattern doesn't have a type attribute, try to filter by related products
            from database.models.product import Product
            from database.models.relationship_tables import product_pattern_table

            patterns = self.session.query(Pattern). \
                join(product_pattern_table). \
                join(Product). \
                filter(Product.type == pattern_type).all()

            return list(set(patterns))  # Remove duplicates

    def search_patterns(self, search_term: str) -> List[Pattern]:
        """Search patterns by term in name and description.

        Args:
            search_term: Term to search for in name and description

        Returns:
            List of matching pattern instances
        """
        self.logger.debug(f"Searching patterns with term '{search_term}'")
        return self.session.query(Pattern).filter(
            or_(
                Pattern.name.ilike(f"%{search_term}%"),
                Pattern.description.ilike(f"%{search_term}%") if hasattr(Pattern, 'description') else False
            )
        ).all()

    # Component-related methods

    def get_pattern_with_components(self, pattern_id: int) -> Dict[str, Any]:
        """Get pattern with all components.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Pattern dictionary with components

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Getting pattern {pattern_id} with components")
        from database.models.component import Component

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # Get pattern data
        result = pattern.to_dict()

        # Get components
        components = pattern.components
        result['components'] = [component.to_dict() for component in components]

        return result

    def add_component_to_pattern(self, pattern_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a component to a pattern.

        Args:
            pattern_id: ID of the pattern
            component_data: Component data dictionary

        Returns:
            Updated pattern with components

        Raises:
            EntityNotFoundError: If pattern not found
            ValidationError: If validation fails
        """
        self.logger.debug(f"Adding component to pattern {pattern_id}")
        from database.models.component import Component

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        try:
            # Create new component
            component = Component(**component_data)
            self.session.add(component)
            self.session.flush()  # Get component ID

            # Add to pattern
            pattern.components.append(component)
            self.session.flush()

            # Return updated pattern with components
            return self.get_pattern_with_components(pattern_id)
        except Exception as e:
            self.logger.error(f"Error adding component to pattern: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to add component to pattern: {str(e)}")

    def remove_component_from_pattern(self, pattern_id: int, component_id: int) -> Dict[str, Any]:
        """Remove a component from a pattern.

        Args:
            pattern_id: ID of the pattern
            component_id: ID of the component to remove

        Returns:
            Updated pattern with components

        Raises:
            EntityNotFoundError: If pattern or component not found
        """
        self.logger.debug(f"Removing component {component_id} from pattern {pattern_id}")
        from database.models.component import Component

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        component = self.session.query(Component).get(component_id)
        if not component:
            raise EntityNotFoundError(f"Component with ID {component_id} not found")

        try:
            # Remove component from pattern
            pattern.components.remove(component)
            self.session.flush()

            # Return updated pattern with components
            return self.get_pattern_with_components(pattern_id)
        except ValueError:
            raise EntityNotFoundError(f"Component {component_id} not found in pattern {pattern_id}")
        except Exception as e:
            self.logger.error(f"Error removing component from pattern: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to remove component from pattern: {str(e)}")

    # Material usage methods

    def get_pattern_material_requirements(self, pattern_id: int) -> Dict[str, Any]:
        """Get material requirements for a pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Dictionary with pattern and material requirements

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Getting material requirements for pattern {pattern_id}")
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial
        from database.models.material import Material

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # Get pattern data
        result = pattern.to_dict()

        # Get components with materials
        components = []
        materials_by_id = {}

        for component in pattern.components:
            component_dict = component.to_dict()
            component_dict['materials'] = []

            # Get component materials
            component_materials = self.session.query(ComponentMaterial). \
                filter(ComponentMaterial.component_id == component.id).all()

            for cm in component_materials:
                material = self.session.query(Material).get(cm.material_id)
                if material:
                    material_dict = material.to_dict()
                    material_dict['quantity'] = cm.quantity
                    component_dict['materials'].append(material_dict)

                    # Accumulate total material requirements
                    if cm.material_id not in materials_by_id:
                        materials_by_id[cm.material_id] = {
                            **material_dict,
                            'quantity': cm.quantity,
                            'used_in_components': [component.id]
                        }
                    else:
                        materials_by_id[cm.material_id]['quantity'] += cm.quantity
                        materials_by_id[cm.material_id]['used_in_components'].append(component.id)

            components.append(component_dict)

        result['components'] = components
        result['material_requirements'] = list(materials_by_id.values())

        return result

    # Product association methods

    def get_associated_products(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get products associated with a pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of associated product dictionaries

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Getting products associated with pattern {pattern_id}")
        from database.models.product import Product
        from database.models.relationship_tables import product_pattern_table

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        # Query products associated with the pattern
        products = self.session.query(Product). \
            join(product_pattern_table). \
            filter(product_pattern_table.c.pattern_id == pattern_id).all()

        return [product.to_dict() for product in products]

    def associate_product(self, pattern_id: int, product_id: int) -> Dict[str, Any]:
        """Associate a product with a pattern.

        Args:
            pattern_id: ID of the pattern
            product_id: ID of the product

        Returns:
            Pattern with updated product associations

        Raises:
            EntityNotFoundError: If pattern or product not found
        """
        self.logger.debug(f"Associating product {product_id} with pattern {pattern_id}")
        from database.models.product import Product

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        product = self.session.query(Product).get(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        # Check if association already exists
        if product in pattern.products:
            return {
                'pattern': pattern.to_dict(),
                'products': [p.to_dict() for p in pattern.products]
            }

        # Add association
        pattern.products.append(product)
        self.session.flush()

        return {
            'pattern': pattern.to_dict(),
            'products': [p.to_dict() for p in pattern.products]
        }

    def disassociate_product(self, pattern_id: int, product_id: int) -> Dict[str, Any]:
        """Remove association between a pattern and a product.

        Args:
            pattern_id: ID of the pattern
            product_id: ID of the product

        Returns:
            Pattern with updated product associations

        Raises:
            EntityNotFoundError: If pattern or product not found
        """
        self.logger.debug(f"Disassociating product {product_id} from pattern {pattern_id}")
        from database.models.product import Product

        pattern = self.get_by_id(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        product = self.session.query(Product).get(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        # Remove association
        try:
            pattern.products.remove(product)
            self.session.flush()
        except ValueError:
            raise EntityNotFoundError(f"Product {product_id} not associated with pattern {pattern_id}")

        return {
            'pattern': pattern.to_dict(),
            'products': [p.to_dict() for p in pattern.products]
        }

    # GUI-specific functionality

    def get_pattern_dashboard_data(self) -> Dict[str, Any]:
        """Get data for pattern dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting pattern dashboard data")

        # Count by skill level
        skill_counts = self.session.query(
            Pattern.skill_level,
            func.count().label('count')
        ).group_by(Pattern.skill_level).all()

        skill_data = {level.value: count for level, count in skill_counts}

        # Count by project type (if applicable)
        type_data = {}
        if hasattr(Pattern, 'type'):
            type_counts = self.session.query(
                Pattern.type,
                func.count().label('count')
            ).group_by(Pattern.type).all()

            type_data = {type_.value: count for type_, count in type_counts}

        # Get component type distribution
        from database.models.component import Component

        component_type_counts = self.session.query(
            Component.component_type,
            func.count().label('count')
        ).join(
            Pattern.components
        ).group_by(Component.component_type).all()

        component_type_data = {type_.value: count for type_, count in component_type_counts}

        # Get pattern usage in products
        from database.models.product import Product
        from database.models.relationship_tables import product_pattern_table

        pattern_usage = self.session.query(
            Pattern.id,
            Pattern.name,
            func.count(distinct(product_pattern_table.c.product_id)).label('product_count')
        ).outerjoin(
            product_pattern_table
        ).group_by(
            Pattern.id,
            Pattern.name
        ).order_by(
            func.count(distinct(product_pattern_table.c.product_id)).desc()
        ).limit(10).all()

        pattern_usage_data = [{
            'pattern_id': pattern_id,
            'pattern_name': pattern_name,
            'product_count': product_count
        } for pattern_id, pattern_name, product_count in pattern_usage]

        # Return combined data
        return {
            'total_patterns': self.count(),
            'skill_level_counts': skill_data,
            'type_counts': type_data,
            'component_type_counts': component_type_data,
            'most_used_patterns': pattern_usage_data,
            'recent_patterns': [p.to_dict() for p in self.get_recent_patterns()]
        }

    def get_recent_patterns(self, limit: int = 5) -> List[Pattern]:
        """Get recently created patterns.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of recent pattern instances
        """
        if hasattr(Pattern, 'created_at'):
            return self.session.query(Pattern). \
                order_by(Pattern.created_at.desc()).limit(limit).all()
        else:
            return self.session.query(Pattern).limit(limit).all()

    def filter_patterns_for_gui(self,
                                search_term: Optional[str] = None,
                                skill_levels: Optional[List[SkillLevel]] = None,
                                pattern_types: Optional[List[str]] = None,
                                sort_by: str = 'name',
                                sort_dir: str = 'asc',
                                page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate patterns for GUI display.

        Args:
            search_term: Optional search term
            skill_levels: Optional list of skill levels to filter by
            pattern_types: Optional list of pattern types to filter by
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(f"Filtering patterns for GUI: search='{search_term}', levels={skill_levels}")

        # Start with base query
        query = self.session.query(Pattern)

        # Apply search filter if provided
        if search_term:
            query = query.filter(
                or_(
                    Pattern.name.ilike(f"%{search_term}%"),
                    Pattern.description.ilike(f"%{search_term}%") if hasattr(Pattern, 'description') else False
                )
            )

        # Apply skill level filter if provided
        if skill_levels:
            query = query.filter(Pattern.skill_level.in_(skill_levels))

        # Apply pattern type filter if provided and applicable
        if pattern_types and hasattr(Pattern, 'type'):
            query = query.filter(Pattern.type.in_(pattern_types))

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Pattern.name.desc())
            else:
                query = query.order_by(Pattern.name.asc())
        elif sort_by == 'skill_level':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Pattern.skill_level.desc())
            else:
                query = query.order_by(Pattern.skill_level.asc())
        elif sort_by == 'created_at' and hasattr(Pattern, 'created_at'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Pattern.created_at.desc())
            else:
                query = query.order_by(Pattern.created_at.asc())
        elif sort_by == 'type' and hasattr(Pattern, 'type'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Pattern.type.desc())
            else:
                query = query.order_by(Pattern.type.asc())
        else:
            # Default to name
            query = query.order_by(Pattern.name.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query and get component counts
        patterns = query.all()

        # Get component counts for each pattern
        from database.models.component import Component

        pattern_ids = [p.id for p in patterns]
        component_counts = {}

        if pattern_ids:
            count_query = self.session.query(
                Component.pattern_id,
                func.count().label('count')
            ).filter(Component.pattern_id.in_(pattern_ids)). \
                group_by(Component.pattern_id).all()

            component_counts = {pattern_id: count for pattern_id, count in count_query}

        # Format results
        items = []
        for pattern in patterns:
            pattern_dict = pattern.to_dict()
            pattern_dict['component_count'] = component_counts.get(pattern.id, 0)
            items.append(pattern_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }

    def export_pattern_data(self, pattern_id: int, format: str = "json") -> Dict[str, Any]:
        """Export pattern data with components and materials.

        Args:
            pattern_id: ID of the pattern to export
            format: Export format ("json", "csv", etc.)

        Returns:
            Dict with export data and metadata

        Raises:
            EntityNotFoundError: If pattern not found
        """
        self.logger.debug(f"Exporting pattern {pattern_id} data in {format} format")

        # Get pattern with all related data
        pattern_data = self.get_pattern_material_requirements(pattern_id)

        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'pattern_id': pattern_id,
            'pattern_name': pattern_data.get('name', 'Unknown Pattern')
        }

        return {
            'data': pattern_data,
            'metadata': metadata
        }