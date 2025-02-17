# Store Management System

[Concise paragraph summarizing the purpose of the software, its target audience, and key benefits]

## Table of Contents

1.  Project Overview
2.  Features
3.  Installation
4.  Usage
5.  Modules
    - 5.1 Product Management
        - 5.1.1 Storage View
        - 5.1.2 Recipe View
    - 5.2 Storage Management
        - 5.2.1 Shelf Management
        - 5.2.2 Sorting System
    - 5.3 Order Management
        - 5.3.1 Incoming Goods
        - 5.3.2 Shopping List
        - 5.3.3 Supplier
6.  Data Management
7.  Security Features
8.  Roadmap (Optional)
9.  Contributing
10. License
11. Contact

## 1. Project Overview

[Detailed description of the project's goals, target audience, and benefits]

## 2. Features

[List the main features of the application, using bullet points. Highlight any unique or innovative features.]

## 3. Installation

[Step-by-step instructions on how to set up the development environment, install dependencies, and configure the database.]

### 3.1 Prerequisites

-   Python 3.8 or higher
-   pip package manager
-   [Optional] Virtual environment (recommended)

### 3.2 Setup Instructions

1.  Clone the repository:
    ```bash
    git clone [repository URL]
    ```
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv
    ```
3.  Activate the virtual environment:
    -   Windows: `.venv\Scripts\activate`
    -   macOS/Linux: `source .venv/bin/activate`
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5.  Configure the database:
    -   Edit the `config.py` file and set the correct database connection settings.
    -   Run the database setup script:
        ```bash
        python database/database_setup.py
        ```
6.  Run the application:
    ```bash
    python main.py
    ```

## 4. Usage

[General instructions on how to use the application, including screenshots (if available).]

## 5. Modules

### 5.1 Product Management

#### 5.1.1 Storage View

[Description of the Storage View module, including table headers and functionality.]

Table Headers:

-   Unique ID Product
-   Name
-   Type
-   Collection
-   Color
-   Amount
-   Bin
-   Notes

Functionality:

-   ADD: [Description of the "ADD" functionality, including the drop-down menu for "Unique ID Product" and the preview feature.]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

#### 5.1.2 Recipe View

[Description of the Recipe View module, including table headers and functionality.]

INDEX Table Headers:

-   Unique ID Product
-   Name
-   Type
-   Collection
-   Notes

Recipe Details Table Headers:

-   Unique ID parts
-   Name
-   Color
-   Amount
-   Size
-   in storage
-   Pattern ID
-   Notes

Functionality:

-   ADD Recipe: [Description of the "ADD Recipe" functionality]
-   ADD Item to Recipe: [Description of the "ADD Item to Recipe" functionality]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

### 5.2 Storage Management

#### 5.2.1 Shelf Management

[Description of the Shelf Management module, including table headers and functionality.]

Table Headers:

-   Unique ID leather
-   Name
-   Type
-   Color
-   Thickness
-   size(ft)
-   Area(sqft)
-   Shelf
-   Notes

Functionality:

-   ADD: [Description of the "ADD" functionality, including the auto-generation of "Unique ID leather" and the shelf validation.]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

#### 5.2.2 Sorting System

[Description of the Sorting System module, including table headers and functionality.]

Table Headers:

-   Unique ID parts
-   Name
-   Color
-   in Storage
-   bin
-   Notes

Functionality:

-   ADD: [Description of the "ADD" functionality, including the auto-generation of "Unique ID parts" from the bin.]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

### 5.3 Order Management

#### 5.3.1 Incoming Goods

[Description of the Incoming Goods module, including table headers and functionality.]

Orders Table Headers:

-   Supplier
-   date of order
-   status
-   order number
-   payed

Order Details Table Headers:

-   Article
-   Price
-   Amount
-   Total
-   Unique ID (parts/leather)
-   Notes
-   Shipping
-   Discount
-   TOTAL

Functionality:

-   ADD: [Description of the "ADD" functionality, including the drop-down menu for "Supplier" and the table generation.]
-   Finish order and add to storage: [Description of the "Finish order and add to storage" functionality]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

#### 5.3.2 Shopping List

[Description of the Shopping List module, including table headers and functionality.]

Table Headers:

-   Supplier
-   Unique ID
-   Article
-   Color
-   Amount
-   Price
-   Notes

Functionality:

-   ADD: [Description of the "ADD" functionality, including the table generation.]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

#### 5.3.3 Supplier

[Description of the Supplier module, including table headers and functionality.]

Table Headers:

-   CompanyName
-   ContactPerson
-   PhoneNumber
-   EmailAddress
-   Website
-   StreetAddress
-   City
-   StateProvince
-   PostalCode
-   Country
-   TaxID
-   BusinessType
-   PaymentTerms
-   Currency
-   BankDetails
-   ProductsOffered
-   LeadTime
-   LastOrderDate
-   Notes

Functionality:

-   ADD: [Description of the "ADD" functionality]
-   SEARCH: [Description of the "Search" functionality]
-   FILTER: [Description of the "Filter" functionality]
-   SAVE/LOAD: [Description of the "Save/Load" functionality]
-   UNDO/REDO: [Description of the "Undo/Redo" functionality]
-   Reset View: [Description of the "Reset View" functionality]
-   Double-click cell editing: [Description of the cell editing feature]
-   Delete row: [Description of the delete row feature]
-   Sortable headers: [Description of the sortable headers feature]

## 6. Data Management

[Description of the data validation rules, error handling, and backup system.]

### 6.1 Data Validation Rules

[Detailed description of the data validation rules.]

### 6.2 Error Handling

[Detailed description of the error handling mechanisms.]

### 6.3 Backup System

[Detailed description of the backup system.]

## 7. Security Features

[Description of the security features, including user management and data protection.]

### 7.1 User Management

[Detailed description of the user management features.]

### 7.2 Data Protection

[Detailed description of the data protection mechanisms.]

## 8. Roadmap (Optional)

[Planned features and future development directions]

## 9. Contributing

[Guidelines for contributing to the project, including coding style, branching model, and pull request process.]

## 10. License

[License information (e.g., MIT License)]

## 11. Contact

PasBernard@protonmail.com
