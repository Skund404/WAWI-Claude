# Repositories Documentation

## Introduction

The repositories in this project provide an abstraction layer between the database models and the higher-level services. They encapsulate the logic for querying and manipulating data in the database. This documentation provides an overview of each repository and their key functionalities.

## Base Repository

The `BaseRepository` serves as a generic base class for all repositories. It provides common CRUD (Create, Read, Update, Delete) operations that can be inherited by the specific repository classes.

### Methods
- `__init__(self, session: Session, model_class: Type[T])`: Initialize the base repository with a database session and the corresponding model class.
- `get(self, model_id: Any) -> Optional[T]`: Retrieve a model instance by its primary key.
- `get_all(self) -> List[T]`: Retrieve all model instances.
- `create(self, model: T) -> T`: Create a new model instance.
- `update(self, model: T) -> T`: Update an existing model instance.
- `delete(self, model_id: Any) -> None`: Delete a model instance by its primary key.
- `commit(self) -> None`: Commit the changes to the database.
- `rollback(self) -> None`: Roll back the changes made in the current transaction.

## Component Repository

The `ComponentRepository` handles database operations related to the `Component` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Component Repository with a database session.
- `get_components_by_type(self, component_type: ComponentType) -> List[Component]`: Retrieve components by their type.

## Customer Repository

The `CustomerRepository` handles database operations related to the `Customer` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Customer Repository with a database session.
- `get_customers_by_tier(self, tier: CustomerTier) -> List[Customer]`: Retrieve customers by their tier.
- `get_customers_by_status(self, status: CustomerStatus) -> List[Customer]`: Retrieve customers by their status.

## Hardware Repository

The `HardwareRepository` handles database operations related to the `Hardware` model.

### Methods
- `__init__(self, session: Session)`: Initialize the HardwareRepository with a database session.
- `get_hardware_by_type(self, hardware_type: HardwareType) -> List[Hardware]`: Retrieve hardware by its type.
- `get_hardware_by_finish(self, finish: HardwareFinish) -> List[Hardware]`: Retrieve hardware by its finish.

## Inventory Repository

The `InventoryRepository` handles database operations related to the `Inventory` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Inventory Repository with a database session.
- `get_inventory_by_status(self, status: InventoryStatus) -> List[Inventory]`: Retrieve inventory by its status.
- `get_low_stock_inventory(self, threshold: int) -> List[Inventory]`: Retrieve inventory with a quantity below the specified threshold.

## Leather Repository

The `LeatherRepository` handles database operations related to the `Leather` model.

### Methods
- `__init__(self, session: Session)`: Initialize the LeatherRepository with a database session.
- `get_leather_by_type(self, leather_type: LeatherType) -> List[Leather]`: Retrieve leather by its type.
- `get_leather_by_quality(self, quality: QualityGrade) -> List[Leather]`: Retrieve leather by its quality grade.

## Material Repository

The `MaterialRepository` handles database operations related to the `Material` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Material Repository with a database session.
- `get_materials_by_type(self, material_type: MaterialType) -> List[Material]`: Retrieve materials by their type.
- `get_low_stock_materials(self, threshold: int) -> List[Material]`: Retrieve materials with a quantity below the specified threshold.

## Metrics Repository 

The `MetricsRepository` handles database operations related to metrics and analytics.

### Methods
- `__init__(self, session: Session)`: Initialize the MetricsRepository with a database session. 
- `get_material_usage_logs(self, start_date: datetime, end_date: datetime) -> List[MaterialUsageLog]`: Retrieve material usage logs within the specified date range.
- `get_metric_snapshot(self, metric_type: MetricType, time_frame: TimeFrame) -> Optional[MetricSnapshot]`: Retrieve a metric snapshot for a specific metric type and time frame.

## Pattern Repository

The `PatternRepository` handles database operations related to the `Pattern` model.

### Methods  
- `__init__(self, session: Session)`: Initialize the PatternRepository with a database session.
- `get_patterns_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]`: Retrieve patterns by their required skill level.
- `search_patterns(self, query: str) -> List[Pattern]`: Search for patterns based on a query string.

## Picking List Repository

The `PickingListRepository` handles database operations related to the `PickingList` and `PickingListItem` models.

### Methods
- `__init__(self, session: Session)`: Initialize the PickingList Repository with a database session.
- `get_picking_lists_by_status(self, status: PickingListStatus) -> List[PickingList]`: Retrieve picking lists by their status.
- `get_picking_list_items_by_list(self, picking_list_id: int) -> List[PickingListItem]`: Retrieve picking list items by their associated picking list ID.

## Product Repository

The `ProductRepository` handles database operations related to the `Product` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Product Repository with a database session.
- `search_products(self, query: str) -> List[Product]`: Search for products based on a query string.
- `get_products_by_material(self, material_type: MaterialType) -> List[Product]`: Retrieve products by the type of material used.

## Project Component Repository

The `ProjectComponentRepository` handles database operations related to the `ProjectComponent` model.

### Methods
- `__init__(self, session: Session)`: Initialize the ProjectComponent Repository with a database session.
- `get_project_components_by_project(self, project_id: int) -> List[ProjectComponent]`: Retrieve project components by their associated project ID.

## Project Repository

The `ProjectRepository` handles database operations related to the `Project` model.

### Methods
- `__init__(self, session: Session)`: Initialize the project repository with a database session.
- `get_projects_by_status(self, status: ProjectStatus) -> List[Project]`: Retrieve projects by their status.
- `get_projects_by_type(self, project_type: ProjectType) -> List[Project]`: Retrieve projects by their type.
- `get_projects_by_skill_level(self, skill_level: SkillLevel) -> List[Project]`: Retrieve projects by their required skill level.

## Purchase Item Repository

The `PurchaseItemRepository` handles database operations related to the `PurchaseItem` model.

### Methods
- `__init__(self, session: Session)`: Initialize the PurchaseItem Repository with a database session.
- `get_purchase_items_by_purchase(self, purchase_id: int) -> List[PurchaseItem]`: Retrieve purchase items by their associated purchase ID.

## Purchase Repository

The `PurchaseRepository` handles database operations related to the `Purchase` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Purchase Repository with a database session.
- `get_purchases_by_status(self, status: PurchaseStatus) -> List[Purchase]`: Retrieve purchases by their status.
- `get_purchases_by_supplier(self, supplier_id: int) -> List[Purchase]`: Retrieve purchases by their associated supplier ID.

## Repository Factory

The `RepositoryFactory` provides a centralized way to create instances of different repositories.

### Methods
- `__init__(self, session: Session)`: Initialize the repository factory with a database session.
- `get_repository(self, repository_type: Type[BaseRepository]) -> BaseRepository`: Get an instance of the specified repository type.

## Sales Item Repository

The `SalesItemRepository` handles database operations related to the `SalesItem` model.

### Methods
- `__init__(self, session: Session)`: Initialize the SalesItemRepository with a database session.
- `get_sales_items_by_sale(self, sale_id: int) -> List[SalesItem]`: Retrieve sales items by their associated sale ID.

## Sales Repository

The `SalesRepository` handles database operations related to the `Sales` model.

### Methods
- `__init__(self, session: Session)`: Initialize the SalesRepository with a database session.  
- `get_sales_by_status(self, status: SaleStatus) -> List[Sales]`: Retrieve sales by their status.
- `get_sales_by_customer(self, customer_id: int) -> List[Sales]`: Retrieve sales by their associated customer ID.
- `get_sales_by_payment_status(self, payment_status: PaymentStatus) -> List[Sales]`: Retrieve sales by their payment status.

## Supplier Repository

The `SupplierRepository` handles database operations related to the `Supplier` model.

### Methods
- `__init__(self, session: Session)`: Initialize the SupplierRepository with a database session.
- `get_suppliers_by_status(self, status: SupplierStatus) -> List[Supplier]`: Retrieve suppliers by their status.
- `search_suppliers(self, query: str) -> List[Supplier]`: Search for suppliers based on a query string.
- `get_top_suppliers_by_purchase_count(self, limit: int) -> List[Supplier]`: Retrieve the top suppliers based on their purchase count.

## Supplies Repository

The `SuppliesRepository` handles database operations related to the `Supplies` model.

### Methods
- `__init__(self, session: Session)`: Initialize the SuppliesRepository with a database session. 
- `get_supplies_by_type(self, material_type: MaterialType) -> List[Supplies]`: Retrieve supplies by their material type.
- `get_low_stock_supplies(self, threshold: int) -> List[Supplies]`: Retrieve supplies with a quantity below the specified threshold.

## Tool List Repository

The `ToolListRepository` handles database operations related to the `ToolList` and `ToolListItem` models.

### Methods
- `__init__(self, session: Session)`: Initialize the ToolList Repository with a database session.
- `get_tool_lists_by_status(self, status: ToolListStatus) -> List[ToolList]`: Retrieve tool lists by their status.
- `get_tool_list_items_by_list(self, tool_list_id: int) -> List[ToolListItem]`: Retrieve tool list items by their associated tool list ID.

## Tool Repository

The `ToolRepository` handles database operations related to the `Tool` model.

### Methods
- `__init__(self, session: Session)`: Initialize the Tool Repository with a database session.  
- `get_tools_by_category(self, category: ToolCategory) -> List[Tool]`: Retrieve tools by their category.
- `search_tools(self, query: str) -> List[Tool]`: Search for tools based on a query string.

## Conclusion

The repositories provided in this project offer a convenient way to interact with the database and perform various data operations. They abstract the complexity of the underlying database queries and provide a clean interface for the higher-level services to use. By utilizing these repositories, developers can easily retrieve, create, update, and delete data related to different entities in the system.