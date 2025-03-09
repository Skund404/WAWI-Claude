# Models Documentation

## Introduction

The models in this project represent the core entities and their relationships in the custom leatherwork management system. They are implemented using SQLAlchemy, a powerful Object-Relational Mapping (ORM) library for Python. This documentation provides detailed information about each model, its attributes, relationships, and any custom validation logic.

## Base Models and Mixins

The project includes several base models and mixins that provide common functionality and attributes to other models:

### `Base`
The `Base` class is the declarative base for all models. It establishes the connection between the models and the database.

### `ModelValidationError`
The `ModelValidationError` class is a custom exception raised when model validation fails.

### `ValidationMixin`
The `ValidationMixin` class provides common validation methods for models, such as `validate_length` and `validate_string_fields`.

### `TimestampMixin`
The `TimestampMixin` class adds timestamp columns (`created_at` and `updated_at`) to models.

### `CostingMixin`
The `CostingMixin` class adds cost-related columns (`unit_cost`, `unit_price`, `markup_percentage`) to models.

### `TrackingMixin`
The `TrackingMixin` class adds tracking-related columns (`created_by`, `updated_by`) to models.

### `ComplianceMixin`
The `ComplianceMixin` class adds compliance-related columns to models.

### `AuditMixin`
The `AuditMixin` class adds auditing functionality to models.

### `AbstractBase`
The `AbstractBase` class is an abstract base class that combines the `Base` and `TimestampMixin` classes.

## Enums

The project defines several enumerations (`enums.py`) to represent various statuses, types, and categories used across the models. These enums ensure data consistency and provide a clear set of choices for certain fields.

## Model Classes

### `Component`
The `Component` model represents a component used in leatherwork projects. It has attributes such as `name`, `description`, `component_type`, `size`, `material_requirements`, and relationships with `ProjectComponent`, `PickingListItem`, and `ComponentMaterial`.

### `ComponentMaterial`
The `ComponentMaterial` model represents the association between a component and its required materials. It has attributes such as `component_id`, `material_id`, and `quantity`.

### `Customer`
The `Customer` model represents a customer in the system. It has attributes such as `first_name`, `last_name`, `email`, `phone`, `address`, `status`, `tier`, and `source`.

### `Inventory`
The `Inventory` model represents the inventory of materials and supplies. It has attributes such as `material_id`, `quantity`, `unit`, `status`, `storage_location`, `reorder_threshold`, `supplier_id`, `cost`, and `notes`.

### `Material`
The `Material` model represents a material used in leatherwork projects. It has attributes such as `name`, `description`, `material_type`, `unit_cost`, `unit_price`, `markup_percentage`, and relationships with `Inventory`, `PurchaseItem`, `PickingListItem`, `Supplier`, and `ComponentMaterial`.

### `Leather`
The `Leather` model is a subclass of `Material` and represents leather materials. It has additional attributes such as `leather_type`, `thickness`, `grade`, `tannage`, `finish`, `size`, and `color`.

### `Hardware`
The `Hardware` model is a subclass of `Material` and represents hardware materials. It has additional attributes such as `hardware_type`, `size`, `color`, `finish`, `brand`, and `product_code`.

### `Supplies`
The `Supplies` model is a subclass of `Material` and represents supplies used in leatherwork projects. It has additional attributes such as `supplies_type`, `size`, `color`, and `brand`.

### `Pattern`
The `Pattern` model represents a pattern used for leatherwork projects. It has attributes such as `name`, `description`, `instructions`, `size_parameters`, `material_requirements`, `skill_level`, and relationships with `ProjectPattern` and `Component`.

### `PickingList`
The `PickingList` model represents a list of materials and components required for a project. It has attributes such as `project_id`, `status`, `created_by`, `created_at`, and `notes`, and a relationship with `PickingListItem`.

### `PickingListItem`
The `PickingListItem` model represents an item in a picking list. It has attributes such as `picking_list_id`, `material_id`, `component_id`, `quantity`, and `status`.

### `Product`
The `Product` model represents a product that can be sold. It has attributes such as `name`, `description`, `sku`, `unit_price`, `markup_percentage`, `labor_cost`, `overhead_cost`, `inventory_quantity`, `low_stock_threshold`, and relationships with `Pattern`, `Material`, and `SalesItem`.

### `Project`
The `Project` model represents a leatherwork project. It has attributes such as `name`, `description`, `customer_id`, `status`, `start_date`, `end_date`, `estimated_hours`, `actual_hours`, `hourly_rate`, `project_type`, and relationships with `ProjectComponent` and `PickingList`.

### `ProjectComponent`
The `ProjectComponent` model represents the association between a project and its components. It has attributes such as `project_id`, `component_id`, and `quantity`.

### `Purchase`
The `Purchase` model represents a purchase made from a supplier. It has attributes such as `supplier_id`, `purchase_date`, `status`, `shipping_cost`, `tax`, `total_cost`, `notes`, and a relationship with `PurchaseItem`.

### `PurchaseItem`
The `PurchaseItem` model represents an item in a purchase. It has attributes such as `purchase_id`, `material_id`, `quantity`, `unit_cost`, and `total_cost`.

### `Sales`
The `Sales` model represents a sale made to a customer. It has attributes such as `customer_id`, `sale_date`, `status`, `payment_status`, `shipping_cost`, `tax`, `total_amount`, `notes`, and a relationship with `SalesItem`.

### `SalesItem`
The `SalesItem` model represents an item in a sale. It has attributes such as `sale_id`, `product_id`, `quantity`, `unit_price`, and `total_price`.

### `Supplier`
The `Supplier` model represents a supplier of materials or tools. It has attributes such as `name`, `contact_name`, `email`, `phone`, `address`, `status`, and relationships with `Purchase` and `Material`.

### `Tool`
The `Tool` model represents a tool used in leatherwork projects. It has attributes such as `name`, `description`, `category`, `brand`, `supplier_id`, `purchase_date`, `cost`, `status`, and `notes`.

### `ToolList`
The `ToolList` model represents a list of tools required for a project. It has attributes such as `project_id`, `status`, `created_by`, `created_at`, and `notes`, and a relationship with `ToolListItem`.

### `ToolListItem`
The `ToolListItem` model represents an item in a tool list. It has attributes such as `tool_list_id`, `tool_id`, and `quantity`.

## Relationship Tables

The project includes several relationship tables (`relationship_tables.py`) to establish many-to-many relationships between models. These tables include:

- `pattern_component_table`: Establishes the relationship between `Pattern` and `Component` models.
- `product_pattern_table`: Establishes the relationship between `Product` and `Pattern` models.

## Initialization and Registration

The `__init__.py` file contains utility functions for model initialization and registration:

- `initialization_timer`: A context manager to track model initialization performance.
- `register_models`: Registers all imported models in the `ModelRegistry`.

## Conclusion

The models in this project provide a structured and organized way to represent the entities and their relationships in the custom leatherwork management system. By leveraging SQLAlchemy's ORM capabilities, the models abstract the underlying database operations and provide a convenient way to interact with the data.

The models also include custom validation logic to ensure data integrity and consistency. The use of enums further enhances the clarity and maintainability of the codebase.

Developers working with these models should familiarize themselves with the attributes, relationships, and any specific validation requirements for each model. The documentation provided here serves as a comprehensive reference for understanding and utilizing the models effectively in the project.