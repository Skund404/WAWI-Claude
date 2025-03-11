# gui/views/sales/sales_details_view.py
"""
Sales details view for the leatherworking application.

This view provides a comprehensive interface for viewing and editing
individual sale details including customer information, line items,
payment details, and status management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import Any, Dict, List, Optional, Tuple
import logging

# Import GUI components
from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.widgets.status_badge import StatusBadge

# Import services and utilities
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish, subscribe, unsubscribe

# Import model enums
from database.models.enums import SaleStatus, PaymentStatus


class SalesDetailsView(BaseView):
    """
    Sales details view for viewing and editing individual sales.

    This view provides a comprehensive interface for managing sale details,
    including customer information, line items, payment details, and order status.
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the sales details view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                sale_id: ID of the sale to view/edit (None for new sales)
                create_new: Whether to create a new sale
                readonly: Whether the view should be read-only
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing SalesDetailsView")

        # Extract parameters
        self.sale_id = kwargs.pop('sale_id', None)
        self.create_new = kwargs.pop('create_new', False)
        self.readonly = kwargs.pop('readonly', False)

        # Default title
        self.title = "Sale Details"

        # Initialize base class
        super().__init__(parent)

        # Initialize services
        self.sales_service = get_service("sales_service")
        self.customer_service = get_service("customer_service")
        self.product_service = get_service("product_service")
        self.inventory_service = get_service("inventory_service")

        # Initialize data containers
        self.sale_data = None
        self.line_items = []
        self.customer_data = None

        # Initialize form variables
        self._initialize_form_variables()

        # Load data if editing existing sale
        if self.sale_id:
            self.load_sale()
        elif self.create_new:
            self.title = "New Sale"
            self.readonly = False
            self._initialize_new_sale()

    def _initialize_form_variables(self):
        """Initialize form variables for data binding."""
        # Sale information variables
        self.sale_number_var = tk.StringVar()
        self.sale_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.payment_status_var = tk.StringVar()
        self.subtotal_var = tk.StringVar(value="$0.00")
        self.tax_var = tk.StringVar(value="$0.00")
        self.shipping_var = tk.StringVar(value="$0.00")
        self.discount_var = tk.StringVar(value="$0.00")
        self.total_var = tk.StringVar(value="$0.00")
        self.notes_var = tk.StringVar()

        # Customer information variables
        self.customer_id_var = tk.StringVar()
        self.customer_name_var = tk.StringVar()
        self.customer_email_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()

        # Shipping information variables
        self.ship_name_var = tk.StringVar()
        self.ship_street1_var = tk.StringVar()
        self.ship_street2_var = tk.StringVar()
        self.ship_city_var = tk.StringVar()
        self.ship_state_var = tk.StringVar()
        self.ship_postal_code_var = tk.StringVar()
        self.ship_country_var = tk.StringVar()

        # Payment information variables
        self.payment_method_var = tk.StringVar()
        self.payment_reference_var = tk.StringVar()
        self.payment_amount_var = tk.StringVar(value="$0.00")
        self.payment_date_var = tk.StringVar()
        self.payment_notes_var = tk.StringVar()

    def _initialize_new_sale(self):
        """Initialize data for a new sale."""
        # Set default values
        self.sale_date_var.set(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.status_var.set(SaleStatus.QUOTE_REQUEST.value)
        self.payment_status_var.set(PaymentStatus.PENDING.value)

        # Create empty line items list
        self.line_items = []

    def build(self):
        """Build the sales details view layout."""
        self.logger.debug("Building SalesDetailsView layout")

        # Create the header with title and action buttons
        self.create_header()

        # Create main content frame with scrolling
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create a canvas with scrollbar for scrolling
        canvas = tk.Canvas(self.main_container, bg=COLORS["bg_color"])
        scrollbar = ttk.Scrollbar(self.main_container, orient=tk.VERTICAL, command=canvas.yview)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create frame inside canvas for content
        self.content_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)

        # Configure content frame width to match canvas
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # Create a tabbed interface
        self.tab_control = ttk.Notebook(self.content_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.create_order_tab()
        self.create_line_items_tab()
        self.create_customer_tab()
        self.create_payment_tab()
        self.create_status_history_tab()

        # Add mouse wheel scrolling to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Create action buttons area at bottom
        self.create_action_buttons()

        # Update fields in readonly mode
        if self.readonly:
            self._set_readonly_mode()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        if self.readonly:
            # Add Edit button in readonly mode
            self.add_header_button("Edit", self.on_edit, icon="edit", primary=True)
        else:
            # Add Back button
            self.add_header_button("Back", self.on_back, icon="arrow-left")

    def create_order_tab(self):
        """Create the order information tab."""
        order_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(order_tab, text="Order Information")

        # Create header and status section
        header_frame = ttk.Frame(order_tab)
        header_frame.pack(fill=tk.X, pady=10)

        # Order number and date
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Sale number
        number_frame = ttk.Frame(info_frame)
        number_frame.pack(fill=tk.X, pady=5)

        ttk.Label(number_frame, text="Sale #:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        sale_number_entry = ttk.Entry(
            number_frame,
            textvariable=self.sale_number_var,
            state="readonly",
            width=15
        )
        sale_number_entry.pack(side=tk.LEFT, padx=5)

        # Sale date
        date_frame = ttk.Frame(info_frame)
        date_frame.pack(fill=tk.X, pady=5)

        ttk.Label(date_frame, text="Date:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        date_entry = ttk.Entry(
            date_frame,
            textvariable=self.sale_date_var,
            state="readonly" if self.readonly else "normal",
            width=20
        )
        date_entry.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            date_button = ttk.Button(
                date_frame,
                text="📅",
                width=3,
                command=lambda: self.show_date_picker(self.sale_date_var)
            )
            date_button.pack(side=tk.LEFT)

        # Status section
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        # Sale status
        sale_status_frame = ttk.Frame(status_frame)
        sale_status_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sale_status_frame, text="Status:").pack(side=tk.LEFT)

        if self.readonly:
            status_value = self.status_var.get()
            status_style = get_status_style(status_value)

            status_badge = StatusBadge(
                sale_status_frame,
                text=status_value,
                bg_color=status_style.get("bg", COLORS["accent_light"]),
                fg_color=status_style.get("fg", COLORS["text_dark"])
            )
            status_badge.pack(side=tk.LEFT, padx=5)
        else:
            status_combo = ttk.Combobox(
                sale_status_frame,
                textvariable=self.status_var,
                values=[s.value for s in SaleStatus],
                state="readonly",
                width=20
            )
            status_combo.pack(side=tk.LEFT, padx=5)

        # Payment status
        payment_status_frame = ttk.Frame(status_frame)
        payment_status_frame.pack(fill=tk.X, pady=5)

        ttk.Label(payment_status_frame, text="Payment:").pack(side=tk.LEFT)

        if self.readonly:
            payment_value = self.payment_status_var.get()
            payment_style = get_status_style(payment_value)

            payment_badge = StatusBadge(
                payment_status_frame,
                text=payment_value,
                bg_color=payment_style.get("bg", COLORS["accent_light"]),
                fg_color=payment_style.get("fg", COLORS["text_dark"])
            )
            payment_badge.pack(side=tk.LEFT, padx=5)
        else:
            payment_combo = ttk.Combobox(
                payment_status_frame,
                textvariable=self.payment_status_var,
                values=[s.value for s in PaymentStatus],
                state="readonly",
                width=20
            )
            payment_combo.pack(side=tk.LEFT, padx=5)

        # Create separator
        ttk.Separator(order_tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Create totals section
        totals_frame = ttk.Frame(order_tab)
        totals_frame.pack(fill=tk.X, padx=10, pady=10)

        # Configure grid columns
        totals_frame.columnconfigure(0, weight=1)  # Left section
        totals_frame.columnconfigure(1, weight=0)  # Right section (fixed width)

        # Notes section (left)
        notes_frame = ttk.LabelFrame(totals_frame, text="Notes")
        notes_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))

        self.notes_text = tk.Text(
            notes_frame,
            height=8,
            width=40,
            wrap=tk.WORD,
            state=tk.NORMAL if not self.readonly else tk.DISABLED
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # If we have notes data, insert it
        if self.notes_var.get():
            self.notes_text.insert("1.0", self.notes_var.get())

        # Totals summary (right)
        summary_frame = ttk.LabelFrame(totals_frame, text="Order Summary")
        summary_frame.grid(row=0, column=1, sticky=tk.NSEW)

        # Subtotal
        subtotal_frame = ttk.Frame(summary_frame)
        subtotal_frame.pack(fill=tk.X, pady=2)

        ttk.Label(subtotal_frame, text="Subtotal:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        subtotal_entry = ttk.Entry(
            subtotal_frame,
            textvariable=self.subtotal_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        subtotal_entry.pack(side=tk.LEFT, padx=5)

        # Tax
        tax_frame = ttk.Frame(summary_frame)
        tax_frame.pack(fill=tk.X, pady=2)

        ttk.Label(tax_frame, text="Tax:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        tax_entry = ttk.Entry(
            tax_frame,
            textvariable=self.tax_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        tax_entry.pack(side=tk.LEFT, padx=5)

        # Shipping
        shipping_frame = ttk.Frame(summary_frame)
        shipping_frame.pack(fill=tk.X, pady=2)

        ttk.Label(shipping_frame, text="Shipping:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        shipping_entry = ttk.Entry(
            shipping_frame,
            textvariable=self.shipping_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        shipping_entry.pack(side=tk.LEFT, padx=5)

        # Discount
        discount_frame = ttk.Frame(summary_frame)
        discount_frame.pack(fill=tk.X, pady=2)

        ttk.Label(discount_frame, text="Discount:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        discount_entry = ttk.Entry(
            discount_frame,
            textvariable=self.discount_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        discount_entry.pack(side=tk.LEFT, padx=5)

        # Separator before total
        ttk.Separator(summary_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Total
        total_frame = ttk.Frame(summary_frame)
        total_frame.pack(fill=tk.X, pady=2)

        ttk.Label(total_frame, text="Total:", width=12, anchor=tk.E, style="Bold.TLabel").pack(side=tk.LEFT)

        total_entry = ttk.Entry(
            total_frame,
            textvariable=self.total_var,
            state="readonly",
            width=15,
            font=("Arial", 10, "bold")
        )
        total_entry.pack(side=tk.LEFT, padx=5)

        # Calculation helpers if not readonly
        if not self.readonly:
            # Add recalculate button
            ttk.Button(
                summary_frame,
                text="Recalculate",
                command=self.recalculate_totals
            ).pack(fill=tk.X, padx=5, pady=10)

    def create_line_items_tab(self):
        """Create the line items tab."""
        line_items_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(line_items_tab, text="Line Items")

        # Create toolbar for items
        toolbar = ttk.Frame(line_items_tab)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        if not self.readonly:
            # Add item button
            add_btn = ttk.Button(
                toolbar,
                text="Add Item",
                command=self.on_add_item
            )
            add_btn.pack(side=tk.LEFT, padx=5)

            # Edit item button
            self.edit_item_btn = ttk.Button(
                toolbar,
                text="Edit Item",
                command=self.on_edit_item,
                state=tk.DISABLED
            )
            self.edit_item_btn.pack(side=tk.LEFT, padx=5)

            # Remove item button
            self.remove_item_btn = ttk.Button(
                toolbar,
                text="Remove Item",
                command=self.on_remove_item,
                state=tk.DISABLED
            )
            self.remove_item_btn.pack(side=tk.LEFT, padx=5)

        # Create treeview for line items
        tree_frame = ttk.Frame(line_items_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview with scrollbars
        columns = ("id", "product", "description", "quantity", "price", "total")

        self.items_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Configure scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.items_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.items_tree.pack(fill=tk.BOTH, expand=True)

        # Set column headings
        self.items_tree.heading("id", text="ID")
        self.items_tree.heading("product", text="Product")
        self.items_tree.heading("description", text="Description")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.heading("price", text="Unit Price")
        self.items_tree.heading("total", text="Total")

        # Set column widths
        self.items_tree.column("id", width=50, stretch=False)
        self.items_tree.column("product", width=150)
        self.items_tree.column("description", width=250)
        self.items_tree.column("quantity", width=80, anchor=tk.E)
        self.items_tree.column("price", width=100, anchor=tk.E)
        self.items_tree.column("total", width=100, anchor=tk.E)

        # Bind events
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.items_tree.bind("<Double-1>", self.on_item_double_click)

        # Load line items if available
        self.update_line_items_tree()

    def create_customer_tab(self):
        """Create the customer information tab."""
        customer_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(customer_tab, text="Customer & Shipping")

        # Create customer information section
        customer_frame = ttk.LabelFrame(customer_tab, text="Customer Information")
        customer_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)

        # Customer header with selection
        customer_header = ttk.Frame(customer_frame)
        customer_header.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(customer_header, text="Customer:").pack(side=tk.LEFT)

        customer_entry = ttk.Entry(
            customer_header,
            textvariable=self.customer_name_var,
            state="readonly",
            width=30
        )
        customer_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Customer ID hidden field
        customer_id_entry = ttk.Entry(
            customer_header,
            textvariable=self.customer_id_var,
            state="readonly",
            width=5
        )

        if not self.readonly:
            select_btn = ttk.Button(
                customer_header,
                text="Select Customer",
                command=self.select_customer
            )
            select_btn.pack(side=tk.LEFT, padx=5)

        # Customer details
        details_frame = ttk.Frame(customer_frame)
        details_frame.pack(fill=tk.X, padx=5, pady=5)

        # Email
        email_frame = ttk.Frame(details_frame)
        email_frame.pack(fill=tk.X, pady=2)

        ttk.Label(email_frame, text="Email:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        email_entry = ttk.Entry(
            email_frame,
            textvariable=self.customer_email_var,
            state="readonly",
            width=30
        )
        email_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Phone
        phone_frame = ttk.Frame(details_frame)
        phone_frame.pack(fill=tk.X, pady=2)

        ttk.Label(phone_frame, text="Phone:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        phone_entry = ttk.Entry(
            phone_frame,
            textvariable=self.customer_phone_var,
            state="readonly",
            width=20
        )
        phone_entry.pack(side=tk.LEFT, padx=5)

        # Create shipping information section
        shipping_frame = ttk.LabelFrame(customer_tab, text="Shipping Information")
        shipping_frame.pack(fill=tk.X, padx=10, pady=10, anchor=tk.N)

        # Shipping name
        name_frame = ttk.Frame(shipping_frame)
        name_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(name_frame, text="Name:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        name_entry = ttk.Entry(
            name_frame,
            textvariable=self.ship_name_var,
            state="readonly" if self.readonly else "normal",
            width=40
        )
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Street 1
        street1_frame = ttk.Frame(shipping_frame)
        street1_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(street1_frame, text="Street 1:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        street1_entry = ttk.Entry(
            street1_frame,
            textvariable=self.ship_street1_var,
            state="readonly" if self.readonly else "normal",
            width=40
        )
        street1_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Street 2
        street2_frame = ttk.Frame(shipping_frame)
        street2_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(street2_frame, text="Street 2:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        street2_entry = ttk.Entry(
            street2_frame,
            textvariable=self.ship_street2_var,
            state="readonly" if self.readonly else "normal",
            width=40
        )
        street2_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # City, State, Postal
        city_frame = ttk.Frame(shipping_frame)
        city_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(city_frame, text="City:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        city_entry = ttk.Entry(
            city_frame,
            textvariable=self.ship_city_var,
            state="readonly" if self.readonly else "normal",
            width=20
        )
        city_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(city_frame, text="State:").pack(side=tk.LEFT, padx=(10, 0))

        state_entry = ttk.Entry(
            city_frame,
            textvariable=self.ship_state_var,
            state="readonly" if self.readonly else "normal",
            width=10
        )
        state_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(city_frame, text="Postal:").pack(side=tk.LEFT, padx=(10, 0))

        postal_entry = ttk.Entry(
            city_frame,
            textvariable=self.ship_postal_code_var,
            state="readonly" if self.readonly else "normal",
            width=10
        )
        postal_entry.pack(side=tk.LEFT, padx=5)

        # Country
        country_frame = ttk.Frame(shipping_frame)
        country_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(country_frame, text="Country:", width=12, anchor=tk.E).pack(side=tk.LEFT)

        country_entry = ttk.Entry(
            country_frame,
            textvariable=self.ship_country_var,
            state="readonly" if self.readonly else "normal",
            width=20
        )
        country_entry.pack(side=tk.LEFT, padx=5)

        # Buttons for copying customer address, etc.
        if not self.readonly:
            button_frame = ttk.Frame(shipping_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=10)

            ttk.Button(
                button_frame,
                text="Use Customer Address",
                command=self.use_customer_address
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Clear",
                command=self.clear_shipping_address
            ).pack(side=tk.LEFT, padx=5)

    def create_payment_tab(self):
        """Create the payment information tab."""
        payment_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(payment_tab, text="Payment")

        # Create payment information section
        payment_frame = ttk.LabelFrame(payment_tab, text="Payment Information")
        payment_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Payment method
        method_frame = ttk.Frame(payment_frame)
        method_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(method_frame, text="Payment Method:", width=15, anchor=tk.E).pack(side=tk.LEFT)

        if self.readonly:
            method_entry = ttk.Entry(
                method_frame,
                textvariable=self.payment_method_var,
                state="readonly",
                width=20
            )
            method_entry.pack(side=tk.LEFT, padx=5)
        else:
            payment_methods = ["Credit Card", "Bank Transfer", "Cash", "Check", "Other"]

            method_combo = ttk.Combobox(
                method_frame,
                textvariable=self.payment_method_var,
                values=payment_methods,
                state="readonly",
                width=20
            )
            method_combo.pack(side=tk.LEFT, padx=5)

        # Payment reference
        reference_frame = ttk.Frame(payment_frame)
        reference_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(reference_frame, text="Reference #:", width=15, anchor=tk.E).pack(side=tk.LEFT)

        reference_entry = ttk.Entry(
            reference_frame,
            textvariable=self.payment_reference_var,
            state="readonly" if self.readonly else "normal",
            width=20
        )
        reference_entry.pack(side=tk.LEFT, padx=5)

        # Payment amount
        amount_frame = ttk.Frame(payment_frame)
        amount_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(amount_frame, text="Amount:", width=15, anchor=tk.E).pack(side=tk.LEFT)

        amount_entry = ttk.Entry(
            amount_frame,
            textvariable=self.payment_amount_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        amount_entry.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            ttk.Button(
                amount_frame,
                text="Use Total",
                command=lambda: self.payment_amount_var.set(self.total_var.get())
            ).pack(side=tk.LEFT, padx=5)

        # Payment date
        date_frame = ttk.Frame(payment_frame)
        date_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(date_frame, text="Date:", width=15, anchor=tk.E).pack(side=tk.LEFT)

        date_entry = ttk.Entry(
            date_frame,
            textvariable=self.payment_date_var,
            state="readonly" if self.readonly else "normal",
            width=15
        )
        date_entry.pack(side=tk.LEFT, padx=5)

        if not self.readonly:
            ttk.Button(
                date_frame,
                text="📅",
                width=3,
                command=lambda: self.show_date_picker(self.payment_date_var)
            ).pack(side=tk.LEFT)

            ttk.Button(
                date_frame,
                text="Today",
                command=lambda: self.payment_date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))
            ).pack(side=tk.LEFT, padx=5)

        # Payment notes
        notes_frame = ttk.Frame(payment_frame)
        notes_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(notes_frame, text="Notes:", width=15, anchor=tk.E).pack(side=tk.LEFT, anchor=tk.N)

        payment_notes_text = tk.Text(
            notes_frame,
            height=4,
            width=40,
            wrap=tk.WORD,
            state=tk.NORMAL if not self.readonly else tk.DISABLED
        )
        payment_notes_text.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # If we have payment notes, insert them
        if self.payment_notes_var.get():
            payment_notes_text.insert("1.0", self.payment_notes_var.get())

        # Store reference to text widget
        self.payment_notes_text = payment_notes_text

        # Add payment history section if not a new sale
        if self.sale_id and not self.create_new:
            # Create history section
            history_frame = ttk.LabelFrame(payment_tab, text="Payment History")
            history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create treeview for payment history
            columns = ("date", "method", "reference", "amount", "user")

            history_tree = ttk.Treeview(
                history_frame,
                columns=columns,
                show="headings",
                selectmode="browse",
                height=6
            )

            # Set column headings
            history_tree.heading("date", text="Date")
            history_tree.heading("method", text="Method")
            history_tree.heading("reference", text="Reference")
            history_tree.heading("amount", text="Amount")
            history_tree.heading("user", text="User")

            # Set column widths
            history_tree.column("date", width=120)
            history_tree.column("method", width=100)
            history_tree.column("reference", width=120)
            history_tree.column("amount", width=100, anchor=tk.E)
            history_tree.column("user", width=120)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=history_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            history_tree.configure(yscrollcommand=scrollbar.set)

            history_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Store reference to the tree
            self.payment_history_tree = history_tree

            # Load payment history data
            self.load_payment_history()

        # Payment actions section
        if not self.readonly:
            actions_frame = ttk.Frame(payment_tab)
            actions_frame.pack(fill=tk.X, padx=10, pady=10)

            ttk.Button(
                actions_frame,
                text="Process Payment",
                style="Accent.TButton",
                command=self.process_payment
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                actions_frame,
                text="Record Payment",
                command=self.record_payment
            ).pack(side=tk.LEFT, padx=5)

    def create_status_history_tab(self):
        """Create the status history tab."""
        history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(history_tab, text="Status History")

        # Create status history treeview
        columns = ("date", "status", "user", "notes")

        self.status_tree = ttk.Treeview(
            history_tab,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Set column headings
        self.status_tree.heading("date", text="Date & Time")
        self.status_tree.heading("status", text="Status")
        self.status_tree.heading("user", text="User")
        self.status_tree.heading("notes", text="Notes")

        # Set column widths
        self.status_tree.column("date", width=150)
        self.status_tree.column("status", width=150)
        self.status_tree.column("user", width=120)
        self.status_tree.column("notes", width=300)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(history_tab, orient=tk.VERTICAL, command=self.status_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(history_tab, orient=tk.HORIZONTAL, command=self.status_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.status_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load status history if we have a sale ID
        if self.sale_id:
            self.load_status_history()

    def create_action_buttons(self):
        """Create action buttons at the bottom of the view."""
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        if self.readonly:
            # View mode buttons
            ttk.Button(
                button_frame,
                text="Edit",
                style="Accent.TButton",
                command=self.on_edit
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Back",
                command=self.on_back
            ).pack(side=tk.RIGHT, padx=5)

            # Additional actions in view mode
            ttk.Button(
                button_frame,
                text="Generate Invoice",
                command=self.on_generate_invoice
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Print Receipt",
                command=self.on_print_receipt
            ).pack(side=tk.LEFT, padx=5)
        else:
            # Edit mode buttons
            ttk.Button(
                button_frame,
                text="Save",
                style="Accent.TButton",
                command=self.on_save
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Cancel",
                command=self.on_cancel
            ).pack(side=tk.RIGHT, padx=5)

    def load_sale(self):
        """Load sale data from service."""
        try:
            # Get sale data with related customer and items
            self.sale_data = self.sales_service.get_sale(
                self.sale_id,
                include_customer=True,
                include_items=True
            )

            # Update title with sale number
            self.title = f"Sale #{self.sale_data.id}"

            # Set form data
            self.sale_number_var.set(str(self.sale_data.id))

            # Format date
            if hasattr(self.sale_data, "created_at") and self.sale_data.created_at:
                self.sale_date_var.set(self.sale_data.created_at.strftime("%Y-%m-%d %H:%M"))

            # Set status
            if hasattr(self.sale_data, "status") and self.sale_data.status:
                self.status_var.set(self.sale_data.status)

            # Set payment status
            if hasattr(self.sale_data, "payment_status") and self.sale_data.payment_status:
                self.payment_status_var.set(self.sale_data.payment_status)

            # Set totals
            if hasattr(self.sale_data, "subtotal") and self.sale_data.subtotal is not None:
                self.subtotal_var.set(f"${self.sale_data.subtotal:.2f}")

            if hasattr(self.sale_data, "tax") and self.sale_data.tax is not None:
                self.tax_var.set(f"${self.sale_data.tax:.2f}")

            if hasattr(self.sale_data, "shipping") and self.sale_data.shipping is not None:
                self.shipping_var.set(f"${self.sale_data.shipping:.2f}")

            if hasattr(self.sale_data, "discount") and self.sale_data.discount is not None:
                self.discount_var.set(f"${self.sale_data.discount:.2f}")

            if hasattr(self.sale_data, "total_amount") and self.sale_data.total_amount is not None:
                self.total_var.set(f"${self.sale_data.total_amount:.2f}")

            # Set notes
            if hasattr(self.sale_data, "notes") and self.sale_data.notes:
                self.notes_var.set(self.sale_data.notes)

            # Set customer data
            if hasattr(self.sale_data, "customer") and self.sale_data.customer:
                self.customer_data = self.sale_data.customer
                self.update_customer_info()

            # Set line items
            if hasattr(self.sale_data, "items") and self.sale_data.items:
                self.line_items = self.sale_data.items
                self.update_line_items_tree()

            # Set shipping information
            if hasattr(self.sale_data, "shipping_address") and self.sale_data.shipping_address:
                self.update_shipping_info(self.sale_data.shipping_address)

            # Set payment information
            if hasattr(self.sale_data, "payment_method") and self.sale_data.payment_method:
                self.payment_method_var.set(self.sale_data.payment_method)

            if hasattr(self.sale_data, "payment_reference") and self.sale_data.payment_reference:
                self.payment_reference_var.set(self.sale_data.payment_reference)

            if hasattr(self.sale_data, "payment_amount") and self.sale_data.payment_amount is not None:
                self.payment_amount_var.set(f"${self.sale_data.payment_amount:.2f}")

            if hasattr(self.sale_data, "payment_date") and self.sale_data.payment_date:
                self.payment_date_var.set(self.sale_data.payment_date.strftime("%Y-%m-%d"))

            if hasattr(self.sale_data, "payment_notes") and self.sale_data.payment_notes:
                self.payment_notes_var.set(self.sale_data.payment_notes)

        except Exception as e:
            self.logger.error(f"Error loading sale data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load sale data: {str(e)}")

            # Go back to previous view
            self.on_back()

    def update_customer_info(self):
        """Update customer information fields from customer data."""
        if not self.customer_data:
            return

        # Set customer name
        if hasattr(self.customer_data, "first_name") and hasattr(self.customer_data, "last_name"):
            self.customer_name_var.set(f"{self.customer_data.first_name} {self.customer_data.last_name}")

        # Set customer ID
        if hasattr(self.customer_data, "id"):
            self.customer_id_var.set(str(self.customer_data.id))

        # Set email
        if hasattr(self.customer_data, "email"):
            self.customer_email_var.set(self.customer_data.email)

        # Set phone
        if hasattr(self.customer_data, "phone"):
            self.customer_phone_var.set(self.customer_data.phone)

    def update_shipping_info(self, shipping_address):
        """
        Update shipping information fields from address data.

        Args:
            shipping_address: Dictionary with shipping address data
        """
        # Set shipping name (use customer name if not provided)
        if shipping_address.get("name"):
            self.ship_name_var.set(shipping_address.get("name"))
        elif self.customer_data:
            self.ship_name_var.set(f"{self.customer_data.first_name} {self.customer_data.last_name}")

        # Set address fields
        if shipping_address.get("street1"):
            self.ship_street1_var.set(shipping_address.get("street1"))

        if shipping_address.get("street2"):
            self.ship_street2_var.set(shipping_address.get("street2"))

        if shipping_address.get("city"):
            self.ship_city_var.set(shipping_address.get("city"))

        if shipping_address.get("state"):
            self.ship_state_var.set(shipping_address.get("state"))

        if shipping_address.get("postal_code"):
            self.ship_postal_code_var.set(shipping_address.get("postal_code"))

        if shipping_address.get("country"):
            self.ship_country_var.set(shipping_address.get("country"))

    def update_line_items_tree(self):
        """Update the line items treeview with current items."""
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        # Add items to treeview
        for item in self.line_items:
            # Format price and total
            price = f"${item.price:.2f}" if hasattr(item, "price") and item.price is not None else "$0.00"

            # Calculate total
            quantity = item.quantity if hasattr(item, "quantity") else 0
            item_price = item.price if hasattr(item, "price") else 0
            total = quantity * item_price
            total_str = f"${total:.2f}"

            # Add to treeview
            self.items_tree.insert(
                "",
                "end",
                values=(
                    getattr(item, "id", ""),
                    getattr(item, "product_name", "Custom Item"),
                    getattr(item, "description", ""),
                    getattr(item, "quantity", 0),
                    price,
                    total_str
                )
            )

    def load_status_history(self):
        """Load status history data if available."""
        try:
            # Get status history
            history = self.sales_service.get_status_history(self.sale_id)

            # Clear existing items
            for item in self.status_tree.get_children():
                self.status_tree.delete(item)

            # Add items to treeview
            for entry in history:
                # Format date
                date_str = ""
                if hasattr(entry, "created_at") and entry.created_at:
                    date_str = entry.created_at.strftime("%Y-%m-%d %H:%M")

                # Insert into tree
                self.status_tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        getattr(entry, "status", ""),
                        getattr(entry, "user", "System"),
                        getattr(entry, "notes", "")
                    )
                )

        except Exception as e:
            self.logger.error(f"Error loading status history: {e}", exc_info=True)

    def load_payment_history(self):
        """Load payment history data if available."""
        try:
            # Get payment history
            history = self.sales_service.get_payment_history(self.sale_id)

            # Clear existing items
            for item in self.payment_history_tree.get_children():
                self.payment_history_tree.delete(item)

            # Add items to treeview
            for entry in history:
                # Format date
                date_str = ""
                if hasattr(entry, "payment_date") and entry.payment_date:
                    date_str = entry.payment_date.strftime("%Y-%m-%d")

                # Format amount
                amount_str = "$0.00"
                if hasattr(entry, "amount") and entry.amount is not None:
                    amount_str = f"${entry.amount:.2f}"

                # Insert into tree
                self.payment_history_tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        getattr(entry, "method", ""),
                        getattr(entry, "reference", ""),
                        amount_str,
                        getattr(entry, "user", "System")
                    )
                )

        except Exception as e:
            self.logger.error(f"Error loading payment history: {e}", exc_info=True)

    def _set_readonly_mode(self):
        """Set all fields to readonly mode."""
        # This method updates the UI state based on readonly flag
        # Most widgets are already configured in their creation
        pass

    def select_customer(self):
        """Open customer selection dialog."""
        self.logger.debug("Opening customer selection dialog")

        # Create customer selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Customer")
        dialog.transient(self)
        dialog.grab_set()

        # Set dialog size and position
        dialog.geometry("600x500")
        dialog.resizable(True, True)

        # Create search section
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        search_btn = ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_customers(search_var.get(), customer_tree)
        )
        search_btn.pack(side=tk.LEFT, padx=5)

        # Create customers treeview
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("id", "name", "email", "phone", "status")
        customer_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Define headings
        customer_tree.heading("id", text="ID")
        customer_tree.heading("name", text="Name")
        customer_tree.heading("email", text="Email")
        customer_tree.heading("phone", text="Phone")
        customer_tree.heading("status", text="Status")

        # Define columns
        customer_tree.column("id", width=50)
        customer_tree.column("name", width=150)
        customer_tree.column("email", width=150)
        customer_tree.column("phone", width=100)
        customer_tree.column("status", width=100)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=customer_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=customer_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        customer_tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        customer_tree.pack(fill=tk.BOTH, expand=True)

        # Create buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="New Customer",
            command=lambda: self.create_new_customer(dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Select",
            style="Accent.TButton",
            command=lambda: self.select_customer_from_tree(customer_tree, dialog)
        ).pack(side=tk.RIGHT, padx=5)

        # Load initial customer data
        self.search_customers("", customer_tree)

        # Set focus to search entry
        search_entry.focus_set()

        # Bind double-click to select
        customer_tree.bind("<Double-1>", lambda e: self.select_customer_from_tree(customer_tree, dialog))

        # Bind Enter key in search entry
        search_entry.bind("<Return>", lambda e: self.search_customers(search_var.get(), customer_tree))

        # Wait for dialog to close
        dialog.wait_window()

    def search_customers(self, search_text, tree):
        """
        Search customers based on search text.

        Args:
            search_text: Text to search for
            tree: Treeview to display results
        """
        try:
            # Clear existing items
            for item in tree.get_children():
                tree.delete(item)

            # Search customers
            customers = self.customer_service.search_customers(
                search_text=search_text,
                limit=100
            )

            # Display results
            for customer in customers:
                tree.insert(
                    "",
                    "end",
                    iid=str(customer.id),
                    values=(
                        customer.id,
                        f"{customer.first_name} {customer.last_name}",
                        customer.email,
                        customer.phone,
                        customer.status
                    )
                )

        except Exception as e:
            self.logger.error(f"Error searching customers: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to search customers: {str(e)}")

    def select_customer_from_tree(self, tree, dialog):
        """
        Select the highlighted customer from the tree.

        Args:
            tree: Treeview with customer data
            dialog: Dialog to close after selection
        """
        # Get selected item
        selected_id = tree.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer.")
            return

        # Get selected item data
        item_data = tree.item(selected_id)
        values = item_data["values"]

        if not values or len(values) < 5:
            messagebox.showwarning("Selection Error", "Invalid customer data.")
            return

        # Set customer variables
        self.customer_id_var.set(str(values[0]))
        self.customer_name_var.set(values[1])
        self.customer_email_var.set(values[2])
        self.customer_phone_var.set(values[3])

        # Load full customer data
        try:
            self.customer_data = self.customer_service.get_customer(int(values[0]))
        except Exception as e:
            self.logger.error(f"Error loading customer details: {e}", exc_info=True)

        # Close dialog
        dialog.destroy()

    def create_new_customer(self, parent_dialog):
        """
        Create a new customer.

        Args:
            parent_dialog: Parent dialog to close after creation
        """
        # Close the customer selection dialog
        parent_dialog.destroy()

        # Navigate to the customer creation view
        self.parent.master.show_view("customer", add_to_history=True, view_data={"create_new": True})

    def use_customer_address(self):
        """Copy customer address to shipping address fields."""
        if not self.customer_data:
            messagebox.showwarning("No Customer", "Please select a customer first.")
            return

        # Get customer's address
        try:
            address = self.customer_service.get_customer_address(int(self.customer_id_var.get()))

            if not address:
                messagebox.showwarning("No Address", "The selected customer does not have an address.")
                return

            # Set shipping address fields
            self.ship_name_var.set(self.customer_name_var.get())
            self.ship_street1_var.set(address.get("street1", ""))
            self.ship_street2_var.set(address.get("street2", ""))
            self.ship_city_var.set(address.get("city", ""))
            self.ship_state_var.set(address.get("state", ""))
            self.ship_postal_code_var.set(address.get("postal_code", ""))
            self.ship_country_var.set(address.get("country", ""))

        except Exception as e:
            self.logger.error(f"Error getting customer address: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to get customer address: {str(e)}")

    def clear_shipping_address(self):
        """Clear all shipping address fields."""
        self.ship_name_var.set("")
        self.ship_street1_var.set("")
        self.ship_street2_var.set("")
        self.ship_city_var.set("")
        self.ship_state_var.set("")
        self.ship_postal_code_var.set("")
        self.ship_country_var.set("")

    def on_item_select(self, event):
        """
        Handle item selection in the line items treeview.

        Args:
            event: TreeviewSelect event
        """
        # Enable/disable item action buttons
        if self.items_tree.selection() and not self.readonly:
            if hasattr(self, 'edit_item_btn'):
                self.edit_item_btn.config(state=tk.NORMAL)

            if hasattr(self, 'remove_item_btn'):
                self.remove_item_btn.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_item_btn'):
                self.edit_item_btn.config(state=tk.DISABLED)

            if hasattr(self, 'remove_item_btn'):
                self.remove_item_btn.config(state=tk.DISABLED)

    def on_item_double_click(self, event):
        """
        Handle double-click on line item.

        Args:
            event: Double-click event
        """
        if not self.readonly:
            self.on_edit_item()

    def on_add_item(self):
        """Handle add item button click."""
        from gui.views.sales.sales_item_dialog import SalesItemDialog

        dialog = SalesItemDialog(self, create_new=True)
        result = dialog.show()

        if result:
            # Add new item to line items list
            self.line_items.append(result)

            # Update the treeview
            self.update_line_items_tree()

            # Recalculate totals
            self.recalculate_totals()

    def on_edit_item(self):
        """Handle edit item button click."""
        from gui.views.sales.sales_item_dialog import SalesItemDialog

        # Get selected item
        selection = self.items_tree.selection()
        if not selection:
            return

        # Find selected item in line items list
        selected_index = self.items_tree.index(selection[0])
        if selected_index < 0 or selected_index >= len(self.line_items):
            return

        item = self.line_items[selected_index]

        # Open edit dialog
        dialog = SalesItemDialog(self, item=item)
        result = dialog.show()

        if result:
            # Update the item in the list
            self.line_items[selected_index] = result

            # Update the treeview
            self.update_line_items_tree()

            # Recalculate totals
            self.recalculate_totals()

    def on_remove_item(self):
        """Handle remove item button click."""
        # Get selected item
        selection = self.items_tree.selection()
        if not selection:
            return

        # Confirm removal
        if not messagebox.askyesno("Confirm Removal", "Are you sure you want to remove this item?"):
            return

        # Find selected item in line items list
        selected_index = self.items_tree.index(selection[0])
        if selected_index < 0 or selected_index >= len(self.line_items):
            return

        # Remove the item
        del self.line_items[selected_index]

        # Update the treeview
        self.update_line_items_tree()

        # Recalculate totals
        self.recalculate_totals()

    def recalculate_totals(self):
        """Recalculate sales totals based on line items and adjustments."""
        # Calculate subtotal from line items
        subtotal = 0.0
        for item in self.line_items:
            quantity = getattr(item, "quantity", 0)
            price = getattr(item, "price", 0.0)
            subtotal += quantity * price

        # Parse other values
        tax = 0.0
        if self.tax_var.get():
            try:
                tax_str = self.tax_var.get().replace('$', '')
                tax = float(tax_str)
            except ValueError:
                pass

        shipping = 0.0
        if self.shipping_var.get():
            try:
                shipping_str = self.shipping_var.get().replace('$', '')
                shipping = float(shipping_str)
            except ValueError:
                pass

        discount = 0.0
        if self.discount_var.get():
            try:
                discount_str = self.discount_var.get().replace('$', '')
                discount = float(discount_str)
            except ValueError:
                pass

        # Calculate total
        total = subtotal + tax + shipping - discount

        # Update display values
        self.subtotal_var.set(f"${subtotal:.2f}")
        self.tax_var.set(f"${tax:.2f}")
        self.shipping_var.set(f"${shipping:.2f}")
        self.discount_var.set(f"${discount:.2f}")
        self.total_var.set(f"${total:.2f}")

    def process_payment(self):
        """Handle payment processing."""
        # This would typically open a payment processing dialog
        # For now, we'll just show a message and record the payment
        messagebox.showinfo(
            "Payment Processing",
            "Payment processing integration will be implemented in a future phase."
        )

        # Proceed to record the payment
        self.record_payment()

    def record_payment(self):
        """Record a payment for the sale."""
        # Validate payment inputs
        if not self.payment_method_var.get():
            messagebox.showwarning("Missing Data", "Please select a payment method.")
            return

        # Parse payment amount
        payment_amount = 0.0
        try:
            amount_str = self.payment_amount_var.get().replace('$', '')
            payment_amount = float(amount_str)
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Please enter a valid payment amount.")
            return

        if payment_amount <= 0:
            messagebox.showwarning("Invalid Amount", "Payment amount must be greater than zero.")
            return

        # Parse payment date
        payment_date = None
        if self.payment_date_var.get():
            try:
                payment_date = datetime.datetime.strptime(self.payment_date_var.get(), "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid Date", "Please enter a valid payment date (YYYY-MM-DD).")
                return
        else:
            # Use current date if not provided
            payment_date = datetime.datetime.now()

        # Get payment notes
        payment_notes = ""
        if hasattr(self, 'payment_notes_text'):
            payment_notes = self.payment_notes_text.get("1.0", tk.END).strip()

        # Create payment data
        payment_data = {
            "method": self.payment_method_var.get(),
            "reference": self.payment_reference_var.get(),
            "amount": payment_amount,
            "date": payment_date,
            "notes": payment_notes
        }

        try:
            # Record the payment
            result = self.sales_service.record_payment(self.sale_id, payment_data)

            # Update payment status if needed
            if result.get("status_updated"):
                self.payment_status_var.set(result.get("new_status"))

            # Refresh payment history if available
            if hasattr(self, 'payment_history_tree'):
                self.load_payment_history()

            # Show success message
            messagebox.showinfo("Payment Recorded", "Payment has been recorded successfully.")

            # Clear payment form for next entry
            self.payment_reference_var.set("")
            self.payment_amount_var.set("$0.00")
            self.payment_date_var.set("")
            self.payment_notes_text.delete("1.0", tk.END)

        except Exception as e:
            self.logger.error(f"Error recording payment: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to record payment: {str(e)}")

    def collect_form_data(self):
        """
        Collect data from form fields.

        Returns:
            Dictionary of form data
        """
        # Get notes from text widget
        notes = ""
        if hasattr(self, 'notes_text'):
            notes = self.notes_text.get("1.0", tk.END).strip()

        # Get payment notes from text widget
        payment_notes = ""
        if hasattr(self, 'payment_notes_text'):
            payment_notes = self.payment_notes_text.get("1.0", tk.END).strip()

        # Parse date
        sale_date = None
        try:
            sale_date = datetime.datetime.strptime(self.sale_date_var.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            self.logger.warning(f"Invalid date format: {self.sale_date_var.get()}")

        # Parse payment date
        payment_date = None
        if self.payment_date_var.get():
            try:
                payment_date = datetime.datetime.strptime(self.payment_date_var.get(), "%Y-%m-%d")
            except ValueError:
                self.logger.warning(f"Invalid payment date format: {self.payment_date_var.get()}")

        # Parse totals
        subtotal = 0.0
        tax = 0.0
        shipping = 0.0
        discount = 0.0
        total = 0.0

        try:
            subtotal = float(self.subtotal_var.get().replace('$', ''))
        except ValueError:
            pass

        try:
            tax = float(self.tax_var.get().replace('$', ''))
        except ValueError:
            pass

        try:
            shipping = float(self.shipping_var.get().replace('$', ''))
        except ValueError:
            pass

        try:
            discount = float(self.discount_var.get().replace('$', ''))
        except ValueError:
            pass

        try:
            total = float(self.total_var.get().replace('$', ''))
        except ValueError:
            pass

        # Parse payment amount
        payment_amount = 0.0
        try:
            payment_amount = float(self.payment_amount_var.get().replace('$', ''))
        except ValueError:
            pass

        # Create shipping address dict
        shipping_address = {
            "name": self.ship_name_var.get(),
            "street1": self.ship_street1_var.get(),
            "street2": self.ship_street2_var.get(),
            "city": self.ship_city_var.get(),
            "state": self.ship_state_var.get(),
            "postal_code": self.ship_postal_code_var.get(),
            "country": self.ship_country_var.get()
        }

        # Create data dictionary
        data = {
            "customer_id": int(self.customer_id_var.get()) if self.customer_id_var.get() else None,
            "created_at": sale_date,
            "status": self.status_var.get(),
            "payment_status": self.payment_status_var.get(),
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "discount": discount,
            "total_amount": total,
            "notes": notes,
            "shipping_address": shipping_address,
            "payment_method": self.payment_method_var.get(),
            "payment_reference": self.payment_reference_var.get(),
            "payment_amount": payment_amount,
            "payment_date": payment_date,
            "payment_notes": payment_notes,
            "items": self.line_items
        }

        return data

    def validate_form(self):
        """
        Validate form data.

        Returns:
            Tuple of (valid, error_message)
        """
        # Check customer
        if not self.customer_id_var.get():
            return False, "Please select a customer."

        # Check line items
        if not self.line_items:
            return False, "Please add at least one item to the sale."

        # Check date
        try:
            datetime.datetime.strptime(self.sale_date_var.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "Please enter a valid date (YYYY-MM-DD HH:MM)."

        # Check totals
        try:
            float(self.subtotal_var.get().replace('$', ''))
        except ValueError:
            return False, "Please enter a valid subtotal amount."

        try:
            float(self.total_var.get().replace('$', ''))
        except ValueError:
            return False, "Please enter a valid total amount."

        # All validations passed
        return True, ""

    def on_save(self):
        """Handle save button click."""
        # Validate form
        valid, message = self.validate_form()
        if not valid:
            messagebox.showwarning("Validation Error", message)
            return

        # Collect form data
        data = self.collect_form_data()

        try:
            # Save or update the sale
            if self.sale_id:
                # Update existing sale
                result = self.sales_service.update_sale(self.sale_id, data)
                messagebox.showinfo("Success", "Sale has been updated successfully.")
            else:
                # Create new sale
                result = self.sales_service.create_sale(data)
                messagebox.showinfo("Success", "Sale has been created successfully.")

                # Update sale ID
                self.sale_id = result.id

            # Publish event for sale update
            publish("sale_updated", {"sale_id": self.sale_id})

            # Go back to sales list
            self.on_back()

        except Exception as e:
            self.logger.error(f"Error saving sale: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save sale: {str(e)}")

    def on_cancel(self):
        """Handle cancel button click."""
        # Confirm if there are unsaved changes
        if messagebox.askyesno("Confirm Cancel", "Discard changes and return to the sales list?"):
            self.on_back()

    def on_back(self):
        """Handle back button click."""
        # Navigate back to the sales list view
        if self.parent and hasattr(self.parent, 'master'):
            self.parent.master.show_view("sales", add_to_history=False)

    def on_edit(self):
        """Handle edit button click in readonly mode."""
        # Navigate to edit mode
        if self.parent and hasattr(self.parent, 'master'):
            self.parent.master.show_view(
                "sales_details",
                add_to_history=True,
                view_data={
                    "sale_id": self.sale_id,
                    "readonly": False
                }
            )

    def on_generate_invoice(self):
        """Handle generate invoice button click."""
        try:
            # This would typically open the invoice generator
            # For now, just call the service method
            result = self.sales_service.generate_invoice(self.sale_id)

            if result.get("success"):
                # Show success message with path to generated invoice
                messagebox.showinfo(
                    "Invoice Generated",
                    f"Invoice has been generated and saved to:\n{result.get('path')}"
                )
            else:
                messagebox.showwarning("Generation Failed", result.get("message", "Failed to generate invoice."))

        except Exception as e:
            self.logger.error(f"Error generating invoice: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to generate invoice: {str(e)}")

    def on_print_receipt(self):
        """Handle print receipt button click."""
        try:
            # This would typically open the receipt printer dialog
            # For now, just call the service method
            result = self.sales_service.print_receipt(self.sale_id)

            if result.get("success"):
                # Show success message
                messagebox.showinfo("Receipt Printed", "Receipt has been sent to the printer.")
            else:
                messagebox.showwarning("Printing Failed", result.get("message", "Failed to print receipt."))

        except Exception as e:
            self.logger.error(f"Error printing receipt: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to print receipt: {str(e)}")

    def show_date_picker(self, date_var):
        """
        Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create date picker dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Date")
        dialog.transient(self)
        dialog.grab_set()

        # Set dialog size and position
        dialog.geometry("300x350")
        dialog.resizable(False, False)

        # Current date
        now = datetime.datetime.now()

        # Set current month and year
        self.calendar_year = tk.IntVar(value=now.year)
        self.calendar_month = tk.IntVar(value=now.month)

        # Month and year selection
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            header_frame,
            text="<",
            width=2,
            command=lambda: self.prev_month(month_year_label, calendar_frame)
        ).pack(side=tk.LEFT)

        month_year_label = ttk.Label(
            header_frame,
            text=f"{now.strftime('%B')} {now.year}",
            style="Heading.TLabel"
        )
        month_year_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        ttk.Button(
            header_frame,
            text=">",
            width=2,
            command=lambda: self.next_month(month_year_label, calendar_frame)
        ).pack(side=tk.RIGHT)

        # Create calendar frame
        calendar_frame = ttk.Frame(dialog)
        calendar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(
                calendar_frame,
                text=day,
                anchor=tk.CENTER,
                style="Bold.TLabel"
            ).grid(row=0, column=i, sticky=tk.NSEW)

        # Initialize calendar
        self.update_calendar(
            calendar_frame,
            month_year_label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            date_var,
            dialog
        )

        # Today button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Today",
            command=lambda: [
                date_var.set(now.strftime("%Y-%m-%d")),
                dialog.destroy()
            ]
        ).pack(side=tk.LEFT)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Clear",
            command=lambda: [
                date_var.set(""),
                dialog.destroy()
            ]
        ).pack(side=tk.RIGHT, padx=5)

    def update_calendar(self, frame, label, year, month, date_var, dialog):
        """
        Update the calendar display based on selected month and year.

        Args:
            frame: Calendar frame
            label: Month/year label
            year: Year to display
            month: Month to display
            date_var: Variable to update with selected date
            dialog: Dialog to close on selection
        """
        # Update month/year label
        month_name = datetime.date(year, month, 1).strftime("%B")
        label.config(text=f"{month_name} {year}")

        # Clear previous calendar
        for widget in frame.winfo_children():
            if widget.grid_info().get("row", 0) > 0:  # Keep headers
                widget.destroy()

        # Get first day of month and number of days
        first_day = datetime.date(year, month, 1)
        last_day = (datetime.date(year, month + 1, 1) if month < 12 else datetime.date(year + 1, 1,
                                                                                       1)) - datetime.timedelta(days=1)

        # Calculate where to start (Monday = 0)
        start_weekday = (first_day.weekday() + 0) % 7

        # Create calendar buttons
        day = 1
        for row in range(1, 7):  # 6 weeks max
            for col in range(7):  # 7 days per week
                if (row == 1 and col < start_weekday) or day > last_day.day:
                    # Empty cell
                    ttk.Label(
                        frame,
                        text="",
                        width=4,
                        anchor=tk.CENTER
                    ).grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
                else:
                    # Date button
                    day_btn = ttk.Button(
                        frame,
                        text=str(day),
                        width=4,
                        command=lambda d=day: [
                            date_var.set(f"{year:04d}-{month:02d}-{d:02d}"),
                            dialog.destroy()
                        ]
                    )
                    day_btn.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
                    day += 1

    def prev_month(self, label, frame):
        """
        Go to previous month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month and year
        if self.calendar_month.get() == 1:
            self.calendar_month.set(12)
            self.calendar_year.set(self.calendar_year.get() - 1)
        else:
            self.calendar_month.set(self.calendar_month.get() - 1)

        # Update calendar
        self.update_calendar(
            frame,
            label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            getattr(self, "date_var", tk.StringVar()),
            frame.winfo_toplevel()
        )

    def next_month(self, label, frame):
        """
        Go to next month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month and year
        if self.calendar_month.get() == 12:
            self.calendar_month.set(1)
            self.calendar_year.set(self.calendar_year.get() + 1)
        else:
            self.calendar_month.set(self.calendar_month.get() + 1)

        # Update calendar
        self.update_calendar(
            frame,
            label,
            self.calendar_year.get(),
            self.calendar_month.get(),
            getattr(self, "date_var", tk.StringVar()),
            frame.winfo_toplevel()
        )

    def refresh(self):
        """Refresh the view with current data."""
        if self.sale_id:
            self.load_sale()

            # Refresh status history
            self.load_status_history()

            # Refresh payment history if available
            if hasattr(self, 'payment_history_tree'):
                self.load_payment_history()