# database/mapper_diagnostics.py
import logging
import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.orm import relationship


def diagnose_mapper_configuration(model_class):
    """
    Diagnose SQLAlchemy mapper configuration for a given model class.

    Args:
        model_class: The SQLAlchemy model class to diagnose

    Returns:
        dict: Detailed diagnostic information about the model's mapper
    """
    logger = logging.getLogger(__name__)

    try:
        # Get the mapper for the model
        mapper = inspect(model_class)

        # Collect mapper properties
        properties = {
            'all_properties': [prop.key for prop in mapper.iterate_properties],
            'mapped_columns': [col.key for col in mapper.columns],
            'relationships': {}
        }

        # Detailed relationship information
        for prop in mapper.relationships:
            properties['relationships'][prop.key] = {
                'target': str(prop.target),
                'back_populates': getattr(prop, 'back_populates', None),
                'cascade': prop.cascade,
                'direction': prop.direction.name
            }

        return properties

    except Exception as e:
        logger.error(f"Error diagnosing mapper for {model_class.__name__}: {e}")
        return {"error": str(e)}


def find_problematic_backrefs():
    """
    Scan all Base subclasses to find potential backref configuration issues.

    Returns:
        dict: Mapping of models with potential backref problems
    """
    from database.models.base import Base
    logger = logging.getLogger(__name__)

    problematic_models = {}

    for model in Base.__subclasses__():
        try:
            # Get all relationships for the model
            relationships = getattr(model, '__mapper_args__', {}).get('properties', {})

            for rel_name, rel_config in relationships.items():
                # Check for backrefs that might not be properly configured
                if isinstance(rel_config, relationship):
                    back_populates = getattr(rel_config, 'back_populates', None)
                    if back_populates:
                        try:
                            # Try to verify the back_populates relationship exists
                            target_class = rel_config.mapper.class_
                            if not hasattr(target_class, back_populates):
                                problematic_models[model.__name__] = {
                                    'relationship': rel_name,
                                    'back_populates': back_populates,
                                    'target_class': target_class.__name__
                                }
                        except Exception as e:
                            logger.warning(f"Error checking relationship for {model.__name__}.{rel_name}: {e}")

        except Exception as e:
            logger.error(f"Error processing model {model.__name__}: {e}")

    return problematic_models


def print_mapper_diagnostic_report():
    """
    Generate a comprehensive diagnostic report for all models.

    Prints detailed information about mapper configurations.
    """
    from database.models.base import Base
    logger = logging.getLogger(__name__)

    logger.info("===== SQLAlchemy Mapper Diagnostic Report =====")

    for model in Base.__subclasses__():
        try:
            logger.info(f"\nModel: {model.__name__}")
            diagnostics = diagnose_mapper_configuration(model)

            if 'error' in diagnostics:
                logger.error(f"Diagnostic Error: {diagnostics['error']}")
                continue

            logger.info("Columns:")
            for col in diagnostics['mapped_columns']:
                logger.info(f"  - {col}")

            logger.info("Relationships:")
            for rel_name, rel_details in diagnostics.get('relationships', {}).items():
                logger.info(f"  - {rel_name}: {rel_details}")

        except Exception as e:
            logger.error(f"Error processing model {model.__name__}: {e}")

    logger.info("\n===== Problematic Backrefs =====")
    problematic_refs = find_problematic_backrefs()
    if problematic_refs:
        for model, details in problematic_refs.items():
            logger.warning(f"Model {model}: {details}")
    else:
        logger.info("No problematic backrefs found.")


def clear_sqlalchemy_mappers():
    """
    Clear SQLAlchemy mappers to force a full reconfiguration.

    Use with caution - this should only be done during development/debugging.
    """
    from sqlalchemy.orm import clear_mappers
    from database.models.base import Base

    logger = logging.getLogger(__name__)
    logger.warning("Clearing all SQLAlchemy mappers")

    clear_mappers()
    # Ensure mappers are recreated
    Base.metadata.create_all(bind=sqlalchemy.create_engine('sqlite:///:memory:'))