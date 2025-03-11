# gui/views/sales/customer_details_dialog.py
"""
Customer details dialog for viewing and editing customer information.

This dialog provides a comprehensive interface for managing customer details,
including personal information, contact details, purchase history, and activity.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import CustomerStatus, CustomerTier, CustomerSource
from gui.base.base_dialog import BaseDialog
from gui.base.base_form_view import FormField
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class CustomerDetailsDialog(BaseDialog):
    """
    Dialog for viewing and editing customer details.

    This dialog contains a tabbed interface with sections for basic information,
    purchase history, projects, and activity history.
    """

    def __init__(self, parent, **kwargs):
        """Initialize the customer details dialog.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                customer_id: ID of the customer to view/edit (None for new customers)
                create_new: Whether to create a new customer
                readonly: Whether the dialog is in read-only mode
        """
        # Set dialog properties
        self.title = "Customer Details"
        self.width = 800
        self.height = 600

        # Store view parameters
        self.customer_id = kwargs.get("customer_id")
        self.create_new = kwargs.get("create_new", False)
        self.readonly = kwargs.get("readonly", False)

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self.customer_service = get_service("customer_service")
        self.sales_service = get_service("sales_service")
        self.project_service = get_service("project_service")

        # Initialize result
        self.result = {"success": False, "customer_id": self.customer_id}

        # Call parent constructor
        super().__init__(parent, title=self.title, width=self.width, height=self.height)

    def create_layout(self):
        """Create the dialog layout."""
        # Create main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create header section with customer overview
        self.create_header_section(main_frame)

        # Create notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create tabs
        self.create_basic_info_tab()
        self.create_address_tab()
        self.create_purchase_history_tab()
        self.create_projects_tab()
        self.create_activity_tab()
        self.create_notes_tab()

        # Create buttons section
        self.create_buttons_section(main_frame)

        # Load customer data if editing
        if self.customer_id:
            self.load_customer_data()

        # Set initial UI state
        self.update_ui_state()

    def create_header_section(self, parent):
        """Create header section with customer overview.

        Args:
            parent: The parent widget
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Left column with ID and name
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left_frame, text="Customer ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.id_label = ttk.Label(left_frame, text="New" if self.create_new else f"#{self.customer_id}")
        self.id_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(left_frame, text="Customer Name:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_label = ttk.Label(left_frame, text="New Customer" if self.create_new else "Loading...")
        self.name_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        # Right column with status and tier
        right_frame = ttk.Frame(header_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        status_frame = ttk.Frame(right_frame)
        status_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        self.status_badge = StatusBadge(status_frame, "New" if self.create_new else "Loading...", "new")
        self.status_badge.pack(side=tk.LEFT)

        ttk.Label(right_frame, text="Tier:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.tier_label = ttk.Label(right_frame, text="Standard" if self.create_new else "Loading...")
        self.tier_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

    def create_basic_info_tab(self):
        """Create the basic information tab."""
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="Basic Information")

        # Create scrollable frame
        canvas = tk.Canvas(basic_tab)
        scrollbar = ttk.Scrollbar(basic_tab, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create form frame
        form_frame = ttk.Frame(scrollable_frame, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Personal information section
        personal_frame = ttk.LabelFrame(form_frame, text="Personal Information")
        personal_frame.pack(fill=tk.X, pady=(0, 10))

        # First name
        ttk.Label(personal_frame, text="First Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.first_name_var = tk.StringVar()
        self.first_name_entry = ttk.Entry(personal_frame, textvariable=self.first_name_var, width=30)
        self.first_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Last name
        ttk.Label(personal_frame, text="Last Name:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.last_name_var = tk.StringVar()
        self.last_name_entry = ttk.Entry(personal_frame, textvariable=self.last_name_var, width=30)
        self.last_name_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Date of birth
        ttk.Label(personal_frame, text="Date of Birth:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dob_var = tk.StringVar()
        dob_frame = ttk.Frame(personal_frame)
        dob_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        self.dob_entry = ttk.Entry(dob_frame, textvariable=self.dob_var, width=12)
        self.dob_entry.pack(side=tk.LEFT)

        ttk.Button(
            dob_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.dob_var)
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Gender
        ttk.Label(personal_frame, text="Gender:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.gender_var = tk.StringVar()
        gender_combo = ttk.Combobox(personal_frame, textvariable=self.gender_var, width=15, state="readonly")
        gender_combo["values"] = ["", "Male", "Female", "Non-binary", "Prefer not to say"]
        gender_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Contact information section
        contact_frame = ttk.LabelFrame(form_frame, text="Contact Information")
        contact_frame.pack(fill=tk.X, pady=(0, 10))

        # Email
        ttk.Label(contact_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(contact_frame, textvariable=self.email_var, width=30)
        self.email_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Phone
        ttk.Label(contact_frame, text="Phone:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(contact_frame, textvariable=self.phone_var, width=20)
        self.phone_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Alternate phone
        ttk.Label(contact_frame, text="Alt. Phone:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.alt_phone_var = tk.StringVar()
        self.alt_phone_entry = ttk.Entry(contact_frame, textvariable=self.alt_phone_var, width=20)
        self.alt_phone_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Preferred contact method
        ttk.Label(contact_frame, text="Preferred Contact:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.preferred_contact_var = tk.StringVar()
        preferred_contact_combo = ttk.Combobox(contact_frame, textvariable=self.preferred_contact_var, width=15,
                                               state="readonly")
        preferred_contact_combo["values"] = ["Email", "Phone", "Text", "Mail"]
        preferred_contact_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # System information section
        system_frame = ttk.LabelFrame(form_frame, text="System Information")
        system_frame.pack(fill=tk.X, pady=(0, 10))

        # Status
        ttk.Label(system_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.status_var = tk.StringVar()
        status_combo = ttk.Combobox(system_frame, textvariable=self.status_var, width=15, state="readonly")
        status_values = [s.name for s in CustomerStatus]
        status_combo["values"] = status_values
        status_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # Tier
        ttk.Label(system_frame, text="Tier:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.tier_var = tk.StringVar()
        tier_combo = ttk.Combobox(system_frame, textvariable=self.tier_var, width=15, state="readonly")
        tier_values = [t.name for t in CustomerTier]
        tier_combo["values"] = tier_values
        tier_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Source
        ttk.Label(system_frame, text="Source:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.source_var = tk.StringVar()
        source_combo = ttk.Combobox(system_frame, textvariable=self.source_var, width=15, state="readonly")
        source_values = [s.name for s in CustomerSource]
        source_combo["values"] = source_values
        source_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Created date
        ttk.Label(system_frame, text="Created Date:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.created_date_var = tk.StringVar()
        self.created_date_entry = ttk.Entry(system_frame, textvariable=self.created_date_var, width=20,
                                            state="readonly")
        self.created_date_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Custom fields section
        custom_frame = ttk.LabelFrame(form_frame, text="Custom Fields")
        custom_frame.pack(fill=tk.X)

        # Implement custom fields that can be added dynamically
        self.custom_fields_frame = ttk.Frame(custom_frame)
        self.custom_fields_frame.pack(fill=tk.X, padx=5, pady=5)

        # No custom fields message
        self.no_fields_label = ttk.Label(self.custom_fields_frame, text="No custom fields defined.")
        self.no_fields_label.pack(pady=10)

        # Add custom field button
        ttk.Button(
            custom_frame,
            text="Add Custom Field",
            command=self.add_custom_field
        ).pack(anchor=tk.E, padx=5, pady=5)

    def create_address_tab(self):
        """Create the address tab."""
        address_tab = ttk.Frame(self.notebook)
        self.notebook.add(address_tab, text="Addresses")

        # Create form frame
        form_frame = ttk.Frame(address_tab, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Primary address section
        primary_frame = ttk.LabelFrame(form_frame, text="Primary Address")
        primary_frame.pack(fill=tk.X, pady=(0, 10))

        # Street 1
        ttk.Label(primary_frame, text="Street 1:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.street1_var = tk.StringVar()
        self.street1_entry = ttk.Entry(primary_frame, textvariable=self.street1_var, width=50)
        self.street1_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Street 2
        ttk.Label(primary_frame, text="Street 2:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.street2_var = tk.StringVar()
        self.street2_entry = ttk.Entry(primary_frame, textvariable=self.street2_var, width=50)
        self.street2_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # City
        ttk.Label(primary_frame, text="City:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(primary_frame, textvariable=self.city_var, width=30)
        self.city_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # State/Province
        ttk.Label(primary_frame, text="State/Province:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.state_var = tk.StringVar()
        self.state_entry = ttk.Entry(primary_frame, textvariable=self.state_var, width=20)
        self.state_entry.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        # Postal code
        ttk.Label(primary_frame, text="Postal Code:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.postal_code_var = tk.StringVar()
        self.postal_code_entry = ttk.Entry(primary_frame, textvariable=self.postal_code_var, width=15)
        self.postal_code_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Country
        ttk.Label(primary_frame, text="Country:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.country_var = tk.StringVar()
        self.country_entry = ttk.Entry(primary_frame, textvariable=self.country_var, width=20)
        self.country_entry.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # Shipping address section
        shipping_frame = ttk.LabelFrame(form_frame, text="Shipping Address")
        shipping_frame.pack(fill=tk.X, pady=(0, 10))

        # Same as primary checkbox
        self.same_as_primary_var = tk.BooleanVar(value=True)
        same_as_primary_check = ttk.Checkbutton(
            shipping_frame,
            text="Same as primary address",
            variable=self.same_as_primary_var,
            command=self.toggle_shipping_address
        )
        same_as_primary_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)

        # Shipping street 1
        ttk.Label(shipping_frame, text="Street 1:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ship_street1_var = tk.StringVar()
        self.ship_street1_entry = ttk.Entry(shipping_frame, textvariable=self.ship_street1_var, width=50,
                                            state=tk.DISABLED)
        self.ship_street1_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Shipping street 2
        ttk.Label(shipping_frame, text="Street 2:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.ship_street2_var = tk.StringVar()
        self.ship_street2_entry = ttk.Entry(shipping_frame, textvariable=self.ship_street2_var, width=50,
                                            state=tk.DISABLED)
        self.ship_street2_entry.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Shipping city
        ttk.Label(shipping_frame, text="City:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.ship_city_var = tk.StringVar()
        self.ship_city_entry = ttk.Entry(shipping_frame, textvariable=self.ship_city_var, width=30, state=tk.DISABLED)
        self.ship_city_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Shipping state/province
        ttk.Label(shipping_frame, text="State/Province:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.ship_state_var = tk.StringVar()
        self.ship_state_entry = ttk.Entry(shipping_frame, textvariable=self.ship_state_var, width=20, state=tk.DISABLED)
        self.ship_state_entry.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # Shipping postal code
        ttk.Label(shipping_frame, text="Postal Code:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.ship_postal_code_var = tk.StringVar()
        self.ship_postal_code_entry = ttk.Entry(shipping_frame, textvariable=self.ship_postal_code_var, width=15,
                                                state=tk.DISABLED)
        self.ship_postal_code_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        # Shipping country
        ttk.Label(shipping_frame, text="Country:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        self.ship_country_var = tk.StringVar()
        self.ship_country_entry = ttk.Entry(shipping_frame, textvariable=self.ship_country_var, width=20,
                                            state=tk.DISABLED)
        self.ship_country_entry.grid(row=4, column=3, sticky=tk.W, padx=5, pady=5)

        # Billing address section
        billing_frame = ttk.LabelFrame(form_frame, text="Billing Address")
        billing_frame.pack(fill=tk.X)

        # Same as primary checkbox
        self.same_as_primary_billing_var = tk.BooleanVar(value=True)
        same_as_primary_billing_check = ttk.Checkbutton(
            billing_frame,
            text="Same as primary address",
            variable=self.same_as_primary_billing_var,
            command=self.toggle_billing_address
        )
        same_as_primary_billing_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)

        # Billing street 1
        ttk.Label(billing_frame, text="Street 1:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.bill_street1_var = tk.StringVar()
        self.bill_street1_entry = ttk.Entry(billing_frame, textvariable=self.bill_street1_var, width=50,
                                            state=tk.DISABLED)
        self.bill_street1_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Billing street 2
        ttk.Label(billing_frame, text="Street 2:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.bill_street2_var = tk.StringVar()
        self.bill_street2_entry = ttk.Entry(billing_frame, textvariable=self.bill_street2_var, width=50,
                                            state=tk.DISABLED)
        self.bill_street2_entry.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Billing city
        ttk.Label(billing_frame, text="City:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.bill_city_var = tk.StringVar()
        self.bill_city_entry = ttk.Entry(billing_frame, textvariable=self.bill_city_var, width=30, state=tk.DISABLED)
        self.bill_city_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Billing state/province
        ttk.Label(billing_frame, text="State/Province:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.bill_state_var = tk.StringVar()
        self.bill_state_entry = ttk.Entry(billing_frame, textvariable=self.bill_state_var, width=20, state=tk.DISABLED)
        self.bill_state_entry.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # Billing postal code
        ttk.Label(billing_frame, text="Postal Code:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.bill_postal_code_var = tk.StringVar()
        self.bill_postal_code_entry = ttk.Entry(billing_frame, textvariable=self.bill_postal_code_var, width=15,
                                                state=tk.DISABLED)
        self.bill_postal_code_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

        # Billing country
        ttk.Label(billing_frame, text="Country:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        self.bill_country_var = tk.StringVar()
        self.bill_country_entry = ttk.Entry(billing_frame, textvariable=self.bill_country_var, width=20,
                                            state=tk.DISABLED)
        self.bill_country_entry.grid(row=4, column=3, sticky=tk.W, padx=5, pady=5)

    def create_purchase_history_tab(self):
        """Create the purchase history tab."""
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="Purchase History")

        # Create summary frame
        summary_frame = ttk.LabelFrame(history_tab, text="Purchase Summary")
        summary_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create grid for summary metrics
        metrics_grid = ttk.Frame(summary_frame)
        metrics_grid.pack(fill=tk.X, padx=10, pady=10)

        # Total purchases
        ttk.Label(metrics_grid, text="Total Purchases:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0,
                                                                                                 padx=5, pady=2,
                                                                                                 sticky=tk.W)
        self.total_purchases_label = ttk.Label(metrics_grid, text="0")
        self.total_purchases_label.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        # Total spent
        ttk.Label(metrics_grid, text="Total Spent:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=2, padx=5,
                                                                                             pady=2, sticky=tk.W)
        self.total_spent_label = ttk.Label(metrics_grid, text="$0.00")
        self.total_spent_label.grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)

        # Average order value
        ttk.Label(metrics_grid, text="Avg. Order Value:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4,
                                                                                                  padx=5, pady=2,
                                                                                                  sticky=tk.W)
        self.avg_order_label = ttk.Label(metrics_grid, text="$0.00")
        self.avg_order_label.grid(row=0, column=5, padx=5, pady=2, sticky=tk.W)

        # First purchase
        ttk.Label(metrics_grid, text="First Purchase:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0, padx=5,
                                                                                                pady=2, sticky=tk.W)
        self.first_purchase_label = ttk.Label(metrics_grid, text="N/A")
        self.first_purchase_label.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        # Last purchase
        ttk.Label(metrics_grid, text="Last Purchase:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=2, padx=5,
                                                                                               pady=2, sticky=tk.W)
        self.last_purchase_label = ttk.Label(metrics_grid, text="N/A")
        self.last_purchase_label.grid(row=1, column=3, padx=5, pady=2, sticky=tk.W)

        # Purchase frequency
        ttk.Label(metrics_grid, text="Purchase Frequency:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=4,
                                                                                                    padx=5, pady=2,
                                                                                                    sticky=tk.W)
        self.frequency_label = ttk.Label(metrics_grid, text="N/A")
        self.frequency_label.grid(row=1, column=5, padx=5, pady=2, sticky=tk.W)

        # Create purchases list
        list_frame = ttk.LabelFrame(history_tab, text="Purchase History")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create treeview for purchases
        columns = ("id", "date", "total", "items", "status", "payment_status")
        self.purchases_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Configure columns
        self.purchases_tree.heading("id", text="Order ID")
        self.purchases_tree.heading("date", text="Date")
        self.purchases_tree.heading("total", text="Total")
        self.purchases_tree.heading("items", text="Items")
        self.purchases_tree.heading("status", text="Status")
        self.purchases_tree.heading("payment_status", text="Payment Status")

        self.purchases_tree.column("id", width=80)
        self.purchases_tree.column("date", width=100)
        self.purchases_tree.column("total", width=100)
        self.purchases_tree.column("items", width=50)
        self.purchases_tree.column("status", width=120)
        self.purchases_tree.column("payment_status", width=120)

        # Add scrollbar
        purchases_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.purchases_tree.yview)
        self.purchases_tree.configure(yscrollcommand=purchases_scroll.set)

        # Pack treeview and scrollbar
        self.purchases_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        purchases_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to view sale details
        self.purchases_tree.bind("<Double-1>", self.on_view_sale)

        # Add action buttons
        actions_frame = ttk.Frame(history_tab)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            actions_frame,
            text="View Sale",
            command=self.on_view_sale
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Create New Sale",
            command=self.on_create_sale
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Export History",
            command=self.on_export_history
        ).pack(side=tk.LEFT, padx=5)

    def create_projects_tab(self):
        """Create the projects tab."""
        projects_tab = ttk.Frame(self.notebook)
        self.notebook.add(projects_tab, text="Projects")

        # Create projects list
        list_frame = ttk.Frame(projects_tab, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview for projects
        columns = ("id", "name", "type", "status", "start_date", "end_date", "total")
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Configure columns
        self.projects_tree.heading("id", text="Project ID")
        self.projects_tree.heading("name", text="Name")
        self.projects_tree.heading("type", text="Type")
        self.projects_tree.heading("status", text="Status")
        self.projects_tree.heading("start_date", text="Start Date")
        self.projects_tree.heading("end_date", text="End Date")
        self.projects_tree.heading("total", text="Total")

        self.projects_tree.column("id", width=80)
        self.projects_tree.column("name", width=200)
        self.projects_tree.column("type", width=100)
        self.projects_tree.column("status", width=120)
        self.projects_tree.column("start_date", width=100)
        self.projects_tree.column("end_date", width=100)
        self.projects_tree.column("total", width=100)

        # Add scrollbar
        projects_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=projects_scroll.set)

        # Pack treeview and scrollbar
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        projects_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to view project details
        self.projects_tree.bind("<Double-1>", self.on_view_project)

        # Add action buttons
        actions_frame = ttk.Frame(projects_tab)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            actions_frame,
            text="View Project",
            command=self.on_view_project
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Create New Project",
            command=self.on_create_project
        ).pack(side=tk.LEFT, padx=5)

    def create_activity_tab(self):
        """Create the activity history tab."""
        activity_tab = ttk.Frame(self.notebook)
        self.notebook.add(activity_tab, text="Activity History")

        # Create activity list
        list_frame = ttk.Frame(activity_tab, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview for activity
        columns = ("date", "type", "description", "user")
        self.activity_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Configure columns
        self.activity_tree.heading("date", text="Date & Time")
        self.activity_tree.heading("type", text="Activity Type")
        self.activity_tree.heading("description", text="Description")
        self.activity_tree.heading("user", text="User")

        self.activity_tree.column("date", width=150)
        self.activity_tree.column("type", width=120)
        self.activity_tree.column("description", width=400)
        self.activity_tree.column("user", width=100)

        # Add scrollbar
        activity_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=activity_scroll.set)

        # Pack treeview and scrollbar
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Add filter controls
        filter_frame = ttk.Frame(activity_tab)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(filter_frame, text="Filter by Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.activity_filter_var = tk.StringVar(value="All")
        activity_combo = ttk.Combobox(filter_frame, textvariable=self.activity_filter_var, width=15, state="readonly")
        activity_values = ["All", "Sale", "Project", "Status Change", "Communication", "System"]
        activity_combo["values"] = activity_values
        activity_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Date Range:").pack(side=tk.LEFT, padx=(15, 5))
        self.activity_date_from_var = tk.StringVar()
        activity_from_entry = ttk.Entry(filter_frame, textvariable=self.activity_date_from_var, width=12)
        activity_from_entry.pack(side=tk.LEFT, padx=(0, 2))

        ttk.Button(
            filter_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.activity_date_from_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(filter_frame, text="to").pack(side=tk.LEFT, padx=5)

        self.activity_date_to_var = tk.StringVar()
        activity_to_entry = ttk.Entry(filter_frame, textvariable=self.activity_date_to_var, width=12)
        activity_to_entry.pack(side=tk.LEFT, padx=(5, 2))

        ttk.Button(
            filter_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.activity_date_to_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            filter_frame,
            text="Apply Filter",
            command=self.on_filter_activity
        ).pack(side=tk.LEFT, padx=15)

        ttk.Button(
            filter_frame,
            text="Export Activity",
            command=self.on_export_activity
        ).pack(side=tk.RIGHT, padx=5)

    def create_notes_tab(self):
        """Create the notes tab."""
        notes_tab = ttk.Frame(self.notebook)
        self.notebook.add(notes_tab, text="Notes")

        # Create notes section
        notes_frame = ttk.Frame(notes_tab, padding=10)
        notes_frame.pack(fill=tk.BOTH, expand=True)

        # Create notes text area
        ttk.Label(notes_frame, text="Customer Notes:").pack(anchor=tk.W, pady=(0, 5))

        self.notes_text = tk.Text(notes_frame, height=15, width=80)
        self.notes_text.pack(fill=tk.BOTH, expand=True)

        # Format toolbar
        toolbar_frame = ttk.Frame(notes_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            toolbar_frame,
            text="Bold",
            command=lambda: self.format_text("bold")
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="Italic",
            command=lambda: self.format_text("italic")
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="Underline",
            command=lambda: self.format_text("underline")
        ).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        ttk.Button(
            toolbar_frame,
            text="Add Date",
            command=self.add_date_to_notes
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="Add Signature",
            command=self.add_signature_to_notes
        ).pack(side=tk.LEFT, padx=2)

        # Add preset note templates
        templates_frame = ttk.LabelFrame(notes_frame, text="Note Templates")
        templates_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            templates_frame,
            text="Follow-up Reminder",
            command=lambda: self.add_note_template("follow_up")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            templates_frame,
            text="Customer Preference",
            command=lambda: self.add_note_template("preference")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            templates_frame,
            text="Special Handling",
            command=lambda: self.add_note_template("special_handling")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(
            templates_frame,
            text="Payment Issue",
            command=lambda: self.add_note_template("payment_issue")
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # Notes history
        history_frame = ttk.LabelFrame(notes_frame, text="Notes History")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview for notes history
        columns = ("date", "user", "note")
        self.notes_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=5)

        # Configure columns
        self.notes_tree.heading("date", text="Date & Time")
        self.notes_tree.heading("user", text="User")
        self.notes_tree.heading("note", text="Note Preview")

        self.notes_tree.column("date", width=150)
        self.notes_tree.column("user", width=100)
        self.notes_tree.column("note", width=450)

        # Add scrollbar
        notes_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.notes_tree.yview)
        self.notes_tree.configure(yscrollcommand=notes_scroll.set)

        # Pack treeview and scrollbar
        self.notes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to view note
        self.notes_tree.bind("<Double-1>", self.on_view_note)

    def create_buttons_section(self, parent):
        """Create buttons section.

        Args:
            parent: The parent widget
        """
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        if self.readonly:
            # Read-only mode buttons
            ttk.Button(
                buttons_frame,
                text="Edit",
                command=self.on_edit
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                buttons_frame,
                text="Close",
                command=self.close
            ).pack(side=tk.RIGHT, padx=5)
        else:
            # Edit mode buttons
            ttk.Button(
                buttons_frame,
                text="Save",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                buttons_frame,
                text="Cancel",
                command=self.close
            ).pack(side=tk.RIGHT, padx=5)

    def load_customer_data(self):
        """Load customer data from the service."""
        try:
            # Get customer data from service
            customer = self.customer_service.get_customer(
                self.customer_id,
                include_address=True,
                include_sales=True,
                include_projects=True,
                include_activity=True,
                include_notes=True
            )

            if not customer:
                messagebox.showerror("Error", f"Customer not found with ID {self.customer_id}")
                self.close()
                return

            # Update window title
            name = ""
            if hasattr(customer, 'first_name') and customer.first_name:
                name += customer.first_name
            if hasattr(customer, 'last_name') and customer.last_name:
                if name:
                    name += " "
                name += customer.last_name

            self.window.title(f"Customer: {name}")

            # Update header section
            self.name_label.configure(text=name)

            if hasattr(customer, 'status') and customer.status:
                status_text = customer.status.value.replace("_", " ").title()
                status_value = customer.status.value
                self.status_badge.set_text(status_text, status_value)

            if hasattr(customer, 'tier') and customer.tier:
                self.tier_label.configure(text=customer.tier.value.title())

            # Populate basic info tab
            if hasattr(customer, 'first_name'):
                self.first_name_var.set(customer.first_name or "")

            if hasattr(customer, 'last_name'):
                self.last_name_var.set(customer.last_name or "")

            if hasattr(customer, 'email'):
                self.email_var.set(customer.email or "")

            if hasattr(customer, 'phone'):
                self.phone_var.set(customer.phone or "")

            if hasattr(customer, 'alt_phone'):
                self.alt_phone_var.set(customer.alt_phone or "")

            if hasattr(customer, 'date_of_birth') and customer.date_of_birth:
                self.dob_var.set(customer.date_of_birth.strftime("%Y-%m-%d"))

            if hasattr(customer, 'gender'):
                self.gender_var.set(customer.gender or "")

            if hasattr(customer, 'preferred_contact'):
                self.preferred_contact_var.set(customer.preferred_contact or "")

            if hasattr(customer, 'status') and customer.status:
                self.status_var.set(customer.status.name)

            if hasattr(customer, 'tier') and customer.tier:
                self.tier_var.set(customer.tier.name)

            if hasattr(customer, 'source') and customer.source:
                self.source_var.set(customer.source.name)

            if hasattr(customer, 'created_at') and customer.created_at:
                self.created_date_var.set(customer.created_at.strftime("%Y-%m-%d %H:%M"))

            # Populate address tab
            if hasattr(customer, 'address'):
                address = customer.address

                # Primary address
                if hasattr(address, 'street1'):
                    self.street1_var.set(address.street1 or "")

                if hasattr(address, 'street2'):
                    self.street2_var.set(address.street2 or "")

                if hasattr(address, 'city'):
                    self.city_var.set(address.city or "")

                if hasattr(address, 'state'):
                    self.state_var.set(address.state or "")

                if hasattr(address, 'postal_code'):
                    self.postal_code_var.set(address.postal_code or "")

                if hasattr(address, 'country'):
                    self.country_var.set(address.country or "")

                # Shipping address
                if hasattr(address, 'ship_street1') and address.ship_street1:
                    self.same_as_primary_var.set(False)
                    self.toggle_shipping_address()

                    self.ship_street1_var.set(address.ship_street1 or "")
                    self.ship_street2_var.set(address.ship_street2 or "")
                    self.ship_city_var.set(address.ship_city or "")
                    self.ship_state_var.set(address.ship_state or "")
                    self.ship_postal_code_var.set(address.ship_postal_code or "")
                    self.ship_country_var.set(address.ship_country or "")

                # Billing address
                if hasattr(address, 'bill_street1') and address.bill_street1:
                    self.same_as_primary_billing_var.set(False)
                    self.toggle_billing_address()

                    self.bill_street1_var.set(address.bill_street1 or "")
                    self.bill_street2_var.set(address.bill_street2 or "")
                    self.bill_city_var.set(address.bill_city or "")
                    self.bill_state_var.set(address.bill_state or "")
                    self.bill_postal_code_var.set(address.bill_postal_code or "")
                    self.bill_country_var.set(address.bill_country or "")

            # Load purchase history
            self.load_purchase_history(customer)

            # Load projects
            self.load_projects(customer)

            # Load activity history
            self.load_activity_history(customer)

            # Load notes
            self.load_notes(customer)

        except Exception as e:
            self.logger.error(f"Error loading customer data: {e}")
            messagebox.showerror("Error", f"Failed to load customer data: {str(e)}")

    def load_purchase_history(self, customer):
        """Load purchase history data.

        Args:
            customer: Customer data object
        """
        try:
            # Update purchase summary
            if hasattr(customer, 'sales_summary'):
                summary = customer.sales_summary

                if 'total_purchases' in summary:
                    self.total_purchases_label.configure(text=str(summary['total_purchases']))

                if 'total_spent' in summary:
                    self.total_spent_label.configure(text=f"${summary['total_spent']:.2f}")

                if 'average_order' in summary:
                    self.avg_order_label.configure(text=f"${summary['average_order']:.2f}")

                if 'first_purchase_date' in summary and summary['first_purchase_date']:
                    self.first_purchase_label.configure(text=summary['first_purchase_date'].strftime("%Y-%m-%d"))

                if 'last_purchase_date' in summary and summary['last_purchase_date']:
                    self.last_purchase_label.configure(text=summary['last_purchase_date'].strftime("%Y-%m-%d"))

                if 'purchase_frequency' in summary:
                    if summary['purchase_frequency'] == 0:
                        self.frequency_label.configure(text="N/A")
                    else:
                        # Convert days to a more readable format
                        days = summary['purchase_frequency']
                        if days < 30:
                            self.frequency_label.configure(text=f"{days:.1f} days")
                        elif days < 365:
                            self.frequency_label.configure(text=f"{days / 30:.1f} months")
                        else:
                            self.frequency_label.configure(text=f"{days / 365:.1f} years")

            # Update purchases list
            for item in self.purchases_tree.get_children():
                self.purchases_tree.delete(item)

            if hasattr(customer, 'sales') and customer.sales:
                for sale in customer.sales:
                    # Format date
                    date = ""
                    if hasattr(sale, 'created_at') and sale.created_at:
                        date = sale.created_at.strftime("%Y-%m-%d")

                    # Format total
                    total = "$0.00"
                    if hasattr(sale, 'total_amount'):
                        total = f"${sale.total_amount:.2f}"

                    # Format item count
                    items = "0"
                    if hasattr(sale, 'items') and sale.items:
                        items = str(len(sale.items))
                    elif hasattr(sale, 'item_count'):
                        items = str(sale.item_count)

                    # Format status
                    status = ""
                    if hasattr(sale, 'status') and sale.status:
                        status = sale.status.value.replace("_", " ").title()

                    # Format payment status
                    payment_status = ""
                    if hasattr(sale, 'payment_status') and sale.payment_status:
                        payment_status = sale.payment_status.value.replace("_", " ").title()

                    sale_id = sale.id if hasattr(sale, 'id') else ""
                    self.purchases_tree.insert('', 'end', iid=str(sale_id), values=(
                        sale_id, date, total, items, status, payment_status
                    ))

        except Exception as e:
            self.logger.error(f"Error loading purchase history: {e}")

    def load_projects(self, customer):
        """Load projects data.

        Args:
            customer: Customer data object
        """
        try:
            # Update projects list
            for item in self.projects_tree.get_children():
                self.projects_tree.delete(item)

            if hasattr(customer, 'projects') and customer.projects:
                for project in customer.projects:
                    # Format dates
                    start_date = ""
                    if hasattr(project, 'start_date') and project.start_date:
                        start_date = project.start_date.strftime("%Y-%m-%d")

                    end_date = ""
                    if hasattr(project, 'end_date') and project.end_date:
                        end_date = project.end_date.strftime("%Y-%m-%d")

                    # Format type
                    project_type = ""
                    if hasattr(project, 'type') and project.type:
                        project_type = project.type.value.replace("_", " ").title()

                    # Format status
                    status = ""
                    if hasattr(project, 'status') and project.status:
                        status = project.status.value.replace("_", " ").title()

                    # Format total
                    total = "$0.00"
                    if hasattr(project, 'total_cost'):
                        total = f"${project.total_cost:.2f}"
                    elif hasattr(project, 'budget') and project.budget:
                        total = f"${project.budget:.2f}"

                    project_id = project.id if hasattr(project, 'id') else ""
                    project_name = project.name if hasattr(project, 'name') else ""

                    self.projects_tree.insert('', 'end', iid=str(project_id), values=(
                        project_id, project_name, project_type, status, start_date, end_date, total
                    ))

        except Exception as e:
            self.logger.error(f"Error loading projects: {e}")

    def load_activity_history(self, customer):
        """Load activity history data.

        Args:
            customer: Customer data object
        """
        try:
            # Update activity list
            for item in self.activity_tree.get_children():
                self.activity_tree.delete(item)

            if hasattr(customer, 'activity') and customer.activity:
                for idx, activity in enumerate(customer.activity):
                    # Format date
                    date = ""
                    if hasattr(activity, 'timestamp') and activity.timestamp:
                        date = activity.timestamp.strftime("%Y-%m-%d %H:%M")

                    # Extract data
                    activity_type = activity.type if hasattr(activity, 'type') else ""
                    description = activity.description if hasattr(activity, 'description') else ""
                    user = activity.user if hasattr(activity, 'user') else ""

                    self.activity_tree.insert('', 'end', iid=str(idx), values=(
                        date, activity_type, description, user
                    ))

        except Exception as e:
            self.logger.error(f"Error loading activity history: {e}")

    def load_notes(self, customer):
        """Load notes data.

        Args:
            customer: Customer data object
        """
        try:
            # Update current notes
            self.notes_text.delete("1.0", tk.END)

            if hasattr(customer, 'notes') and customer.notes:
                self.notes_text.insert("1.0", customer.notes)

            # Update notes history
            for item in self.notes_tree.get_children():
                self.notes_tree.delete(item)

            if hasattr(customer, 'notes_history') and customer.notes_history:
                for idx, note in enumerate(customer.notes_history):
                    # Format date
                    date = ""
                    if hasattr(note, 'timestamp') and note.timestamp:
                        date = note.timestamp.strftime("%Y-%m-%d %H:%M")

                    # Extract data
                    user = note.user if hasattr(note, 'user') else ""

                    # Preview of note content
                    preview = note.content if hasattr(note, 'content') else ""
                    if len(preview) > 50:
                        preview = preview[:47] + "..."

                    self.notes_tree.insert('', 'end', iid=str(idx), values=(
                        date, user, preview
                    ))

        except Exception as e:
            self.logger.error(f"Error loading notes: {e}")

    def update_ui_state(self):
        """Update UI elements based on current state (readonly/edit)."""
        state = tk.DISABLED if self.readonly else tk.NORMAL

        # Update basic info tab fields
        self.first_name_entry.configure(state=state)
        self.last_name_entry.configure(state=state)
        self.email_entry.configure(state=state)
        self.phone_entry.configure(state=state)
        self.alt_phone_entry.configure(state=state)
        self.dob_entry.configure(state=state)

        # Update address tab fields
        self.street1_entry.configure(state=state)
        self.street2_entry.configure(state=state)
        self.city_entry.configure(state=state)
        self.state_entry.configure(state=state)
        self.postal_code_entry.configure(state=state)
        self.country_entry.configure(state=state)

        # Update notes
        self.notes_text.configure(state=state)

    def toggle_shipping_address(self):
        """Toggle shipping address fields based on checkbox state."""
        if self.readonly:
            return

        if self.same_as_primary_var.get():
            # Disable shipping address fields
            self.ship_street1_entry.configure(state=tk.DISABLED)
            self.ship_street2_entry.configure(state=tk.DISABLED)
            self.ship_city_entry.configure(state=tk.DISABLED)
            self.ship_state_entry.configure(state=tk.DISABLED)
            self.ship_postal_code_entry.configure(state=tk.DISABLED)
            self.ship_country_entry.configure(state=tk.DISABLED)
        else:
            # Enable shipping address fields
            self.ship_street1_entry.configure(state=tk.NORMAL)
            self.ship_street2_entry.configure(state=tk.NORMAL)
            self.ship_city_entry.configure(state=tk.NORMAL)
            self.ship_state_entry.configure(state=tk.NORMAL)
            self.ship_postal_code_entry.configure(state=tk.NORMAL)
            self.ship_country_entry.configure(state=tk.NORMAL)

    def toggle_billing_address(self):
        """Toggle billing address fields based on checkbox state."""
        if self.readonly:
            return

        if self.same_as_primary_billing_var.get():
            # Disable billing address fields
            self.bill_street1_entry.configure(state=tk.DISABLED)
            self.bill_street2_entry.configure(state=tk.DISABLED)
            self.bill_city_entry.configure(state=tk.DISABLED)
            self.bill_state_entry.configure(state=tk.DISABLED)
            self.bill_postal_code_entry.configure(state=tk.DISABLED)
            self.bill_country_entry.configure(state=tk.DISABLED)
        else:
            # Enable billing address fields
            self.bill_street1_entry.configure(state=tk.NORMAL)
            self.bill_street2_entry.configure(state=tk.NORMAL)
            self.bill_city_entry.configure(state=tk.NORMAL)
            self.bill_state_entry.configure(state=tk.NORMAL)
            self.bill_postal_code_entry.configure(state=tk.NORMAL)
            self.bill_country_entry.configure(state=tk.NORMAL)

    def add_custom_field(self):
        """Add a custom field to the customer data."""
        if self.readonly:
            return

        # Create custom field dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Custom Field")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.geometry("400x200")

        # Field name
        ttk.Label(dialog, text="Field Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        # Field value
        ttk.Label(dialog, text="Field Value:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        value_var = tk.StringVar()
        value_entry = ttk.Entry(dialog, textvariable=value_var, width=30)
        value_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Field type
        ttk.Label(dialog, text="Field Type:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        type_var = tk.StringVar(value="Text")
        type_combo = ttk.Combobox(dialog, textvariable=type_var, width=15, state="readonly")
        type_combo["values"] = ["Text", "Number", "Date", "Boolean"]
        type_combo.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        def on_add_field():
            # Validate input
            if not name_var.get():
                messagebox.showwarning("Input Error", "Please enter a field name.", parent=dialog)
                return

            # Remove no fields message if present
            if self.no_fields_label.winfo_exists():
                self.no_fields_label.destroy()

            # Create a new custom field row
            row_frame = ttk.Frame(self.custom_fields_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(row_frame, text=f"{name_var.get()}:", width=20).pack(side=tk.LEFT, padx=5)

            if type_var.get() == "Boolean":
                # Boolean field
                bool_var = tk.BooleanVar(value=value_var.get().lower() in ('true', 'yes', '1'))
                ttk.Checkbutton(row_frame, variable=bool_var).pack(side=tk.LEFT)
            elif type_var.get() == "Date":
                # Date field
                date_var = tk.StringVar(value=value_var.get())
                date_frame = ttk.Frame(row_frame)
                date_frame.pack(side=tk.LEFT)

                date_entry = ttk.Entry(date_frame, textvariable=date_var, width=12)
                date_entry.pack(side=tk.LEFT)

                ttk.Button(
                    date_frame,
                    text="...",
                    width=2,
                    command=lambda v=date_var: self.show_date_picker(v)
                ).pack(side=tk.LEFT, padx=(5, 0))
            else:
                # Text or number field
                field_var = tk.StringVar(value=value_var.get())
                ttk.Entry(row_frame, textvariable=field_var, width=30).pack(side=tk.LEFT)

            # Add delete button
            ttk.Button(
                row_frame,
                text="×",
                width=2,
                command=lambda f=row_frame: f.destroy()
            ).pack(side=tk.RIGHT, padx=5)

            # Close dialog
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="Add",
            command=on_add_field
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Set focus to name entry
        name_entry.focus_set()

    def format_text(self, format_type):
        """Apply formatting to selected text in notes.

        Args:
            format_type: The type of formatting to apply (bold, italic, underline)
        """
        if self.readonly:
            return

        # Get selected text
        try:
            selected_text = self.notes_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            # No selection
            return

        # Apply formatting
        formatted_text = selected_text
        if format_type == "bold":
            formatted_text = f"**{selected_text}**"
        elif format_type == "italic":
            formatted_text = f"*{selected_text}*"
        elif format_type == "underline":
            formatted_text = f"_{selected_text}_"

        # Replace selected text with formatted text
        self.notes_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.notes_text.insert(tk.INSERT, formatted_text)

    def add_date_to_notes(self):
        """Add current date to notes at cursor position."""
        if self.readonly:
            return

        # Get current date and time
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M")

        # Insert at cursor position
        self.notes_text.insert(tk.INSERT, f"[{date_str}] ")

    def add_signature_to_notes(self):
        """Add user signature to notes at cursor position."""
        if self.readonly:
            return

        # Get current user (would come from user service in production)
        user = "User"  # Placeholder

        # Get current date
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        # Insert signature
        signature = f"\n\n-- {user} ({date_str})"
        self.notes_text.insert(tk.INSERT, signature)

    def add_note_template(self, template_type):
        """Add a note template to the notes area.

        Args:
            template_type: The type of template to add
        """
        if self.readonly:
            return

        # Get current date
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        # Define templates
        templates = {
            "follow_up": f"[{date_str}] Follow-up Reminder: Contact customer by [DATE] regarding [TOPIC].",
            "preference": f"[{date_str}] Customer Preference: Customer prefers [PREFERENCE].",
            "special_handling": f"[{date_str}] Special Handling: This customer requires [SPECIAL_HANDLING].",
            "payment_issue": f"[{date_str}] Payment Issue: [DESCRIPTION]. Follow up by [DATE]."
        }

        # Insert template at cursor position
        if template_type in templates:
            self.notes_text.insert(tk.INSERT, templates[template_type] + "\n\n")

    def on_view_note(self, event=None):
        """Handle viewing a note from history.

        Args:
            event: The event that triggered this action
        """
        selected_id = self.notes_tree.focus()
        if not selected_id:
            return

        # This would show the full note in a dialog
        # For this implementation, we'll just show a message
        item = self.notes_tree.item(selected_id)
        note_date = item["values"][0] if item and "values" in item and len(item["values"]) > 0 else ""
        note_user = item["values"][1] if item and "values" in item and len(item["values"]) > 1 else ""

        messagebox.showinfo(
            "Note Details",
            f"Note from {note_user} on {note_date}\n\nFull note content would be displayed here."
        )

    def on_filter_activity(self):
        """Handle activity filter button click."""
        # This would apply filters to the activity list
        # For this implementation, we'll just show a message
        messagebox.showinfo(
            "Filter Activity",
            "Activity list would be filtered based on selected criteria."
        )

    def on_export_activity(self):
        """Handle export activity button click."""
        # This would export activity to a file
        # For this implementation, we'll just show a message
        messagebox.showinfo(
            "Export Activity",
            "Activity history would be exported to a file."
        )

    def on_export_history(self):
        """Handle export purchase history button click."""
        # This would export purchase history to a file
        # For this implementation, we'll just show a message
        messagebox.showinfo(
            "Export History",
            "Purchase history would be exported to a file."
        )

    def on_view_sale(self, event=None):
        """Handle view sale button click.

        Args:
            event: The event that triggered this action
        """
        selected_id = self.purchases_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a sale to view.")
            return

        # Close dialog and navigate to sale details
        self.result = {"action": "view_sale", "sale_id": int(selected_id)}
        self.close()

    def on_create_sale(self):
        """Handle create new sale button click."""
        # Close dialog and navigate to new sale
        self.result = {"action": "create_sale", "customer_id": self.customer_id}
        self.close()

    def on_view_project(self, event=None):
        """Handle view project button click.

        Args:
            event: The event that triggered this action
        """
        selected_id = self.projects_tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a project to view.")
            return

        # Close dialog and navigate to project details
        self.result = {"action": "view_project", "project_id": int(selected_id)}
        self.close()

    def on_create_project(self):
        """Handle create new project button click."""
        # Close dialog and navigate to new project
        self.result = {"action": "create_project", "customer_id": self.customer_id}
        self.close()

    def on_edit(self):
        """Handle edit button click from read-only mode."""
        # Close dialog and reopen in edit mode
        self.result = {"action": "edit", "customer_id": self.customer_id}
        self.close()

    def on_save(self):
        """Handle save button click."""
        try:
            # Validate form
            if not self.validate_form():
                return

            # Collect customer data
            customer_data = self.collect_form_data()

            # Save customer
            if self.create_new:
                # Create new customer
                result = self.customer_service.create_customer(customer_data)
                if result:
                    self.customer_id = result.id
                    self.result = {"success": True, "customer_id": self.customer_id}

                    # Show success message
                    messagebox.showinfo("Success", "Customer has been created successfully.")

                    # Publish event
                    publish("customer_created", {"customer_id": self.customer_id})

                    # Close dialog
                    self.close()
            else:
                # Update existing customer
                result = self.customer_service.update_customer(self.customer_id, customer_data)
                if result:
                    self.result = {"success": True, "customer_id": self.customer_id}

                    # Show success message
                    messagebox.showinfo("Success", "Customer has been updated successfully.")

                    # Publish event
                    publish("customer_updated", {"customer_id": self.customer_id})

                    # Close dialog
                    self.close()

        except Exception as e:
            self.logger.error(f"Error saving customer: {e}")
            messagebox.showerror("Save Error", f"Failed to save customer: {str(e)}")

    def validate_form(self):
        """Validate the form data.

        Returns:
            True if the form is valid, False otherwise
        """
        # Basic validation
        if not self.first_name_var.get() and not self.last_name_var.get():
            messagebox.showwarning("Validation Error", "Please enter either a first name or last name.")
            return False

        if not self.email_var.get() and not self.phone_var.get():
            messagebox.showwarning("Validation Error", "Please enter either an email or phone number.")
            return False

        # Email format validation (basic)
        if self.email_var.get() and "@" not in self.email_var.get():
            messagebox.showwarning("Validation Error", "Please enter a valid email address.")
            return False

        # Status validation
        if not self.status_var.get():
            messagebox.showwarning("Validation Error", "Please select a customer status.")
            return False

        # Tier validation
        if not self.tier_var.get():
            messagebox.showwarning("Validation Error", "Please select a customer tier.")
            return False

        return True

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

        # Add billing address if different from primary
        if not self.same_as_primary_billing_var.get():
            address_data.update({
                "bill_street1": self.bill_street1_var.get(),
                "bill_street2": self.bill_street2_var.get(),
                "bill_city": self.bill_city_var.get(),
                "bill_state": self.bill_state_var.get(),
                "bill_postal_code": self.bill_postal_code_var.get(),
                "bill_country": self.bill_country_var.get()
            })

        # Add address to customer data
        data["address"] = address_data

        # Add customer preferences
        data["preferred_contact"] = self.preferred_contact_var.get()

        # TODO: Add custom fields

        return data

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create a simple date picker dialog
        date_dialog = tk.Toplevel(self.window)
        date_dialog.title("Select Date")
        date_dialog.transient(self.window)
        date_dialog.grab_set()

        # Create a calendar (simplified version - production would use a better calendar)
        cal_frame = ttk.Frame(date_dialog, padding=10)
        cal_frame.pack(fill=tk.BOTH, expand=True)

        # Current year and month selection
        current_date = datetime.datetime.now()
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d")
            except ValueError:
                pass

        year_var = tk.StringVar(value=str(current_date.year))
        month_var = tk.StringVar(value=str(current_date.month))

        header_frame = ttk.Frame(cal_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Year:").pack(side=tk.LEFT)
        ttk.Spinbox(
            header_frame,
            from_=1900,
            to=2100,
            textvariable=year_var,
            width=5
        ).pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(header_frame, text="Month:").pack(side=tk.LEFT)
        month_spin = ttk.Spinbox(
            header_frame,
            from_=1,
            to=12,
            textvariable=month_var,
            width=3
        )
        month_spin.pack(side=tk.LEFT, padx=5)

        # Simple calendar grid (would use a proper calendar widget in production)
        def select_date(day):
            year = int(year_var.get())
            month = int(month_var.get())
            date_var.set(f"{year:04d}-{month:02d}-{day:02d}")
            date_dialog.destroy()

        days_frame = ttk.Frame(cal_frame)
        days_frame.pack(fill=tk.BOTH, expand=True)

        # Button for each day (simplified)
        for day in range(1, 32):
            day_btn = ttk.Button(
                days_frame,
                text=str(day),
                width=3,
                command=lambda d=day: select_date(d)
            )
            row = (day - 1) // 7
            col = (day - 1) % 7
            day_btn.grid(row=row, column=col, padx=2, pady=2)

        # Cancel button
        ttk.Button(
            cal_frame,
            text="Cancel",
            command=date_dialog.destroy
        ).pack(pady=10)