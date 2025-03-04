# database/relationship_diagnostics.py
"""
Advanced diagnostic utility for SQLAlchemy model relationships.
"""

import logging
import importlib
import inspect
from typing import Dict, Any, List, Type

import sqlalchemy
from sqlalchemy.orm import relationship, class_mapper
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class RelationshipDiagnostics:
    """
    Comprehensive diagnostic tool for analyzing SQLAlchemy model relationships.
    """

    @classmethod
    def scan_all_models(cls) -> Dict[str, Dict[str, Any]]:
        """
        Scan all models in the application for relationship configurations.

        Returns:
            Dict of model relationships with detailed diagnostic information
        """
        from database.models.base import Base

        relationship_map = {}

        # Iterate through all Base subclasses
        for model in Base.__subclasses__():
            try:
                model_relationships = cls.analyze_model_relationships(model)
                if model_relationships:
                    relationship_map[model.__name__] = model_relationships
            except Exception as e:
                logger.error(f"Error analyzing relationships for {model.__name__}: {e}")

        return relationship_map

    @classmethod
    def analyze_model_relationships(cls, model: Type) -> Dict[str, Any]:
        """
        Analyze relationships for a specific model.

        Args:
            model (Type): SQLAlchemy model class to analyze

        Returns:
            Dict of relationship details
        """
        relationships = {}

        try:
            # Use SQLAlchemy's inspection to get mapper properties
            mapper = class_mapper(model)

            for prop in mapper.relationships:
                relationship_info = {
                    'key': prop.key,
                    'target': str(prop.target),
                    'direction': prop.direction.name,
                    'back_populates': getattr(prop, 'back_populates', None),
                    'cascade': prop.cascade,
                    'lazy': prop.lazy
                }
                relationships[prop.key] = relationship_info

        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error analyzing {model.__name__} relationships: {e}")
        except Exception as e:
            logger.error(f"Unexpected error analyzing {model.__name__} relationships: {e}")

        return relationships

    @classmethod
    def find_orphaned_relationships(cls) -> Dict[str, List[str]]:
        """
        Find relationships that might be orphaned or misconfigured.

        Returns:
            Dict of models with potentially orphaned relationships
        """
        orphaned_relationships = {}
        relationship_map = cls.scan_all_models()

        for model_name, relationships in relationship_map.items():
            orphaned = []
            for rel_name, rel_details in relationships.items():
                # Check for relationships without back_populates
                if not rel_details.get('back_populates'):
                    orphaned.append(rel_name)

                # Check for relationships pointing to non-existent targets
                try:
                    target = rel_details['target']
                    # You might want to add more sophisticated target validation
                    if 'products' in target.lower():
                        orphaned.append(rel_name)
                except Exception:
                    orphaned.append(rel_name)

            if orphaned:
                orphaned_relationships[model_name] = orphaned

        return orphaned_relationships

    @classmethod
    def generate_diagnostic_report(cls) -> str:
        """
        Generate a comprehensive diagnostic report of model relationships.

        Returns:
            Formatted diagnostic report as a string
        """
        report = ["SQLAlchemy Relationship Diagnostic Report", "=" * 50]

        # Scan all models
        relationship_map = cls.scan_all_models()

        # Detailed model relationships
        report.append("\nModel Relationships:")
        for model_name, relationships in relationship_map.items():
            report.append(f"\n{model_name}:")
            for rel_name, details in relationships.items():
                report.append(f"  - {rel_name}: {details}")

        # Orphaned relationships
        orphaned = cls.find_orphaned_relationships()
        if orphaned:
            report.append("\nOrphaned Relationships:")
            for model, rels in orphaned.items():
                report.append(f"  {model}: {rels}")

        return "\n".join(report)

    @classmethod
    def clear_relationship_caches(cls):
        """
        Attempt to clear SQLAlchemy relationship caches.
        """
        try:
            from sqlalchemy.orm import clear_mappers
            clear_mappers()
            logger.info("SQLAlchemy mappers cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing mappers: {e}")


def print_relationship_diagnostic_report():
    """
    Convenience function to print the full diagnostic report.
    """
    print(RelationshipDiagnostics.generate_diagnostic_report())


def diagnose_relationship_issues():
    """
    Comprehensive relationship issue diagnosis.
    """
    print("Performing Relationship Diagnostics...")

    # Clear existing caches
    RelationshipDiagnostics.clear_relationship_caches()

    # Generate and print report
    print_relationship_diagnostic_report()

    # Analyze orphaned relationships
    orphaned = RelationshipDiagnostics.find_orphaned_relationships()
    if orphaned:
        print("\nWarning: Orphaned Relationships Detected:")
        for model, relationships in orphaned.items():
            print(f"  {model}: {relationships}")