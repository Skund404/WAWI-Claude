# database/models/factories.py
"""
Advanced Factory Classes for Creating Model Instances in Leatherworking Management System

This module provides factory classes that implement the Factory pattern
for creating instances of models with appropriate validation, defaults,
and relationship management. Each factory handles complex validation logic,
manages circular dependencies, and creates properly initialized objects.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Type, TypeVar, Union, Generic, cast

from sqlalchemy.exc import SQLAlchemyError

from database.models.base import Base, ModelValidationError
from database.models.enums import (
    ProjectStatus,
    ProjectType,
    SkillLevel,
    SaleStatus,
    PaymentStatus,
    ComponentType,
    HardwareType,
    HardwareMaterial,
    HardwareFinish,
    InventoryStatus,
    MeasurementUnit,
    MaterialType,
    LeatherType,
    LeatherFinish,
    QualityGrade,
    SupplierStatus,    # Added missing import
    ToolCategory,      # Added missing import
    TransactionType
)
from utils.circular_import_resolver import (
    lazy_import,
    register_lazy_import
)
from utils.enhanced_model_validator import ValidationError

# Type variable for generic typing
T = TypeVar('T', bound=Base)

# Setup logger
logger = logging.getLogger(__name__)

# Register lazy imports to resolve potential circular dependencies
register_lazy_import('Project', 'database.models.project', 'Project')
register_lazy_import('Pattern', 'database.models.pattern', 'Pattern')
register_lazy_import('Component', 'database.models.components', 'Component')
register_lazy_import('ProjectComponent', 'database.models.components', 'ProjectComponent')
register_lazy_import('PatternComponent', 'database.models.components', 'PatternComponent')
register_lazy_import('ComponentMaterial', 'database.models.components', 'ComponentMaterial')
register_lazy_import('ComponentLeather', 'database.models.components', 'ComponentLeather')
register_lazy_import('ComponentHardware', 'database.models.components', 'ComponentHardware')
register_lazy_import('ComponentTool', 'database.models.components', 'ComponentTool')
register_lazy_import('Sales', 'database.models.sales', 'Sales')
register_lazy_import('SalesItem', 'database.models.sales_item', 'SalesItem')
register_lazy_import('Hardware', 'database.models.hardware', 'Hardware')
register_lazy_import('Material', 'database.models.material', 'Material')
register_lazy_import('Leather', 'database.models.leather', 'Leather')
register_lazy_import('Tool', 'database.models.tool', 'Tool')
register_lazy_import('Product', 'database.models.product', 'Product')
register_lazy_import('Supplier', 'database.models.supplier', 'Supplier')

class BaseFactory(Generic[T]):
    """
    Base factory class with common functionality for all model factories.

    Provides common creation and validation logic, handling circular dependencies
    and proper initialization of model instances.
    """

    @classmethod
    def create(cls, data: Dict[str, Any]) -> T:
        """
        Create a model instance with comprehensive validation.

        Args:
            data: Dictionary containing model attributes

        Returns:
            Created model instance

        Raises:
            ModelValidationError: If creation fails
        """
        try:
            # Get model class (implemented by subclasses)
            model_class = cls._get_model_class()

            # Pre-process input data
            processed_data = cls._preprocess_data(data)

            # Create and return model instance
            logger.debug(f"Creating {model_class.__name__} instance with data: {processed_data}")
            instance = model_class(**processed_data)

            # Run any post-creation steps
            cls._post_process_instance(instance, data)

            return instance

        except (SQLAlchemyError, ValidationError, ValueError, KeyError) as e:
            error_msg = f"Failed to create {cls.__name__.replace('Factory', '')}: {e}"
            logger.error(error_msg)
            raise ModelValidationError(error_msg) from e

    @classmethod
    def _get_model_class(cls) -> Type[T]:
        """
        Get the model class this factory creates.
        To be implemented by subclasses.

        Returns:
            The model class
        """
        raise NotImplementedError("Subclasses must implement _get_model_class")

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate input data before model creation.

        Args:
            data: Raw input data

        Returns:
            Processed data dictionary
        """
        # Base implementation just returns a copy of the data
        return data.copy()

    @classmethod
    def _post_process_instance(cls, instance: T, original_data: Dict[str, Any]) -> None:
        """
        Perform post-processing on the created instance.

        Args:
            instance: The created model instance
            original_data: The original input data
        """
        # Base implementation does nothing
        pass

    @classmethod
    def create_batch(cls, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple model instances at once.

        Args:
            data_list: List of data dictionaries

        Returns:
            List of created instances
        """
        results = []
        errors = []

        for i, data in enumerate(data_list):
            try:
                instance = cls.create(data)
                results.append(instance)
            except Exception as e:
                error_detail = f"Error creating item {i}: {str(e)}"
                errors.append(error_detail)
                logger.error(error_detail)

        if errors:
            logger.warning(f"Batch creation completed with {len(errors)} errors out of {len(data_list)} items")
        else:
            logger.info(f"Successfully created {len(results)} instances")

        return results


class ProjectFactory(BaseFactory["Project"]):
    """
    Factory for creating Project model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Project"]:
        """Get the Project model class."""
        return lazy_import('database.models.project', 'Project')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate project data.

        Args:
            data: Raw project data

        Returns:
            Processed project data
        """
        processed_data = data.copy()

        # Validate and convert project type
        if 'project_type' in processed_data and isinstance(processed_data['project_type'], str):
            try:
                processed_data['project_type'] = ProjectType[processed_data['project_type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid project type: {processed_data['project_type']}")

        # Validate and convert skill level if provided
        if 'skill_level' in processed_data and isinstance(processed_data['skill_level'], str):
            try:
                processed_data['skill_level'] = SkillLevel[processed_data['skill_level'].upper()]
            except KeyError:
                raise ValueError(f"Invalid skill level: {processed_data['skill_level']}")

        # Validate and convert status if provided
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = ProjectStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid project status: {processed_data['status']}")

        # Ensure start_date is present for active projects
        if 'status' in processed_data:
            status = processed_data['status']
            if status not in [ProjectStatus.INITIAL_CONSULTATION, ProjectStatus.DESIGN_PHASE]:
                if 'start_date' not in processed_data or not processed_data['start_date']:
                    processed_data['start_date'] = datetime.utcnow()

        # Initialize empty attributes if not provided
        if 'attributes' not in processed_data:
            processed_data['attributes'] = {}

        return processed_data

    @classmethod
    def create_with_components(
            cls,
            project_data: Dict[str, Any],
            component_data_list: List[Dict[str, Any]]
    ) -> "Project":
        """
        Create a project with related components in one operation.

        Args:
            project_data: Data for the project
            component_data_list: List of data dictionaries for components

        Returns:
            Created project with linked components

        Raises:
            ModelValidationError: If creation fails
        """
        try:
            # Create the project
            project = cls.create(project_data)

            # Import component models
            ProjectComponent = lazy_import('database.models.components', 'ProjectComponent')

            # Create and link components
            for comp_data in component_data_list:
                # Ensure project_id is set
                comp_data['project_id'] = project.id

                # Create the component
                component = ProjectComponent(**comp_data)

                if hasattr(project, 'components'):
                    project.components.append(component)

            logger.info(f"Created project {project.id} with {len(component_data_list)} components")
            return project

        except Exception as e:
            error_msg = f"Failed to create project with components: {e}"
            logger.error(error_msg)
            raise ModelValidationError(error_msg) from e


class PatternFactory(BaseFactory["Pattern"]):
    """
    Factory for creating Pattern model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Pattern"]:
        """Get the Pattern model class."""
        return lazy_import('database.models.pattern', 'Pattern')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate pattern data.

        Args:
            data: Raw pattern data

        Returns:
            Processed pattern data
        """
        processed_data = data.copy()

        # Validate and convert skill level if provided
        if 'skill_level' in processed_data and isinstance(processed_data['skill_level'], str):
            try:
                processed_data['skill_level'] = SkillLevel[processed_data['skill_level'].upper()]
            except KeyError:
                raise ValueError(f"Invalid skill level: {processed_data['skill_level']}")

        # Ensure components is initialized as an empty list if not provided
        if 'components' not in processed_data:
            processed_data['components'] = []

        # Validate dimensions if provided
        if 'dimensions' in processed_data and not isinstance(processed_data['dimensions'], dict):
            raise ValueError("Dimensions must be a dictionary")

        return processed_data

    @classmethod
    def create_with_components(
            cls,
            pattern_data: Dict[str, Any],
            component_data_list: List[Dict[str, Any]]
    ) -> "Pattern":
        """
        Create a pattern with related components in one operation.

        Args:
            pattern_data: Data for the pattern
            component_data_list: List of data dictionaries for components

        Returns:
            Created pattern with linked components

        Raises:
            ModelValidationError: If creation fails
        """
        try:
            # Create the pattern
            pattern = cls.create(pattern_data)

            # Import component models
            PatternComponent = lazy_import('database.models.components', 'PatternComponent')

            # Create and link components
            for comp_data in component_data_list:
                # Ensure pattern_id is set
                comp_data['pattern_id'] = pattern.id

                # Create the component
                component = PatternComponent(**comp_data)

                if hasattr(pattern, 'components'):
                    pattern.components.append(component)

            logger.info(f"Created pattern {pattern.id} with {len(component_data_list)} components")
            return pattern

        except Exception as e:
            error_msg = f"Failed to create pattern with components: {e}"
            logger.error(error_msg)
            raise ModelValidationError(error_msg) from e


class ComponentFactory(BaseFactory["Component"]):
    """
    Factory for creating Component model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Component"]:
        """Get the Component model class."""
        return lazy_import('database.models.components', 'Component')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate component data.

        Args:
            data: Raw component data

        Returns:
            Processed component data
        """
        processed_data = data.copy()

        # Validate and convert component type
        if 'component_type' in processed_data and isinstance(processed_data['component_type'], str):
            try:
                processed_data['component_type'] = ComponentType[processed_data['component_type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid component type: {processed_data['component_type']}")

        # Initialize attributes if not provided
        if 'attributes' not in processed_data:
            processed_data['attributes'] = {}

        # Initialize dimensions if not provided
        if 'dimensions' not in processed_data:
            processed_data['dimensions'] = {}

        return processed_data

    @classmethod
    def create_with_materials(
            cls,
            component_data: Dict[str, Any],
            material_associations: List[Dict[str, Any]]
    ) -> "Component":
        """
        Create a component with material associations.

        Args:
            component_data: Data for the component
            material_associations: List of material association data

        Returns:
            Created component with material associations

        Raises:
            ModelValidationError: If creation fails
        """
        try:
            # Create the component
            component = cls.create(component_data)

            # Import material association models
            ComponentMaterial = lazy_import('database.models.components', 'ComponentMaterial')
            ComponentLeather = lazy_import('database.models.components', 'ComponentLeather')
            ComponentHardware = lazy_import('database.models.components', 'ComponentHardware')
            ComponentTool = lazy_import('database.models.components', 'ComponentTool')

            # Create and link material associations
            for assoc_data in material_associations:
                # Set component_id
                assoc_data['component_id'] = component.id

                # Determine association type
                assoc_type = assoc_data.get('type', 'material')

                if assoc_type == 'material':
                    association = ComponentMaterial(**assoc_data)
                    if hasattr(component, 'materials'):
                        component.materials.append(association)
                elif assoc_type == 'leather':
                    association = ComponentLeather(**assoc_data)
                    if hasattr(component, 'leathers'):
                        component.leathers.append(association)
                elif assoc_type == 'hardware':
                    association = ComponentHardware(**assoc_data)
                    if hasattr(component, 'hardware_items'):
                        component.hardware_items.append(association)
                elif assoc_type == 'tool':
                    association = ComponentTool(**assoc_data)
                    if hasattr(component, 'tools'):
                        component.tools.append(association)
                else:
                    raise ValueError(f"Invalid association type: {assoc_type}")

            logger.info(f"Created component {component.id} with {len(material_associations)} material associations")
            return component

        except Exception as e:
            error_msg = f"Failed to create component with materials: {e}"
            logger.error(error_msg)
            raise ModelValidationError(error_msg) from e


class SalesFactory(BaseFactory["Sales"]):
    """
    Factory for creating Sales model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Sales"]:
        """Get the Sales model class."""
        return lazy_import('database.models.sales', 'Sales')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate sales data.

        Args:
            data: Raw sales data

        Returns:
            Processed sales data
        """
        processed_data = data.copy()

        # Validate and convert status
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = SaleStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid sale status: {processed_data['status']}")

        # Validate and convert payment status
        if 'payment_status' in processed_data and isinstance(processed_data['payment_status'], str):
            try:
                processed_data['payment_status'] = PaymentStatus[processed_data['payment_status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid payment status: {processed_data['payment_status']}")

        # Ensure total_amount is not negative
        if 'total_amount' in processed_data and processed_data['total_amount'] < 0:
            raise ValueError("Total amount cannot be negative")

        # Set creation date if not provided
        if 'created_at' not in processed_data:
            processed_data['created_at'] = datetime.utcnow()

        return processed_data

    @classmethod
    def create_with_items(
            cls,
            sales_data: Dict[str, Any],
            item_data_list: List[Dict[str, Any]]
    ) -> "Sales":
        """
        Create a sales record with related items in one operation.

        Args:
            sales_data: Data for the sales record
            item_data_list: List of data dictionaries for sales items

        Returns:
            Created sales record with linked items

        Raises:
            ModelValidationError: If creation fails
        """
        try:
            # Create the sales record
            sales = cls.create(sales_data)

            # Import sales item model
            SalesItem = lazy_import('database.models.sales_item', 'SalesItem')

            # Calculate total amount if not provided
            total_amount = 0.0

            # Create and link sales items
            for item_data in item_data_list:
                # Ensure sales_id is set
                item_data['sales_id'] = sales.id

                # Create the item
                item = SalesItem(**item_data)

                # Add to total amount
                if 'price' in item_data and 'quantity' in item_data:
                    total_amount += item_data['price'] * item_data['quantity']

                if hasattr(sales, 'items'):
                    sales.items.append(item)

            # Update total amount if not explicitly set in sales_data
            if 'total_amount' not in sales_data and total_amount > 0:
                sales.total_amount = total_amount

            logger.info(f"Created sales record {sales.id} with {len(item_data_list)} items")
            return sales

        except Exception as e:
            error_msg = f"Failed to create sales with items: {e}"
            logger.error(error_msg)
            raise ModelValidationError(error_msg) from e


class HardwareFactory(BaseFactory["Hardware"]):
    """
    Factory for creating Hardware model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Hardware"]:
        """Get the Hardware model class."""
        return lazy_import('database.models.hardware', 'Hardware')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate hardware data.

        Args:
            data: Raw hardware data

        Returns:
            Processed hardware data
        """
        processed_data = data.copy()

        # Validate and convert hardware type
        if 'hardware_type' in processed_data and isinstance(processed_data['hardware_type'], str):
            try:
                processed_data['hardware_type'] = HardwareType[processed_data['hardware_type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid hardware type: {processed_data['hardware_type']}")

        # Validate and convert hardware material
        if 'material' in processed_data and isinstance(processed_data['material'], str):
            try:
                processed_data['material'] = HardwareMaterial[processed_data['material'].upper()]
            except KeyError:
                raise ValueError(f"Invalid hardware material: {processed_data['material']}")

        # Validate and convert hardware finish
        if 'finish' in processed_data and processed_data['finish'] and isinstance(processed_data['finish'], str):
            try:
                processed_data['finish'] = HardwareFinish[processed_data['finish'].upper()]
            except KeyError:
                raise ValueError(f"Invalid hardware finish: {processed_data['finish']}")

        # Validate and convert inventory status
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = InventoryStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid inventory status: {processed_data['status']}")

        # Validate and convert measurement unit
        if 'unit' in processed_data and isinstance(processed_data['unit'], str):
            try:
                processed_data['unit'] = MeasurementUnit[processed_data['unit'].upper()]
            except KeyError:
                raise ValueError(f"Invalid measurement unit: {processed_data['unit']}")

        # Ensure numeric fields are not negative
        for field in ['quantity', 'min_quantity', 'cost_per_unit', 'price_per_unit']:
            if field in processed_data and processed_data[field] < 0:
                raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative")

        # Set default unit if not provided
        if 'unit' not in processed_data:
            processed_data['unit'] = MeasurementUnit.PIECE

        return processed_data


class MaterialFactory(BaseFactory["Material"]):
    """
    Factory for creating Material model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Material"]:
        """Get the Material model class."""
        return lazy_import('database.models.material', 'Material')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate material data.

        Args:
            data: Raw material data

        Returns:
            Processed material data
        """
        processed_data = data.copy()

        # Validate and convert material type
        if 'material_type' in processed_data and isinstance(processed_data['material_type'], str):
            try:
                processed_data['material_type'] = MaterialType[processed_data['material_type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid material type: {processed_data['material_type']}")

        # Validate and convert quality grade if provided
        if 'quality_grade' in processed_data and processed_data['quality_grade'] and isinstance(processed_data['quality_grade'], str):
            try:
                processed_data['quality_grade'] = QualityGrade[processed_data['quality_grade'].upper()]
            except KeyError:
                raise ValueError(f"Invalid quality grade: {processed_data['quality_grade']}")

        # Validate and convert inventory status
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = InventoryStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid inventory status: {processed_data['status']}")

        # Validate and convert measurement unit
        if 'unit' in processed_data and isinstance(processed_data['unit'], str):
            try:
                processed_data['unit'] = MeasurementUnit[processed_data['unit'].upper()]
            except KeyError:
                raise ValueError(f"Invalid measurement unit: {processed_data['unit']}")

        # Ensure numeric fields are not negative
        for field in ['thickness', 'price_per_unit', 'min_quantity']:
            if field in processed_data and processed_data[field] is not None and processed_data[field] < 0:
                raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative")

        # Initialize metadata if not provided
        if 'metadata' not in processed_data:
            processed_data['metadata'] = {}

        return processed_data


class LeatherFactory(BaseFactory["Leather"]):
    """
    Factory for creating Leather model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Leather"]:
        """Get the Leather model class."""
        return lazy_import('database.models.leather', 'Leather')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate leather data.

        Args:
            data: Raw leather data

        Returns:
            Processed leather data
        """
        processed_data = data.copy()

        # Validate and convert leather type
        if 'leather_type' in processed_data and isinstance(processed_data['leather_type'], str):
            try:
                processed_data['leather_type'] = LeatherType[processed_data['leather_type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid leather type: {processed_data['leather_type']}")

        # Validate and convert leather finish
        if 'finish' in processed_data and processed_data['finish'] and isinstance(processed_data['finish'], str):
            try:
                processed_data['finish'] = LeatherFinish[processed_data['finish'].upper()]
            except KeyError:
                raise ValueError(f"Invalid leather finish: {processed_data['finish']}")

        # Validate and convert quality grade
        if 'quality_grade' in processed_data and processed_data['quality_grade'] and isinstance(processed_data['quality_grade'], str):
            try:
                processed_data['quality_grade'] = QualityGrade[processed_data['quality_grade'].upper()]
            except KeyError:
                raise ValueError(f"Invalid quality grade: {processed_data['quality_grade']}")

        # Validate and convert inventory status
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = InventoryStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid inventory status: {processed_data['status']}")

        # Validate and convert measurement unit
        if 'unit' in processed_data and isinstance(processed_data['unit'], str):
            try:
                processed_data['unit'] = MeasurementUnit[processed_data['unit'].upper()]
            except KeyError:
                raise ValueError(f"Invalid measurement unit: {processed_data['unit']}")

        # Ensure numeric fields are not negative
        for field in ['thickness_mm', 'size_sqft', 'area_available_sqft', 'cost_per_sqft', 'price_per_sqft', 'min_quantity']:
            if field in processed_data and processed_data[field] is not None and processed_data[field] < 0:
                raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative")

        # Set default unit if not provided
        if 'unit' not in processed_data:
            processed_data['unit'] = MeasurementUnit.SQUARE_FOOT

        return processed_data


class ToolFactory(BaseFactory["Tool"]):
    """
    Factory for creating Tool model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Tool"]:
        """Get the Tool model class."""
        return lazy_import('database.models.tool', 'Tool')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate tool data.

        Args:
            data: Raw tool data

        Returns:
            Processed tool data
        """
        processed_data = data.copy()

        # Validate and convert tool category
        if 'type' in processed_data and isinstance(processed_data['type'], str):
            try:
                processed_data['type'] = ToolCategory[processed_data['type'].upper()]
            except KeyError:
                raise ValueError(f"Invalid tool category: {processed_data['type']}")

        # Set is_active if not provided
        if 'is_active' not in processed_data:
            processed_data['is_active'] = True

        return processed_data


class SupplierFactory(BaseFactory["Supplier"]):
    """
    Factory for creating Supplier model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Supplier"]:
        """Get the Supplier model class."""
        return lazy_import('database.models.supplier', 'Supplier')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate supplier data.

        Args:
            data: Raw supplier data

        Returns:
            Processed supplier data
        """
        processed_data = data.copy()

        # Validate and convert supplier status
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = SupplierStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid supplier status: {processed_data['status']}")

        # Validate email format if provided
        if processed_data.get('contact_email'):
            import re
            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, processed_data['contact_email']):
                raise ValueError(f"Invalid email format: {processed_data['contact_email']}")

        # Validate website format if provided
        if processed_data.get('website'):
            import re
            website_pattern = r'^(http|https)://[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+(:[0-9]+)?(/.*)?$'
            if not re.match(website_pattern, processed_data['website']):
                # Try adding http:// prefix if missing
                if re.match(r'^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+', processed_data['website']):
                    processed_data['website'] = f"http://{processed_data['website']}"
                else:
                    raise ValueError(f"Invalid website URL format: {processed_data['website']}")

        return processed_data


class ProductFactory(BaseFactory["Product"]):
    """
    Factory for creating Product model instances with comprehensive validation,
    defaults, and relationship management.
    """

    @classmethod
    def _get_model_class(cls) -> Type["Product"]:
        """Get the Product model class."""
        return lazy_import('database.models.product', 'Product')

    @classmethod
    def _preprocess_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess and validate product data.

        Args:
            data: Raw product data

        Returns:
            Processed product data
        """
        processed_data = data.copy()

        # Validate numeric fields
        if 'price' in processed_data and processed_data['price'] < 0:
            raise ValueError("Price cannot be negative")

        # Validate status if provided
        if 'status' in processed_data and isinstance(processed_data['status'], str):
            try:
                processed_data['status'] = InventoryStatus[processed_data['status'].upper()]
            except KeyError:
                raise ValueError(f"Invalid product status: {processed_data['status']}")

        # Initialize metadata if not provided
        if 'metadata' not in processed_data:
            processed_data['metadata'] = {}

        # Initialize specifications if not provided
        if 'specifications' not in processed_data:
            processed_data['specifications'] = {}

        return processed_data


# Register factory models for circular import resolution
register_lazy_import('BaseFactory', 'database.models.factories', 'BaseFactory')
register_lazy_import('ProjectFactory', 'database.models.factories', 'ProjectFactory')
register_lazy_import('PatternFactory', 'database.models.factories', 'PatternFactory')
register_lazy_import('ComponentFactory', 'database.models.factories', 'ComponentFactory')
register_lazy_import('SalesFactory', 'database.models.factories', 'SalesFactory')
register_lazy_import('HardwareFactory', 'database.models.factories', 'HardwareFactory')
register_lazy_import('MaterialFactory', 'database.models.factories', 'MaterialFactory')
register_lazy_import('LeatherFactory', 'database.models.factories', 'LeatherFactory')
register_lazy_import('ToolFactory', 'database.models.factories', 'ToolFactory')
register_lazy_import('SupplierFactory', 'database.models.factories', 'SupplierFactory')
register_lazy_import('ProductFactory', 'database.models.factories', 'ProductFactory')