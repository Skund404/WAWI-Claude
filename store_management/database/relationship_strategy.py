# database/relationship_strategy.py
"""
Comprehensive Relationship Management Strategy for SQLAlchemy Models

This module provides a centralized approach to defining and managing
relationships between database models with advanced configuration options.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import relationship, RelationshipProperty
from sqlalchemy import ForeignKey, Column
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from enum import Enum, auto

T = TypeVar('T')


class RelationshipLoadingStrategy(Enum):
    """
    Enum defining different relationship loading strategies.
    """
    LAZY = auto()  # Default lazy loading
    EAGER = auto()  # Immediate loading
    JOINED = auto()  # Joined load strategy
    SUBQUERY = auto()  # Subquery load strategy
    SELECT_IN = auto()  # Select-in loading strategy


class RelationshipConfigurator:
    """
    Advanced relationship configuration utility for SQLAlchemy models.

    Provides a comprehensive set of tools for defining and managing
    model relationships with fine-grained control.
    """

    @staticmethod
    def configure_relationship(
            model_class: Type,
            related_model: Type,
            relationship_name: str,
            back_populates: Optional[str] = None,
            foreign_keys: Optional[List[Column]] = None,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY,
            cascade: Optional[str] = None,
            secondary: Optional[Any] = None,
            uselist: bool = True,
            lazy_import: bool = False
    ) -> RelationshipProperty:
        """
        Configures a comprehensive relationship between two models.

        Args:
            model_class: The source model class
            related_model: The related model class
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            foreign_keys: List of foreign key columns
            loading_strategy: Relationship loading strategy
            cascade: Cascade configuration string
            secondary: Association table for many-to-many relationships
            uselist: Whether the relationship is a collection
            lazy_import: Whether to use lazy import for the related model

        Returns:
            Configured SQLAlchemy relationship
        """
        # Determine loading strategy
        lazy_config = {
            RelationshipLoadingStrategy.LAZY: 'select',
            RelationshipLoadingStrategy.EAGER: 'joined',
            RelationshipLoadingStrategy.JOINED: 'joined',
            RelationshipLoadingStrategy.SUBQUERY: 'subquery',
            RelationshipLoadingStrategy.SELECT_IN: 'selectin'
        }.get(loading_strategy, 'select')

        # Default cascade configuration
        if cascade is None:
            cascade = "save-update, merge"

        # Handle lazy import if needed
        if lazy_import:
            from utils.circular_import_resolver import lazy_import
            related_model = lazy_import(f"{related_model.__module__}.{related_model.__name__}")

        # Construct relationship arguments
        relationship_args = {
            'back_populates': back_populates,
            'foreign_keys': foreign_keys,
            'lazy': lazy_config,
            'cascade': cascade,
            'secondary': secondary,
            'uselist': uselist
        }

        # Remove None values
        relationship_args = {k: v for k, v in relationship_args.items() if v is not None}

        # Create and return the relationship
        return relationship(related_model, **relationship_args)

    @staticmethod
    def create_foreign_key(
            model_class: Type,
            related_model: Type,
            nullable: bool = True
    ) -> Column:
        """
        Create a foreign key column for a relationship.

        Args:
            model_class: The source model class
            related_model: The related model class
            nullable: Whether the foreign key can be null

        Returns:
            SQLAlchemy foreign key column
        """
        return Column(
            f"{related_model.__name__.lower()}_id",
            ForeignKey(f"{related_model.__tablename__}.id"),
            nullable=nullable
        )

    @staticmethod
    def define_many_to_one_relationship(
            model_class: Type,
            related_model: Type,
            relationship_name: str,
            back_populates: Optional[str] = None,
            nullable: bool = True,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY
    ):
        """
        Define a standard many-to-one relationship.

        Args:
            model_class: The source model class
            related_model: The related model class
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            nullable: Whether the relationship can be null
            loading_strategy: Relationship loading strategy
        """
        # Create foreign key
        foreign_key = RelationshipConfigurator.create_foreign_key(
            model_class, related_model, nullable
        )

        # Add foreign key to model
        setattr(model_class, f"{related_model.__name__.lower()}_id", foreign_key)

        # Configure relationship
        relationship_config = RelationshipConfigurator.configure_relationship(
            model_class,
            related_model,
            relationship_name,
            back_populates,
            [foreign_key],
            loading_strategy
        )

        # Set relationship on model
        setattr(model_class, relationship_name, relationship_config)

    @staticmethod
    def define_many_to_many_relationship(
            model_class: Type,
            related_model: Type,
            association_table: Any,
            relationship_name: str,
            back_populates: Optional[str] = None,
            loading_strategy: RelationshipLoadingStrategy = RelationshipLoadingStrategy.LAZY
    ):
        """
        Define a many-to-many relationship using an association table.

        Args:
            model_class: The source model class
            related_model: The related model class
            association_table: SQLAlchemy Table for the many-to-many relationship
            relationship_name: Name of the relationship attribute
            back_populates: Name of the back-reference attribute
            loading_strategy: Relationship loading strategy
        """
        relationship_config = RelationshipConfigurator.configure_relationship(
            model_class,
            related_model,
            relationship_name,
            back_populates,
            secondary=association_table,
            loading_strategy=loading_strategy
        )

        # Set relationship on model
        setattr(model_class, relationship_name, relationship_config)


# Example usage demonstrating relationship configuration
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

        # Demonstrating relationship configuration
        RelationshipConfigurator.define_many_to_one_relationship(
            model_class=Project,
            related_model=User,
            relationship_name='owner',
            back_populates='projects',
            nullable=False,
            loading_strategy=RelationshipLoadingStrategy.EAGER
        )


    print("Relationship configuration example complete.")