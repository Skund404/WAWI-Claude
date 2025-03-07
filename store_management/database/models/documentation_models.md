I'll analyze the information from the provided documents and create comprehensive documentation for each summary. Since there are two main summaries - models and repositories - I'll structure the documentation into separate sections for clarity.

# 1. Models Documentation

## 1.1 Database Models Overview

The database models in this leatherworking application follow a structured approach using SQLAlchemy ORM. These models represent the business entities and their relationships in the domain of leatherworking.

### Core Model Architecture

All models extend the `Base` class, which inherits from SQLAlchemy's `DeclarativeBase`. The models use a custom metaclass `BaseModelMetaclass` to handle advanced model configuration, including relationship initialization and validation.

### Key Mixins

Models use several mixins to provide common functionality:

- **TimestampMixin**: Provides created_at and updated_at fields for tracking record timestamps.
- **ValidationMixin**: Adds validation capabilities to ensure data integrity.
- **CostingMixin**: Provides cost-related fields and calculations for materials, products, and projects.
- **TrackingMixin**: Adds fields for tracking status, inventory, and other metrics.
- **ComplianceMixin**: Adds fields for regulatory compliance and quality control.

### Primary Models

1. **Component**: Represents parts used in patterns and projects with support for different component types.
2. **Customer**: Stores customer information with validation for contact details.
3. **Inventory**: Base inventory tracking with support for various material types.
4. **Hardware**: Represents hardware items like buckles, snaps, and rivets.
5. **Leather**: Represents leather materials with detailed attributes for type, finish, and quality.
6. **Material**: Generic materials used in leatherwork like thread, adhesive, dye.
7. **Pattern**: Reusable designs that can be applied to multiple products.
8. **PickingList**: Inventory items to be collected for a specific project.
9. **Product**: Finished items that can be sold or used as templates.
10. **Project**: Represents a leatherworking job with status tracking.
11. **Sales**: Records of sales transactions with customer information.
12. **Supplier**: Vendors providing materials and tools.
13. **Tool**: Tools used in leatherworking with categorization.
14. **Transaction**: Records of inventory movements and adjustments.

### Enumeration Types

The system uses enums to provide standardized values for various attributes:

- **SaleStatus**: Tracks the lifecycle of sales from quote to completion.
- **CustomerStatus/Tier**: Categorizes customers and their relationship with the business.
- **InventoryStatus**: Tracks availability of inventory items.
- **MaterialType/Quality**: Categorizes materials and their quality level.
- **ProjectType/Status**: Classifies projects and tracks their progress.
- **ToolCategory**: Organizes tools by function and type.
- **EdgeFinishType**: Specifies edge finishing techniques.

### Relationship Management

The models use a sophisticated relationship management system that:

1. Resolves circular imports using a custom `CircularImportResolver`.
2. Initializes relationships dynamically through the model metaclass.
3. Uses lazy loading to optimize performance.

### Validation Framework

Models implement comprehensive validation through:

1. SQLAlchemy type checking and constraints.
2. Custom validators in the `ValidationMixin`.
3. `ModelValidationError` for structured error reporting.

## 1.2 Factory Pattern Implementation

The application implements a factory pattern to create model instances with predefined defaults and validation:

- **BaseFactory**: Generic factory implementation.
- **Specialized Factories**: ProjectFactory, PatternFactory, ComponentFactory, etc.

## 1.3 Configuration Management

The application supports configuration at multiple levels:

- **MaterialConfig**: Material-specific settings.
- **ComponentConfig**: Component-specific settings.
- **ModelConfiguration**: Global model settings.

## 1.4 Metrics and Reporting

The application includes models for analytics and reporting:

- **MetricSnapshot**: Point-in-time metrics for dashboards.
- **MaterialUsageLog**: Detailed tracking of material consumption.
- **EfficiencyReport**: Aggregated data on production efficiency.

