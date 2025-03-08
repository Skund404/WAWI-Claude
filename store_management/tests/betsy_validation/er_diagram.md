# Leatherworking Application Entity-Relationship Diagram

## Entities

Customer {
    int id
    str name
    str email
    CustomerStatus status
}

Sales {
    int id
    datetime created_at
    float total_amount
    SalesStatus status
    PaymentStatus payment_status
    int customer_id
}

SalesItem {
    int id
    int quantity
    float price
    int sales_id
    int product_id
}

Product {
    int id
    str name
    float price
}

ProductPattern {
    int product_id
    int pattern_id
}

Purchase {
    int id
    datetime created_at
    float total_amount
    PurchaseStatus status
    int supplier_id
}

PurchaseItem {
    int id
    int quantity
    float price
    int purchase_id
    int material_id
    int leather_id
    int hardware_id
    int tool_id
}

Supplier {
    int id
    str name
    str contact_email
    SupplierStatus status
}

## Inventory Entities

ProductInventory {
    int id
    int product_id
    int quantity
    InventoryStatus status
    str storage_location
}

MaterialInventory {
    int id
    int material_id
    float quantity
    InventoryStatus status
    str storage_location
}

LeatherInventory {
    int id
    int leather_id
    float quantity
    InventoryStatus status
    str storage_location
}

HardwareInventory {
    int id
    int hardware_id
    int quantity
    InventoryStatus status
    str storage_location
}

ToolInventory {
    int id
    int tool_id
    int quantity
    InventoryStatus status
    str storage_location
}

## Project and Pattern Entities

Project {
    int id
    str name
    str description
    ProjectType type
    ProjectStatus status
    datetime start_date
    datetime end_date
    int sales_id
}

Pattern {
    int id
    str name
    str description
    SkillLevel skill_level
    json components
}

Component {
    int id
    str name
    json attributes
}

## Material and Resource Entities

Material {
    int id
    str name
    MaterialType type
    MeasurementUnit unit
    QualityGrade quality
    int supplier_id
}

Leather {
    int id
    str name
    LeatherType type
    QualityGrade quality
    int supplier_id
}

Hardware {
    int id
    str name
    HardwareType type
    int supplier_id
}

Tool {
    int id
    str name
    str description
    ToolType type
    int supplier_id
}

## Junction Tables for Relationships

ComponentMaterial {
    int component_id
    int material_id
    float quantity
}

ComponentLeather {
    int component_id
    int leather_id
    float quantity
}

ComponentHardware {
    int component_id
    int hardware_id
    int quantity
}

ComponentTool {
    int component_id
    int tool_id
}

ProjectComponent {
    int id
    int project_id
    int component_id
    int quantity
    int picking_list_item_id
}

## Picking and Tool Management

PickingList {
    int id
    int sales_id
    PickingListStatus status
    datetime created_at
    datetime completed_at
}

PickingListItem {
    int id
    int picking_list_id
    int component_id
    int material_id
    int leather_id
    int hardware_id
    int quantity_ordered
    int quantity_picked
}

ToolList {
    int id
    int project_id
    ToolListStatus status
    datetime created_at
}

ToolListItem {
    int id
    int tool_list_id
    int tool_id
    int quantity
}

## Relationships

Customer ||--o{ Sales : places
Sales ||--|{ SalesItem : contains
Sales ||--|| PickingList : generates
Sales ||--o| Project : requires

SalesItem }|--|| Product : references
Product }|--o{ ProductPattern : associated_with
ProductPattern }o--|| Pattern : follows

Product ||--|{ ProductInventory : stored_in
Material ||--|{ MaterialInventory : stored_in
Leather ||--|{ LeatherInventory : stored_in
Hardware ||--|{ HardwareInventory : stored_in
Tool ||--|{ ToolInventory : stored_in

Pattern ||--|{ Component : composed_of
Component ||--|{ ComponentMaterial : uses
Component ||--|{ ComponentLeather : uses
Component ||--|{ ComponentHardware : uses
Component ||--|{ ComponentTool : requires

ComponentMaterial }|--|| Material : consists_of
ComponentLeather }|--|| Leather : consists_of
ComponentHardware }|--|| Hardware : consists_of
ComponentTool }|--|| Tool : uses

Project ||--|{ ProjectComponent : consists_of
ProjectComponent }|--|| Component : uses
ProjectComponent ||--|| PickingListItem : fulfills

Project ||--|| ToolList : requires

Supplier ||--|{ Material : supplies
Supplier ||--|{ Leather : supplies
Supplier ||--|{ Hardware : supplies
Supplier ||--|{ Tool : supplies
Supplier ||--|{ Purchase : receives

Purchase ||--|{ PurchaseItem : contains
PurchaseItem }o--|| Material : orders
PurchaseItem }o--|| Leather : orders
PurchaseItem }o--|| Hardware : orders
PurchaseItem }o--|| Tool : orders

PickingList ||--o{ PickingListItem : contains
PickingListItem }o--|| Material : consumes
PickingListItem }o--|| Leather : consumes
PickingListItem }o--|| Hardware : consumes

ToolList ||--o{ ToolListItem : contains
ToolListItem }o--|| Tool : lists