# Sales and Customer Management Module Documentation

## 1. Overview

The Sales and Customer Management module provides a comprehensive solution for managing customer relationships, sales processes, and order fulfillment within the leatherworking ERP system. This module integrates with inventory, project management, and reporting modules to create a seamless workflow from customer acquisition to order fulfillment.

## 2. Architecture and Components

### 2.1 Module Structure

```
gui/views/sales/
├── customer_view.py               # Customer list and management interface
├── customer_details_dialog.py     # Customer information editor and viewer
├── sales_view.py                  # Sales list and dashboard interface
├── sales_details_view.py          # Sale details editor and viewer
├── sales_item_dialog.py           # Dialog for managing line items
├── invoice_generator.py           # Invoice generation functionality
├── order_creation_wizard.py       # Multi-step order creation interface
├── order_status_view.py           # Order tracking and status management
└── payment_dialog.py              # Payment processing interface
```

### 2.2 Key Components

#### Customer Management Components

- **CustomerView**: Main interface for viewing, searching, and managing customer records
  - Provides advanced filtering, metrics dashboard, and quick actions
  - Implements event-based refresh when customer data changes

- **CustomerDetailsDialog**: Comprehensive customer information management
  - Tabbed interface with sections for personal information, addresses, purchase history, projects, and activity
  - Supports custom fields for flexible data management
  - Integrates with sales and project modules for relationship management

#### Sales Management Components

- **SalesView**: Dashboard and listing interface for all sales records
  - Provides filtering by customer, date, status, and payment status
  - Includes sales metrics and visualizations

- **SalesDetailsView**: Detailed sales record viewer and editor
  - Manages line items, customer information, and payment details
  - Supports order status workflow management

- **InvoiceGenerator**: Creates professional invoices from sales records
  - Supports multiple output formats (PDF, HTML)
  - Includes customizable templates and branding options

### 2.3 Dependency Structure

The module uses:
- Service layer via dependency injection (`customer_service`, `sales_service`)
- Event system for inter-component communication (`publish`, `subscribe`)
- Base classes (`BaseListView`, `BaseDialog`) for consistent UI patterns
- Data models defined in `database/models/enums.py`

## 3. Feature Details

### 3.1 Customer Management

#### Customer Listing and Search
- Grid-based view with sortable columns
- Comprehensive search with filters for:
  - Basic Info (Name, Email, Phone)
  - Status (Active, Inactive, Lead)
  - Tier (Standard, Premium, VIP)
  - Date Ranges (Creation, Last Purchase)
  - Source (Website, Referral, etc.)

#### Customer Metrics Dashboard
- Key statistics for customer base analysis:
  - Total customers by status
  - Customer tier distribution
  - New customers over time
  - Revenue metrics by customer segment

#### Customer Profile Management
- Comprehensive customer profile editing
- Multiple address management (Primary, Shipping, Billing)
- Purchase history tracking and analysis
- Project association and history
- Activity timeline for all customer interactions
- Notes and communication history

### 3.2 Sales Management

#### Sales Dashboard
- Sales performance metrics
- Status distribution visualization
- Recent sales activity
- Sales trend charts

#### Sales Record Management
- Complete order lifecycle management
- Line item management with inventory integration
- Multiple payment methods support
- Shipping and fulfillment tracking
- Integration with project management for custom orders

#### Invoice Generation
- Professional invoice creation
- Multiple output formats (PDF, Email, Print)
- Customizable templates
- Tax and discount handling

### 3.3 Order Processing

#### Order Creation Workflow
- Step-by-step guided order creation
- Real-time inventory availability check
- Custom options and specifications
- Pricing and discount application
- Payment method selection

#### Order Status Management
- Visual status workflow
- Status change tracking and history
- Automated notifications
- Milestone tracking

#### Payment Processing
- Multiple payment method support
- Partial payment handling
- Payment verification workflow
- Refund processing

## 4. Implementation Status

### 4.1 Completed Components
- ✅ CustomerView (customer_view.py)
  - Comprehensive customer listing and filtering
  - Customer metrics dashboard
  - Full CRUD operations for customer records

- ✅ CustomerDetailsDialog (customer_details_dialog.py)
  - Tabbed interface for all customer information
  - Address management with multiple address support
  - Purchase history display
  - Projects association
  - Activity history
  - Notes and custom fields

### 4.2 Pending Implementation
- 🔄 SalesView
- 🔄 SalesDetailsView
- 🔄 SalesItemDialog
- 🔄 InvoiceGenerator
- 🔄 OrderCreationWizard
- 🔄 OrderStatusView
- 🔄 PaymentDialog

## 5. Usage Instructions

### 5.1 Customer Management

#### Accessing Customer List
```python
# From main menu or dashboard
self.parent.master.show_view("customer")
```

#### Filtering Customers
1. Use the search field for general text search across all fields
2. Use advanced filters section to narrow by status, tier, date ranges
3. Click "Apply Filters" to update the list

#### Adding a New Customer
1. Click "Add Customer" button in the header
2. Fill in required fields in the customer details dialog
3. Click "Save" to create the customer record

#### Viewing Customer Details
1. Select a customer from the list
2. Click "View Details" button or double-click the customer row
3. Navigate through tabs to view different aspects of the customer record

#### Editing a Customer
1. Open customer details in view mode
2. Click "Edit" button to switch to edit mode
3. Make changes to customer information
4. Click "Save" to update the record

### 5.2 Sales Management

#### Creating a New Sale
1. From customer view, select a customer and click "New Sale"
2. Alternatively, access from the sales view using the "Add Sale" button
3. Complete the order creation wizard:
   - Select/confirm customer
   - Add line items
   - Apply discounts/taxes
   - Specify shipping details
   - Process payment
4. Confirm and finalize the sale

#### Managing Sale Status
1. Open sale details view
2. Use the status workflow controls to update status
3. Enter any notes required for status change
4. Status history is automatically tracked

#### Generating Invoices
1. Open sale details view
2. Click "Generate Invoice" button
3. Select template and output format
4. Preview and confirm
5. Save or print the generated invoice

## 6. Integration Points

### 6.1 Inventory Integration
- Real-time inventory checks during order creation
- Inventory adjustments on order fulfillment
- Low stock alerts during sales process

### 6.2 Project Management Integration
- Association of sales orders with custom projects
- Project status updates based on order progression
- Resource allocation coordination

### 6.3 Reporting Integration
- Sales and customer data feeds into reporting module
- Custom report generation for sales analysis
- Customer segmentation analysis

### 6.4 Service Layer Integration
```python
# Example of service usage in components
self.customer_service = get_service("customer_service")
self.sales_service = get_service("sales_service")

# Example of retrieving customer data with related information
customer = self.customer_service.get_customer(
    self.customer_id,
    include_address=True,
    include_sales=True,
    include_projects=True,
    include_activity=True,
    include_notes=True
)
```

### 6.5 Event Communication
```python
# Publishing events when important actions occur
publish("customer_updated", {"customer_id": customer_id})
publish("sale_status_changed", {"sale_id": sale_id, "old_status": old_status, "new_status": new_status})

# Subscribing to events from other modules
subscribe("customer_updated", self.on_customer_updated)
subscribe("sale_completed", self.on_sale_completed)
```

## 7. Code Examples

### 7.1 Customer Search Implementation

```python
def load_data(self):
    """Load customer data into the treeview based on current filters and pagination."""
    try:
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        
        # Get current page and search criteria
        offset = (self.current_page - 1) * self.page_size
        
        # Get search criteria
        search_text = self.search_var.get() if hasattr(self, 'search_var') else ""
        
        # Collect filter criteria
        filters = {}
        
        if hasattr(self, 'status_var') and self.status_var.get() != "All":
            filters['status'] = self.status_var.get().upper()
        
        if hasattr(self, 'tier_var') and self.tier_var.get() != "All":
            filters['tier'] = self.tier_var.get().upper()
        
        # Get total count
        total_count = self.customer_service.count_customers(
            search_text=search_text,
            filters=filters
        )
        
        # Calculate total pages
        total_pages = (total_count + self.page_size - 1) // self.page_size
        
        # Update pagination display
        self.update_pagination_display(total_pages)
        
        # Get customers for current page
        customers = self.customer_service.search_customers(
            search_text=search_text,
            filters=filters,
            sort_field=sort_field,
            sort_direction=sort_direction,
            offset=offset,
            limit=self.page_size
        )
        
        # Insert customers into treeview
        for customer in customers:
            values = self.extract_item_values(customer)
            item_id = str(customer.id) if hasattr(customer, 'id') else "0"
            
            self.treeview.insert('', 'end', iid=item_id, values=values)
```

### 7.2 Customer Details Form Handling

```python
def collect_form_data(self):
    """Collect form data into a dictionary.
    
    Returns:
        Dictionary of form data
    """
    # Basic information
    data = {
        "first_name": self.first_name_var.get(),
        "last_name": self.last_name_var.get(),
        "email": self.email_var.get(),
        "phone": self.phone_var.get(),
        "alt_phone": self.alt_phone_var.get(),
        "gender": self.gender_var.get(),
        "status": self.status_var.get(),
        "tier": self.tier_var.get(),
        "source": self.source_var.get(),
        "notes": self.notes_text.get("1.0", tk.END).strip()
    }
    
    # Parse date of birth if provided
    if self.dob_var.get():
        try:
            data["date_of_birth"] = datetime.datetime.strptime(self.dob_var.get(), "%Y-%m-%d")
        except ValueError:
            self.logger.warning(f"Invalid date format for DOB: {self.dob_var.get()}")
    
    # Address information
    address_data = {
        "street1": self.street1_var.get(),
        "street2": self.street2_var.get(),
        "city": self.city_var.get(),
        "state": self.state_var.get(),
        "postal_code": self.postal_code_var.get(),
        "country": self.country_var.get()
    }
    
    # Add shipping address if different from primary
    if not self.same_as_primary_var.get():
        address_data.update({
            "ship_street1": self.ship_street1_var.get(),
            "ship_street2": self.ship_street2_var.get(),
            "ship_city": self.ship_city_var.get(),
            "ship_state": self.ship_state_var.get(),
            "ship_postal_code": self.ship_postal_code_var.get(),
            "ship_country": self.ship_country_var.get()
        })
    
    # Add address to customer data
    data["address"] = address_data
    
    return data
```

## 8. Best Practices and Guidelines

### 8.1 UI Design Standards
- Use consistent spacing and layout across all components
- Follow the established tab patterns for complex data forms
- Use status badges for visual status indicators
- Implement section headers for logical grouping of information

### 8.2 Error Handling
- Implement comprehensive error handling with user-friendly messages
- Log errors at appropriate levels for troubleshooting
- Validate user input before sending to services
- Provide clear feedback when operations fail

### 8.3 Performance Considerations
- Implement pagination for large datasets
- Use lazy loading for related data when appropriate
- Cache frequently used reference data
- Optimize service calls to minimize database queries

## 9. Future Enhancements

### 9.1 Planned Features
- Customer segmentation and analytics dashboard
- Automated email marketing integration
- Customer feedback and satisfaction tracking
- Advanced sales forecasting tools
- Multi-currency support
- Batch operations for customer and sales management

### 9.2 Integration Opportunities
- External CRM synchronization
- E-commerce platform integration
- Payment gateway integration
- Shipping provider integration
- Tax calculation service integration

## 10. Troubleshooting

### 10.1 Common Issues

#### Customer Search Not Returning Expected Results
1. Verify search criteria and filters are correctly applied
2. Check for special characters in search terms
3. Confirm service layer search implementation handles partial matches

#### Customer Details Not Saving
1. Validate all required fields are completed
2. Check for formatting errors in date fields
3. Verify service connection and database access

#### UI Display Issues
1. Verify theme settings are correctly applied
2. Check for widget configuration issues
3. Test with different screen resolutions for layout problems

### 10.2 Debugging Steps
1. Enable debug-level logging for detailed component behavior
2. Check service call parameters and responses
3. Verify event publication and subscription
4. Test individual component functionality independently

---

This document serves as the comprehensive guide for the Sales and Customer Management module implementation. It should be updated as the implementation progresses and new components are added.