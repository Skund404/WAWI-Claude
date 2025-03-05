# utils/enhanced_relationship_strategy.py
"""
Advanced Relationship Configuration and Management Strategy

Provides robust mechanisms for defining and managing SQLAlchemy model relationships
with comprehensive support for circular dependencies and lazy loading.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from enum import Enum, auto
from sqlalchemy.orm import relationship, RelationshipProperty
from sqlalchemy import ForeignKey, Column, inspect
from sqlalchemy.orm.relationships import RelationshipProperty as SQLARelationship

from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import,
    register_relationship
)


class RelationshipLoadingStrategy(Enum):
    """
    Comprehensive enum for relationship loading strategies.
    """
    LAZY = auto()  # Default lazy loading
    EAGER = auto()  # Immediate loading
    SUBQUERY = auto()  # Subquery loading
    SELECTIN = auto()  # Select-in loading
    JOINED = auto()  # Joined loading


class RelationshipConfiguration:
    """
    Advanced relationship configuration utility for SQLAlchemy models.
    """

    @staticmethod
    def _resolve_loading_strategy(strategy: RelationshipLoadingStrategy) -> str:
        """
        Convert enum loading strategy to SQLAlchemy lazy loading configuration.

        Args:
            strategy: Relationship loading strategy

        Returns:
            SQLAlchemy lazy loading configuration string
        """
        strategy_map = {
            RelationshipLoadingStrategy.LAZY: 'select',
            RelationshipLoadingStrategy.EAGER: 'joined',
            RelationshipLoadingStrategy.SUBQUERY: 'subquery',
            RelationshipLoadingStrategy.SELECTIN: 'selectin',
            RelationshipLoadingStrategy.JOINED: 'joined'
        }
        return strategy_map.get(strategy, 'select')

    @classmethod
    def configure_relationship(
            cls,
            source_model: Type,
            target_model: Union[Type, str],
            relationship_name: str,
            back_populates: Optional[str] = None,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY,
            cascade: Optional[str] = None,
            foreign_keys: Optional[List[Column]] = None,
            use_lazy_import: bool = True,
            secondary: Optional[Any] = None,
            uselist: bool = True
    ) -> RelationshipProperty:
        """
        Configure a comprehensive SQLAlchemy relationship with advanced options.

        Args:
            source_model: The model class defining the relationship
            target_model: Target model for the relationship
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            loading_strategy: Relationship loading strategy
            cascade: Cascade configuration
            foreign_keys: Optional foreign key columns
            use_lazy_import: Whether to use lazy import for the target model
            secondary: Association table for many-to-many relationships
            uselist: Whether the relationship is a collection

        Returns:
            Configured SQLAlchemy relationship
        """
        # Resolve lazy import if needed
        if use_lazy_import and isinstance(target_model, str):
            target_model = lazy_import(target_model)

        # Default cascade configuration
        if cascade is None:
            cascade = "save-update, merge"

        # Resolve loading strategy
        lazy_config = cls._resolve_loading_strategy(loading_strategy)

        # Build relationship configuration
        relationship_config = {
            'back_populates': back_populates,
            'lazy': lazy_config,
            'cascade': cascade,
            'uselist': uselist
        }

        # Add foreign keys if specified
        if foreign_keys:
            relationship_config['foreign_keys'] = foreign_keys

        # Add secondary table for many-to-many
        if secondary:
            relationship_config['secondary'] = secondary

        # Create and register the relationship
        relationship_prop = relationship(target_model, **relationship_config)

        # Register the relationship for resolution
        register_relationship(
            f"{source_model.__module__}.{source_model.__name__}",
            relationship_name,
            f"{target_model.__module__}.{target_model.__name__}"
        )

        return relationship_prop

    @classmethod
    def create_foreign_key(
            cls,
            source_model: Type,
            target_model: Union[Type, str],
            nullable: bool = True,
            use_lazy_import: bool = True,
            custom_column_name: Optional[str] = None
    ) -> Column:
        """
        Create a foreign key column for a relationship.

        Args:
            source_model: The source model class
            target_model: Target model for the foreign key
            nullable: Whether the foreign key can be null
            use_lazy_import: Whether to use lazy import for the target model
            custom_column_name: Optional custom name for the foreign key column

        Returns:
            SQLAlchemy foreign key column
        """
        # Resolve lazy import if needed
        if use_lazy_import and isinstance(target_model, str):
            target_model = lazy_import(target_model)

        # Determine column name
        if custom_column_name:
            column_name = custom_column_name
        else:
            # Use standard naming convention
            column_name = f"{target_model.__name__.lower()}_id"

        # Create and return foreign key column
        return Column(
            column_name,
            ForeignKey(f"{target_model.__tablename__}.id"),
            nullable=nullable
        )

    @classmethod
    def define_many_to_one_relationship(
            cls,
            source_model: Type,
            target_model: Union[Type, str],
            relationship_name: str,
            back_populates: Optional[str] = None,
            nullable: bool = True,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY,
            use_lazy_import: bool = True
    ) -> Tuple[Column, RelationshipProperty]:
        """
        Define a standard many-to-one relationship with comprehensive configuration.

        Args:
            source_model: The source model class
            target_model: Target model for the relationship
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            nullable: Whether the foreign key can be null
            loading_strategy: Relationship loading strategy
            use_lazy_import: Whether to use lazy import for the target model

        Returns:
            Tuple of (foreign key column, relationship property)
        """
        # Create foreign key column
        foreign_key = cls.create_foreign_key(
            source_model,
            target_model,
            nullable=nullable,
            use_lazy_import=use_lazy_import
        )

        # Add foreign key to source model
        setattr(source_model, foreign_key.name, foreign_key)

        # Configure relationship
        relationship_prop = cls.configure_relationship(
            source_model,
            target_model,
            relationship_name,
            back_populates,
            loading_strategy,
            foreign_keys=[foreign_key],
            uselist=False  # Many-to-one is not a list
        )

        # Set relationship on source model
        setattr(source_model, relationship_name, relationship_prop)

        return foreign_key, relationship_prop

    @classmethod
    def define_many_to_many_relationship(
            cls,
            source_model: Type,
            target_model: Union[Type, str],
            association_table: Any,
            relationship_name: str,
            back_populates: Optional[str] = None,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY,
            use_lazy_import: bool = True
    ) -> RelationshipProperty:
        """
        Define a many-to-many relationship using an association table.

        Args:
            source_model: The source model class
            target_model: Target model for the relationship
            association_table: SQLAlchemy Table for the many-to-many relationship
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            loading_strategy: Relationship loading strategy
            use_lazy_import: Whether to use lazy import for the target model

        Returns:
            Configured relationship property
        """
        # Configure many-to-many relationship
        relationship_prop = cls.configure_relationship(
            source_model,
            target_model,
            relationship_name,
            back_populates,
            loading_strategy,
            secondary=association_table,
            uselist=True  # Many-to-many is always a list
        )

        # Set relationship on source model
        setattr(source_model, relationship_name, relationship_prop)

        return relationship_prop


# Example usage demonstrating relationship configuration strategies
if __name__ == "__main__":
    from sqlalchemy import Column, Integer, String, Table, MetaData
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()


    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)


    class Project(Base):
        __tablename__ = 'projects'
        id = Column(Integer, primary_key=True)
        name = Column(String)

        # Demonstrate relationship configuration
        user_id, user = RelationshipConfiguration.define_many_to_one_relationship(
            source_model=Project,
            target_model=User,
            relationship_name='user',
            back_populates='projects',
            nullable=False,
            loading_strategy=RelationshipLoadingStrategy.EAGER
        )

        # Define many-to-many relationship
        metadata = MetaData()
        project_tags = Table('project_tags', metadata,
                             Column('project_id', Integer, ForeignKey('projects.id')),
                             Column('tag_id', Integer, ForeignKey('tags.id'))
                             )

        tags = RelationshipConfiguration.define_many_to_many_relationship(
            source_model=Project,
            target_model='Tag',  # Demonstrates lazy import
            association_table=project_tags,
            relationship_name='tags',
            back_populates='projects',
            loading_strategy=RelationshipLoadingStrategy.SELECTIN
        )


    # Register lazy import for Tag
    register_lazy_import('database.models.tag.Tag')

    print("Relationship configuration example complete.")