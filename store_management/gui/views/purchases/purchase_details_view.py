# views/purchases/purchase_details_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import PurchaseStatus

from gui.base.base_view import BaseView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class PurchaseDetailsView(BaseView):
    """View for creating, editing, and viewing purchase orders."""

    def __init__(self, parent, **kwargs):
        """Initialize the purchase details view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                purchase_id: ID of the purchase to view/edit (None for new purchases)
                create_new: Whether to create a new purchase
                readonly: Whether the view should be read-only
                supplier_id: ID of the supplier (for new purchases)
                supplier_name: Name of the supplier (for new purchases)
        """
        super().__init__(parent)

        # Extract kwargs
        self.purchase_id = kwargs.get('purchase_id')
        self.create_new = kwargs.get('create_new', False)
        self.readonly = kwargs.get('readonly', False)
        self.supplier_id = kwargs.get('supplier_id')
        self.supplier_name = kwargs.get('supplier_name')

        # Set title based on mode
        if self.create_new:
            self.title = "Create Purchase Order"
            self.subtitle = "Create a new purchase order"
        elif self.readonly:
            self.title = "Purchase Order Details"
            self.subtitle = f"Viewing purchase order #{self.purchase_id}"
        else:
            self.title = "Edit Purchase Order"
            self.subtitle = f"Editing purchase order #{self.purchase_id}"

        # Initialize form variables
        self._initialize_form_variables()

        # Subscribe to events
        subscribe("supplier_selected", self.on_supplier_selected)
        subscribe("item_selected", self.on_item_selected)

        # Build the view
        self.build()

        # Load purchase data if editing
        if self.purchase_id:
            self.load_purchase()

    def _initialize_form_variables(self):
        """Initialize form variables for data binding."""
        # Basic info
        self.supplier_id_var = tk.StringVar(value=self.supplier_id if self.supplier_id else "")
        self.supplier_name_var = tk.StringVar(value=self.supplier_name if self.supplier_name else "")
        self.status_var = tk.StringVar(value=PurchaseStatus.DRAFT.name)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.expected_date_var = tk.StringVar()

        # Set expected date to 14 days from now
        expected_date = datetime.now() + timedelta(days=14)
        self.expected_date_var.set(expected_date.strftime("%Y-%m-%d"))

        # Notes
        self.notes_var = tk.StringVar()

        # Shipping info
        self.shipping_method_var = tk.StringVar()
        self.tracking_number_var = tk.StringVar()

        # Additional options
        self.auto_receive_var = tk.BooleanVar(value=False)
        self.update_inventory_var = tk.BooleanVar(value=True)
        self.send_to_supplier_var = tk.BooleanVar(value=False)

        # Item list
        self.item_list = []

        # Total values
        self.subtotal_var = tk.StringVar(value="$0.00")
        self.tax_var = tk.StringVar(value="$0.00")
        self.shipping_var = tk.StringVar(value="$0.00")
        self.total_var = tk.StringVar(value="$0.00")

        # Tax rate (default 0%)
        self.tax_rate_var = tk.StringVar(value="0.0")

        # Shipping cost
        self.shipping_cost_var = tk.StringVar(value="0.00")

    def build(self):
        """Build the purchase details view."""
        # Create header
        self.create_header()

        # Create main content frame
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Create notebook for tabs
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_order_tab(notebook)
        self.create_items_tab(notebook)
        self.create_history_tab(notebook)

        # Create action buttons at the bottom
        self.create_action_buttons(content_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        if not self.readonly:
            # Add save button
            self.save_button = ttk.Button(
                self.header,
                text="Save",
                command=self.on_save,
                style="Accent.TButton"
            )
            self.save_button.pack(side=tk.RIGHT, padx=(0, 10))

        # Add print button
        self.print_button = ttk.Button(
            self.header,
            text="Print PO",
            command=self.on_print
        )
        self.print_button.pack(side=tk.RIGHT, padx=(0, 10))

        # Add back button
        self.back_button = ttk.Button(
            self.header,
            text="Back to Purchases",
            command=self.on_back
        )
        self.back_button.pack(side=tk.LEFT, padx=(0, 10))

    def create_order_tab(self, notebook):
        """Create the order information tab.

        Args:
            notebook: The notebook widget for the tab
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Order Information")

        # Create scrollable frame for content
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create form sections
        self.create_basic_info_section(scrollable_frame)
        self.create_supplier_section(scrollable_frame)
        self.create_shipping_section(scrollable_frame)
        self.create_notes_section(scrollable_frame)
        self.create_options_section(scrollable_frame)

    def create_basic_info_section(self, parent):
        """Create basic information section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Basic Information")
        section.pack(fill=tk.X, padx=10, pady=10)

        # Create form grid
        form = ttk.Frame(section)
        form.pack(fill=tk.X, padx=10, pady=10)

        # Configure columns
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Status
        row = 0
        ttk.Label(form, text="Status:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        status_frame = ttk.Frame(form)
        status_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        if self.readonly:
            # Show status badge if readonly
            self.status_badge = StatusBadge(status_frame, text="Loading...", status_value="DRAFT")
            self.status_badge.pack(side=tk.LEFT)
        else:
            # Show status dropdown if editable
            statuses = [status.name for status in PurchaseStatus]
            self.status_combo = ttk.Combobox(
                status_frame,
                textvariable=self.status_var,
                values=statuses,
                state="readonly" if not self.readonly else "disabled",
                width=20
            )
            self.status_combo.pack(side=tk.LEFT)

        # PO Date
        ttk.Label(form, text="PO Date:").grid(row=row, column=2, padx=5, pady=5, sticky=tk.W)

        date_frame = ttk.Frame(form)
        date_frame.grid(row=row, column=3, padx=5, pady=5, sticky=tk.W)

        self.date_entry = ttk.Entry(
            date_frame,
            textvariable=self.date_var,
            width=15,
            state="normal" if not self.readonly else "readonly"
        )
        self.date_entry.pack(side=tk.LEFT)

        if not self.readonly:
            self.date_btn = ttk.Button(
                date_frame,
                text="...",
                width=3,
                command=lambda: self.show_date_picker(self.date_var)
            )
            self.date_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Expected Delivery
        row += 1
        ttk.Label(form, text="Expected Delivery:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        exp_date_frame = ttk.Frame(form)
        exp_date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        self.exp_date_entry = ttk.Entry(
            exp_date_frame,
            textvariable=self.expected_date_var,
            width=15,
            state="normal" if not self.readonly else "readonly"
        )
        self.exp_date_entry.pack(side=tk.LEFT)

        if not self.readonly:
            self.exp_date_btn = ttk.Button(
                exp_date_frame,
                text="...",
                width=3,
                command=lambda: self.show_date_picker(self.expected_date_var)
            )
            self.exp_date_btn.pack(side=tk.LEFT, padx=(5, 0))

    def create_supplier_section(self, parent):
        """Create supplier information section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Supplier Information")
        section.pack(fill=tk.X, padx=10, pady=10)

        # Create form grid
        form = ttk.Frame(section)
        form.pack(fill=tk.X, padx=10, pady=10)

        # Configure columns
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Supplier
        row = 0
        ttk.Label(form, text="Supplier:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        supplier_frame = ttk.Frame(form)
        supplier_frame.grid(row=row, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W + tk.E)

        self.supplier_entry = ttk.Entry(
            supplier_frame,
            textvariable=self.supplier_name_var,
            width=40,
            state="readonly"
        )
        self.supplier_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if not self.readonly:
            self.supplier_btn = ttk.Button(
                supplier_frame,
                text="Select Supplier",
                command=self.on_select_supplier
            )
            self.supplier_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Supplier details (populated when supplier is selected)
        row += 1
        self.supplier_details_frame = ttk.Frame(form)
        self.supplier_details_frame.grid(row=row, column=0, columnspan=4, padx=5, pady=5, sticky=tk.W + tk.E)

        # If supplier is already selected, load details
        if self.supplier_id:
            self.load_supplier_details()

    def create_shipping_section(self, parent):
        """Create shipping information section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Shipping Information")
        section.pack(fill=tk.X, padx=10, pady=10)

        # Create form grid
        form = ttk.Frame(section)
        form.pack(fill=tk.X, padx=10, pady=10)

        # Configure columns
        form.columnconfigure(1, weight=1)

        # Shipping method
        row = 0
        ttk.Label(form, text="Shipping Method:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        methods = ["", "Standard", "Express", "Overnight", "Ground", "Pickup", "Freight", "Other"]
        self.shipping_method_combo = ttk.Combobox(
            form,
            textvariable=self.shipping_method_var,
            values=methods,
            state="normal" if not self.readonly else "disabled",
            width=20
        )
        self.shipping_method_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Tracking number
        row += 1
        ttk.Label(form, text="Tracking Number:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        self.tracking_entry = ttk.Entry(
            form,
            textvariable=self.tracking_number_var,
            width=30,
            state="normal" if not self.readonly else "readonly"
        )
        self.tracking_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

    def create_notes_section(self, parent):
        """Create notes section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Notes")
        section.pack(fill=tk.X, padx=10, pady=10)

        # Create notes entry
        notes_frame = ttk.Frame(section)
        notes_frame.pack(fill=tk.X, padx=10, pady=10)

        self.notes_text = tk.Text(
            notes_frame,
            height=4,
            width=50,
            wrap=tk.WORD,
            state="normal" if not self.readonly else "disabled"
        )
        self.notes_text.pack(fill=tk.X)

        # Set notes text if variable has value
        if self.notes_var.get():
            self.notes_text.insert("1.0", self.notes_var.get())

    def create_options_section(self, parent):
        """Create additional options section.

        Args:
            parent: The parent widget
        """
        # Create section frame
        section = ttk.LabelFrame(parent, text="Additional Options")
        section.pack(fill=tk.X, padx=10, pady=10)

        # Create options frame
        options_frame = ttk.Frame(section)
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        # Configure columns
        options_frame.columnconfigure(0, weight=1)

        # Auto-receive option
        self.auto_receive_check = ttk.Checkbutton(
            options_frame,
            text="Auto-receive items upon save",
            variable=self.auto_receive_var,
            state="normal" if not self.readonly else "disabled"
        )
        self.auto_receive_check.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)

        # Update inventory option
        self.update_inventory_check = ttk.Checkbutton(
            options_frame,
            text="Update inventory when received",
            variable=self.update_inventory_var,
            state="normal" if not self.readonly else "disabled"
        )
        self.update_inventory_check.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)

        # Send to supplier option
        self.send_supplier_check = ttk.Checkbutton(
            options_frame,
            text="Send purchase order to supplier upon save",
            variable=self.send_to_supplier_var,
            state="normal" if not self.readonly else "disabled"
        )
        self.send_supplier_check.grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)

    def create_items_tab(self, notebook):
        """Create the line items tab.

        Args:
            notebook: The notebook widget for the tab
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Line Items")

        # Create top frame for items
        items_frame = ttk.Frame(tab)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create items treeview
        self.create_items_treeview(items_frame)

        # Create item buttons
        self.create_item_buttons(items_frame)

        # Create totals section
        self.create_totals_section(tab)

    def create_items_treeview(self, parent):
        """Create the treeview for line items.

        Args:
            parent: The parent widget
        """
        # Create treeview frame
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview
        self.items_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "name", "quantity", "unit_price", "total"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.items_tree.heading("id", text="Item ID")
        self.items_tree.heading("name", text="Item Description")
        self.items_tree.heading("quantity", text="Quantity")
        self.items_tree.heading("unit_price", text="Unit Price")
        self.items_tree.heading("total", text="Total")

        # Configure column widths
        self.items_tree.column("id", width=80, stretch=False)
        self.items_tree.column("name", width=300, stretch=True)
        self.items_tree.column("quantity", width=80, stretch=False)
        self.items_tree.column("unit_price", width=100, stretch=False)
        self.items_tree.column("total", width=100, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscroll=scrollbar.set)

        # Pack widgets
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.items_tree.bind("<Double-1>", self.on_item_double_click)

    def create_item_buttons(self, parent):
        """Create buttons for managing line items.

        Args:
            parent: The parent widget
        """
        # Create buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add item button
        if not self.readonly:
            self.add_item_btn = ttk.Button(
                buttons_frame,
                text="Add Item",
                command=self.on_add_item
            )
            self.add_item_btn.pack(side=tk.LEFT, padx=(0, 5))

            # Edit item button
            self.edit_item_btn = ttk.Button(
                buttons_frame,
                text="Edit Item",
                command=self.on_edit_item,
                state=tk.DISABLED
            )
            self.edit_item_btn.pack(side=tk.LEFT, padx=5)

            # Remove item button
            self.remove_item_btn = ttk.Button(
                buttons_frame,
                text="Remove Item",
                command=self.on_remove_item,
                state=tk.DISABLED
            )
            self.remove_item_btn.pack(side=tk.LEFT, padx=5)

    def create_totals_section(self, parent):
        """Create the totals section.

        Args:
            parent: The parent widget
        """
        # Create totals frame
        totals_frame = ttk.Frame(parent)
        totals_frame.pack(fill=tk.X, padx=15, pady=15)

        # Configure columns
        totals_frame.columnconfigure(0, weight=1)
        totals_frame.columnconfigure(2, weight=0)

        # Create left column for tax and shipping inputs
        if not self.readonly:
            left_frame = ttk.Frame(totals_frame)
            left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

            # Tax rate
            tax_frame = ttk.Frame(left_frame)
            tax_frame.pack(fill=tk.X, pady=(0, 5))

            ttk.Label(tax_frame, text="Tax Rate (%):").pack(side=tk.LEFT, padx=(0, 5))

            tax_entry = ttk.Entry(
                tax_frame,
                textvariable=self.tax_rate_var,
                width=8
            )
            tax_entry.pack(side=tk.LEFT)

            # Bind update event
            tax_entry.bind("<KeyRelease>", lambda e: self.update_totals())

            # Shipping cost
            shipping_frame = ttk.Frame(left_frame)
            shipping_frame.pack(fill=tk.X)

            ttk.Label(shipping_frame, text="Shipping Cost:").pack(side=tk.LEFT, padx=(0, 5))

            shipping_entry = ttk.Entry(
                shipping_frame,
                textvariable=self.shipping_cost_var,
                width=10
            )
            shipping_entry.pack(side=tk.LEFT)

            # Bind update event
            shipping_entry.bind("<KeyRelease>", lambda e: self.update_totals())

        # Create right column for totals
        right_frame = ttk.Frame(totals_frame)
        right_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)

        # Configure grid
        for i in range(2):
            right_frame.columnconfigure(i, weight=1)

        # Subtotal
        ttk.Label(right_frame, text="Subtotal:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Label(
            right_frame,
            textvariable=self.subtotal_var,
            font=("", 10, "")
        ).grid(row=0, column=1, padx=5, pady=2, sticky=tk.E)

        # Tax
        ttk.Label(right_frame, text="Tax:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Label(
            right_frame,
            textvariable=self.tax_var,
            font=("", 10, "")
        ).grid(row=1, column=1, padx=5, pady=2, sticky=tk.E)

        # Shipping
        ttk.Label(right_frame, text="Shipping:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Label(
            right_frame,
            textvariable=self.shipping_var,
            font=("", 10, "")
        ).grid(row=2, column=1, padx=5, pady=2, sticky=tk.E)

        # Separator
        ttk.Separator(right_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, padx=5, pady=5,
                                                              sticky=tk.E + tk.W)

        # Total
        ttk.Label(right_frame, text="Total:").grid(row=4, column=0, padx=5, pady=2, sticky=tk.E)
        ttk.Label(
            right_frame,
            textvariable=self.total_var,
            font=("", 12, "bold")
        ).grid(row=4, column=1, padx=5, pady=2, sticky=tk.E)

    def create_history_tab(self, notebook):
        """Create the history tab for purchase history.

        Args:
            notebook: The notebook widget for the tab
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="History")

        # Create history treeview
        self.create_history_treeview(tab)

    def create_history_treeview(self, parent):
        """Create the treeview for purchase history.

        Args:
            parent: The parent widget
        """
        # Create frame
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview
        self.history_tree = ttk.Treeview(
            frame,
            columns=("date", "user", "action", "details"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.history_tree.heading("date", text="Date/Time")
        self.history_tree.heading("user", text="User")
        self.history_tree.heading("action", text="Action")
        self.history_tree.heading("details", text="Details")

        # Configure column widths
        self.history_tree.column("date", width=150, stretch=False)
        self.history_tree.column("user", width=120, stretch=False)
        self.history_tree.column("action", width=120, stretch=False)
        self.history_tree.column("details", width=400, stretch=True)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)

        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_action_buttons(self, parent):
        """Create action buttons at the bottom.

        Args:
            parent: The parent widget
        """
        # Create buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        if not self.readonly:
            # Save button
            self.save_btn = ttk.Button(
                buttons_frame,
                text="Save",
                command=self.on_save,
                style="Accent.TButton"
            )
            self.save_btn.pack(side=tk.RIGHT, padx=5)

            # Cancel button
            self.cancel_btn = ttk.Button(
                buttons_frame,
                text="Cancel",
                command=self.on_cancel
            )
            self.cancel_btn.pack(side=tk.RIGHT, padx=5)
        else:
            # Edit button
            self.edit_btn = ttk.Button(
                buttons_frame,
                text="Edit",
                command=self.on_edit,
                style="Accent.TButton"
            )
            self.edit_btn.pack(side=tk.RIGHT, padx=5)

            # Receive items button (for ORDERED status)
            self.receive_btn = ttk.Button(
                buttons_frame,
                text="Receive Items",
                command=self.on_receive
            )
            self.receive_btn.pack(side=tk.RIGHT, padx=5)

            # Initially disable - will be enabled if appropriate status
            self.receive_btn.config(state=tk.DISABLED)

    def load_purchase(self):
        """Load purchase data from service."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get purchase data
            purchase = purchase_service.get_purchase(self.purchase_id)

            if not purchase:
                messagebox.showerror("Error", f"Could not find purchase with ID {self.purchase_id}")
                self.on_back()
                return

            # Get supplier data
            supplier_id = purchase.get('supplier_id')
            supplier = purchase.get('supplier', {})
            supplier_name = supplier.get('name', '') if supplier else ''

            # Update supplier variables
            self.supplier_id_var.set(supplier_id)
            self.supplier_name_var.set(supplier_name)

            # Update status
            status = purchase.get('status', '')
            if hasattr(status, 'name'):
                status = status.name

            self.status_var.set(status)

            if hasattr(self, 'status_badge'):
                self.status_badge.set_text(status, status)

            # Update dates
            created_at = purchase.get('created_at', '')
            if isinstance(created_at, datetime):
                self.date_var.set(created_at.strftime("%Y-%m-%d"))

            expected_at = purchase.get('expected_at', '')
            if isinstance(expected_at, datetime):
                self.expected_date_var.set(expected_at.strftime("%Y-%m-%d"))

            # Update shipping info
            self.shipping_method_var.set(purchase.get('shipping_method', ''))
            self.tracking_number_var.set(purchase.get('tracking_number', ''))

            # Update notes
            notes = purchase.get('notes', '')
            if notes:
                self.notes_text.delete("1.0", tk.END)
                self.notes_text.insert("1.0", notes)
                self.notes_var.set(notes)

            # Update options
            self.update_inventory_var.set(purchase.get('update_inventory', True))

            # Update items
            self.item_list = purchase.get('items', [])
            self.update_items_treeview()

            # Update totals
            self.update_totals_from_purchase(purchase)

            # Load supplier details
            self.load_supplier_details()

            # Load history
            self.load_history()

            # Enable/disable receive button based on status
            if hasattr(self, 'receive_btn') and status in ['ORDERED', 'PARTIALLY_RECEIVED']:
                self.receive_btn.config(state=tk.NORMAL)
            elif hasattr(self, 'receive_btn'):
                self.receive_btn.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Error loading purchase data: {e}")
            messagebox.showerror("Error", f"Failed to load purchase data: {e}")

    def load_supplier_details(self):
        """Load supplier details from service."""
        try:
            supplier_id = self.supplier_id_var.get()
            if not supplier_id:
                return

            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Get supplier data
            supplier = supplier_service.get_supplier(supplier_id)

            if not supplier:
                return

            # Clear existing widgets
            for widget in self.supplier_details_frame.winfo_children():
                widget.destroy()

            # Create supplier details
            details_text = f"Contact: {supplier.get('contact_name', 'N/A')}\n"
            details_text += f"Email: {supplier.get('contact_email', 'N/A')}\n"
            details_text += f"Phone: {supplier.get('phone', 'N/A')}"

            ttk.Label(
                self.supplier_details_frame,
                text=details_text,
                style="Secondary.TLabel",
                justify=tk.LEFT
            ).pack(anchor=tk.W)

        except Exception as e:
            logger.error(f"Error loading supplier details: {e}")

    def load_history(self):
        """Load purchase history from service."""
        try:
            # Clear existing items
            self.history_tree.delete(*self.history_tree.get_children())

            # Only continue if we have a purchase ID
            if not self.purchase_id:
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get history
            history = purchase_service.get_purchase_history(self.purchase_id)

            # Insert history items
            for item in history:
                # Format date
                timestamp = item.get('timestamp', '')
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime('%Y-%m-%d %H:%M')

                # Insert into tree
                self.history_tree.insert(
                    '',
                    'end',
                    values=(
                        timestamp,
                        item.get('user', 'System'),
                        item.get('action', ''),
                        item.get('details', '')
                    )
                )

        except Exception as e:
            logger.error(f"Error loading history: {e}")

    def update_items_treeview(self):
        """Update the items treeview with current items."""
        # Clear existing items
        self.items_tree.delete(*self.items_tree.get_children())

        # Add items to treeview
        for item in self.item_list:
            # Calculate item total
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            total = quantity * unit_price

            # Format price values
            unit_price_str = f"${unit_price:.2f}"
            total_str = f"${total:.2f}"

            # Insert into tree
            self.items_tree.insert(
                '',
                'end',
                values=(
                    item.get('item_id', ''),
                    item.get('name', ''),
                    quantity,
                    unit_price_str,
                    total_str
                )
            )

    def update_totals(self):
        """Update the totals based on current items and tax/shipping."""
        try:
            # Calculate subtotal
            subtotal = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in self.item_list)

            # Get tax rate
            try:
                tax_rate = float(self.tax_rate_var.get()) / 100
            except ValueError:
                tax_rate = 0

            # Calculate tax
            tax = subtotal * tax_rate

            # Get shipping cost
            try:
                shipping_cost = float(self.shipping_cost_var.get())
            except ValueError:
                shipping_cost = 0

            # Calculate total
            total = subtotal + tax + shipping_cost

            # Update variables
            self.subtotal_var.set(f"${subtotal:.2f}")
            self.tax_var.set(f"${tax:.2f}")
            self.shipping_var.set(f"${shipping_cost:.2f}")
            self.total_var.set(f"${total:.2f}")

        except Exception as e:
            logger.error(f"Error updating totals: {e}")

    def update_totals_from_purchase(self, purchase):
        """Update totals from purchase data.

        Args:
            purchase: Purchase data dictionary
        """
        # Get values from purchase
        subtotal = purchase.get('subtotal', 0)
        tax = purchase.get('tax', 0)
        shipping = purchase.get('shipping_cost', 0)
        total = purchase.get('total_amount', 0)

        # Update variables
        self.subtotal_var.set(f"${subtotal:.2f}")
        self.tax_var.set(f"${tax:.2f}")
        self.shipping_var.set(f"${shipping:.2f}")
        self.total_var.set(f"${total:.2f}")

        # Update input variables if not readonly
        if not self.readonly:
            tax_rate = purchase.get('tax_rate', 0) * 100
            self.tax_rate_var.set(f"{tax_rate:.1f}")
            self.shipping_cost_var.set(f"{shipping:.2f}")

    def on_select_supplier(self):
        """Handle select supplier button click."""
        # Create supplier selection dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Select Supplier")
        dialog.geometry("600x400")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_suppliers(search_var.get(), supplier_tree)
        ).pack(side=tk.LEFT)

        # Create treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        supplier_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "name", "contact", "status"),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        supplier_tree.heading("id", text="ID")
        supplier_tree.heading("name", text="Name")
        supplier_tree.heading("contact", text="Contact")
        supplier_tree.heading("status", text="Status")

        supplier_tree.column("id", width=50, stretch=False)
        supplier_tree.column("name", width=200, stretch=True)
        supplier_tree.column("contact", width=200, stretch=True)
        supplier_tree.column("status", width=100, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=supplier_tree.yview)
        supplier_tree.configure(yscroll=scrollbar.set)

        supplier_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load suppliers
        self.load_suppliers(supplier_tree)

        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Select",
            command=lambda: self.select_supplier(supplier_tree, dialog),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=(0, 5))

        # Create new supplier button
        ttk.Button(
            button_frame,
            text="New Supplier",
            command=lambda: self.create_new_supplier(dialog)
        ).pack(side=tk.LEFT)

        # Bind double-click
        supplier_tree.bind("<Double-1>", lambda e: self.select_supplier(supplier_tree, dialog))

    def load_suppliers(self, tree):
        """Load suppliers into treeview.

        Args:
            tree: The treeview to populate
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Get suppliers
            suppliers = supplier_service.get_suppliers(limit=100)

            # Insert suppliers
            for supplier in suppliers:
                # Format status
                status = supplier.get('status', '')
                if hasattr(status, 'name'):
                    status = status.name

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        supplier.get('id', ''),
                        supplier.get('name', ''),
                        supplier.get('contact_email', ''),
                        status
                    )
                )

        except Exception as e:
            logger.error(f"Error loading suppliers: {e}")

    def search_suppliers(self, search_text, tree):
        """Search suppliers based on search text.

        Args:
            search_text: Text to search for
            tree: The treeview to populate with results
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Get suppliers
            suppliers = supplier_service.get_suppliers(search_text=search_text, limit=100)

            # Insert suppliers
            for supplier in suppliers:
                # Format status
                status = supplier.get('status', '')
                if hasattr(status, 'name'):
                    status = status.name

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        supplier.get('id', ''),
                        supplier.get('name', ''),
                        supplier.get('contact_email', ''),
                        status
                    )
                )

        except Exception as e:
            logger.error(f"Error searching suppliers: {e}")

    def select_supplier(self, tree, dialog):
        """Select supplier from tree.

        Args:
            tree: The treeview with suppliers
            dialog: The dialog to close
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a supplier.")
            return

        # Get selected supplier
        values = tree.item(selection[0], "values")
        supplier_id = values[0]
        supplier_name = values[1]

        # Update supplier variables
        self.supplier_id_var.set(supplier_id)
        self.supplier_name_var.set(supplier_name)

        # Load supplier details
        self.load_supplier_details()

        # Close dialog
        dialog.destroy()

        # Publish event
        publish("supplier_selected", {"supplier_id": supplier_id, "supplier_name": supplier_name})

    def create_new_supplier(self, parent_dialog):
        """Create a new supplier.

        Args:
            parent_dialog: Parent dialog to close after creation
        """
        try:
            # Get supplier details dialog class
            from gui.views.purchases.supplier_details_dialog import SupplierDetailsDialog

            # Close supplier selection dialog
            parent_dialog.destroy()

            # Show supplier details dialog
            dialog = SupplierDetailsDialog(
                self.winfo_toplevel(),
                create_new=True
            )

            if dialog.show():
                # Reload supplier details
                if dialog.result_data and 'supplier_id' in dialog.result_data:
                    # Update supplier variables
                    self.supplier_id_var.set(dialog.result_data['supplier_id'])
                    self.supplier_name_var.set(dialog.result_data.get('name', ''))

                    # Load supplier details
                    self.load_supplier_details()

        except Exception as e:
            logger.error(f"Error creating new supplier: {e}")
            messagebox.showerror("Error", f"Failed to create new supplier: {e}")

    def on_item_select(self, event=None):
        """Handle line item selection."""
        if not self.readonly:
            # Enable/disable buttons based on selection
            if self.items_tree.selection():
                self.edit_item_btn.config(state=tk.NORMAL)
                self.remove_item_btn.config(state=tk.NORMAL)
            else:
                self.edit_item_btn.config(state=tk.DISABLED)
                self.remove_item_btn.config(state=tk.DISABLED)

    def on_item_double_click(self, event=None):
        """Handle line item double-click."""
        if not self.readonly:
            self.on_edit_item()

    def on_add_item(self):
        """Handle add item button click."""
        # Check if supplier is selected
        if not self.supplier_id_var.get():
            messagebox.showinfo("Select Supplier", "Please select a supplier first.")
            return

        # Create item selection dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Add Item")
        dialog.geometry("600x600")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create materials tab
        self.create_materials_tab(notebook)

        # Create supplies tab
        self.create_supplies_tab(notebook)

        # Create tools tab
        self.create_tools_tab(notebook)

        # Create custom item tab
        self.create_custom_item_tab(notebook)

        # Create buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT)

    def create_materials_tab(self, notebook):
        """Create the materials tab for item selection.

        Args:
            notebook: The notebook widget
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Materials")

        # Create search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_materials(search_var.get(), materials_tree)
        ).pack(side=tk.LEFT)

        # Create treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        materials_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "name", "type", "stock", "price"),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        materials_tree.heading("id", text="ID")
        materials_tree.heading("name", text="Name")
        materials_tree.heading("type", text="Type")
        materials_tree.heading("stock", text="In Stock")
        materials_tree.heading("price", text="Price")

        materials_tree.column("id", width=50, stretch=False)
        materials_tree.column("name", width=200, stretch=True)
        materials_tree.column("type", width=100, stretch=False)
        materials_tree.column("stock", width=80, stretch=False)
        materials_tree.column("price", width=80, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=materials_tree.yview)
        materials_tree.configure(yscroll=scrollbar.set)

        materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load materials
        self.load_materials(materials_tree)

        # Create quantity frame
        quantity_frame = ttk.Frame(tab)
        quantity_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=(0, 5))

        quantity_var = tk.StringVar(value="1")
        quantity_spinbox = ttk.Spinbox(quantity_frame, from_=1, to=1000, textvariable=quantity_var, width=5)
        quantity_spinbox.pack(side=tk.LEFT)

        # Create button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Add to Order",
            command=lambda: self.add_material_to_order(
                materials_tree,
                quantity_var.get(),
                notebook.winfo_parent()
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)

        # Bind double-click
        materials_tree.bind("<Double-1>", lambda e: self.add_material_to_order(
            materials_tree,
            quantity_var.get(),
            notebook.winfo_parent()
        ))

    def create_supplies_tab(self, notebook):
        """Create the supplies tab for item selection.

        Args:
            notebook: The notebook widget
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Supplies")

        # Create search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_supplies(search_var.get(), supplies_tree)
        ).pack(side=tk.LEFT)

        # Create treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        supplies_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "name", "type", "stock", "price"),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        supplies_tree.heading("id", text="ID")
        supplies_tree.heading("name", text="Name")
        supplies_tree.heading("type", text="Type")
        supplies_tree.heading("stock", text="In Stock")
        supplies_tree.heading("price", text="Price")

        supplies_tree.column("id", width=50, stretch=False)
        supplies_tree.column("name", width=200, stretch=True)
        supplies_tree.column("type", width=100, stretch=False)
        supplies_tree.column("stock", width=80, stretch=False)
        supplies_tree.column("price", width=80, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=supplies_tree.yview)
        supplies_tree.configure(yscroll=scrollbar.set)

        supplies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load supplies
        self.load_supplies(supplies_tree)

        # Create quantity frame
        quantity_frame = ttk.Frame(tab)
        quantity_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=(0, 5))

        quantity_var = tk.StringVar(value="1")
        quantity_spinbox = ttk.Spinbox(quantity_frame, from_=1, to=1000, textvariable=quantity_var, width=5)
        quantity_spinbox.pack(side=tk.LEFT)

        # Create button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Add to Order",
            command=lambda: self.add_supplies_to_order(
                supplies_tree,
                quantity_var.get(),
                notebook.winfo_parent()
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)

        # Bind double-click
        supplies_tree.bind("<Double-1>", lambda e: self.add_supplies_to_order(
            supplies_tree,
            quantity_var.get(),
            notebook.winfo_parent()
        ))

    def create_tools_tab(self, notebook):
        """Create the tools tab for item selection.

        Args:
            notebook: The notebook widget
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Tools")

        # Create search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_tools(search_var.get(), tools_tree)
        ).pack(side=tk.LEFT)

        # Create treeview
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tools_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "name", "category", "stock", "price"),
            show="headings",
            selectmode="browse"
        )

        # Configure columns
        tools_tree.heading("id", text="ID")
        tools_tree.heading("name", text="Name")
        tools_tree.heading("category", text="Category")
        tools_tree.heading("stock", text="In Stock")
        tools_tree.heading("price", text="Price")

        tools_tree.column("id", width=50, stretch=False)
        tools_tree.column("name", width=200, stretch=True)
        tools_tree.column("category", width=100, stretch=False)
        tools_tree.column("stock", width=80, stretch=False)
        tools_tree.column("price", width=80, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tools_tree.yview)
        tools_tree.configure(yscroll=scrollbar.set)

        tools_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Load tools
        self.load_tools(tools_tree)

        # Create quantity frame
        quantity_frame = ttk.Frame(tab)
        quantity_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=(0, 5))

        quantity_var = tk.StringVar(value="1")
        quantity_spinbox = ttk.Spinbox(quantity_frame, from_=1, to=1000, textvariable=quantity_var, width=5)
        quantity_spinbox.pack(side=tk.LEFT)

        # Create button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Add to Order",
            command=lambda: self.add_tool_to_order(
                tools_tree,
                quantity_var.get(),
                notebook.winfo_parent()
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)

        # Bind double-click
        tools_tree.bind("<Double-1>", lambda e: self.add_tool_to_order(
            tools_tree,
            quantity_var.get(),
            notebook.winfo_parent()
        ))

    def create_custom_item_tab(self, notebook):
        """Create the custom item tab.

        Args:
            notebook: The notebook widget
        """
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Custom Item")

        # Create form frame
        form_frame = ttk.Frame(tab, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Item description
        row = 0
        ttk.Label(form_frame, text="Description:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        description_var = tk.StringVar()
        description_entry = ttk.Entry(form_frame, textvariable=description_var, width=40)
        description_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Item quantity
        row += 1
        ttk.Label(form_frame, text="Quantity:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        quantity_var = tk.StringVar(value="1")
        quantity_spinbox = ttk.Spinbox(form_frame, from_=1, to=1000, textvariable=quantity_var, width=5)
        quantity_spinbox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Unit price
        row += 1
        ttk.Label(form_frame, text="Unit Price:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        price_var = tk.StringVar(value="0.00")
        price_entry = ttk.Entry(form_frame, textvariable=price_var, width=10)
        price_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Notes
        row += 1
        ttk.Label(form_frame, text="Notes:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

        notes_text = tk.Text(form_frame, height=4, width=40, wrap=tk.WORD)
        notes_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Create button frame
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Add to Order",
            command=lambda: self.add_custom_item_to_order(
                description_var.get(),
                quantity_var.get(),
                price_var.get(),
                notes_text.get("1.0", tk.END).strip(),
                notebook.winfo_parent()
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)

    def load_materials(self, tree):
        """Load materials into treeview.

        Args:
            tree: The treeview to populate
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get material service
            material_service = get_service('IMaterialService')

            # Get materials
            materials = material_service.get_materials(limit=100)

            # Insert materials
            for material in materials:
                # Get inventory data
                inventory = material.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = material.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        material.get('id', ''),
                        material.get('name', ''),
                        material.get('material_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error loading materials: {e}")

    def search_materials(self, search_text, tree):
        """Search materials based on search text.

        Args:
            search_text: Text to search for
            tree: The treeview to populate with results
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get material service
            material_service = get_service('IMaterialService')

            # Get materials
            materials = material_service.get_materials(search_text=search_text, limit=100)

            # Insert materials
            for material in materials:
                # Get inventory data
                inventory = material.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = material.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        material.get('id', ''),
                        material.get('name', ''),
                        material.get('material_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error searching materials: {e}")

    def load_supplies(self, tree):
        """Load supplies into treeview.

        Args:
            tree: The treeview to populate
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get supplies service
            supplies_service = get_service('ISuppliesService')

            # Get supplies
            supplies = supplies_service.get_supplies(limit=100)

            # Insert supplies
            for item in supplies:
                # Get inventory data
                inventory = item.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = item.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        item.get('id', ''),
                        item.get('name', ''),
                        item.get('material_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error loading supplies: {e}")

    def search_supplies(self, search_text, tree):
        """Search supplies based on search text.

        Args:
            search_text: Text to search for
            tree: The treeview to populate with results
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get supplies service
            supplies_service = get_service('ISuppliesService')

            # Get supplies
            supplies = supplies_service.get_supplies(search_text=search_text, limit=100)

            # Insert supplies
            for item in supplies:
                # Get inventory data
                inventory = item.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = item.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        item.get('id', ''),
                        item.get('name', ''),
                        item.get('material_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error searching supplies: {e}")

    def load_tools(self, tree):
        """Load tools into treeview.

        Args:
            tree: The treeview to populate
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get tool service
            tool_service = get_service('IToolService')

            # Get tools
            tools = tool_service.get_tools(limit=100)

            # Insert tools
            for tool in tools:
                # Get inventory data
                inventory = tool.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = tool.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        tool.get('id', ''),
                        tool.get('name', ''),
                        tool.get('tool_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error loading tools: {e}")

    def search_tools(self, search_text, tree):
        """Search tools based on search text.

        Args:
            search_text: Text to search for
            tree: The treeview to populate with results
        """
        try:
            # Clear existing items
            tree.delete(*tree.get_children())

            # Get tool service
            tool_service = get_service('IToolService')

            # Get tools
            tools = tool_service.get_tools(search_text=search_text, limit=100)

            # Insert tools
            for tool in tools:
                # Get inventory data
                inventory = tool.get('inventory', {})
                stock = inventory.get('quantity', 0) if inventory else 0

                # Format price
                price = tool.get('purchase_price', 0)
                price_str = f"${price:.2f}" if price else ""

                # Insert into tree
                tree.insert(
                    '',
                    'end',
                    values=(
                        tool.get('id', ''),
                        tool.get('name', ''),
                        tool.get('tool_type', ''),
                        stock,
                        price_str
                    )
                )

        except Exception as e:
            logger.error(f"Error searching tools: {e}")

    def add_material_to_order(self, tree, quantity_str, parent_window):
        """Add selected material to the order.

        Args:
            tree: The treeview with materials
            quantity_str: Quantity string
            parent_window: Parent window to close
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a material.")
            return

        try:
            # Get selected material
            values = tree.item(selection[0], "values")
            item_id = values[0]
            name = values[1]

            # Parse price
            price_str = values[4]
            price = float(price_str.replace('$', '')) if price_str else 0

            # Parse quantity
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity = 1
            except ValueError:
                quantity = 1

            # Create item dict
            item = {
                'item_id': item_id,
                'item_type': 'material',
                'name': name,
                'quantity': quantity,
                'unit_price': price
            }

            # Add to item list
            self.item_list.append(item)

            # Update treeview
            self.update_items_treeview()

            # Update totals
            self.update_totals()

            # Close parent window
            for widget in self.winfo_toplevel().winfo_children():
                if widget.winfo_id() == int(parent_window):
                    widget.destroy()
                    break

            # Publish event
            publish("item_selected", {"item_id": item_id, "item_type": "material"})

        except Exception as e:
            logger.error(f"Error adding material to order: {e}")
            messagebox.showerror("Error", f"Failed to add material: {e}")

    def add_supplies_to_order(self, tree, quantity_str, parent_window):
        """Add selected supplies to the order.

        Args:
            tree: The treeview with supplies
            quantity_str: Quantity string
            parent_window: Parent window to close
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a supplies item.")
            return

        try:
            # Get selected supplies
            values = tree.item(selection[0], "values")
            item_id = values[0]
            name = values[1]

            # Parse price
            price_str = values[4]
            price = float(price_str.replace('$', '')) if price_str else 0

            # Parse quantity
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity = 1
            except ValueError:
                quantity = 1

            # Create item dict
            item = {
                'item_id': item_id,
                'item_type': 'supplies',
                'name': name,
                'quantity': quantity,
                'unit_price': price
            }

            # Add to item list
            self.item_list.append(item)

            # Update treeview
            self.update_items_treeview()

            # Update totals
            self.update_totals()

            # Close parent window
            for widget in self.winfo_toplevel().winfo_children():
                if widget.winfo_id() == int(parent_window):
                    widget.destroy()
                    break

            # Publish event
            publish("item_selected", {"item_id": item_id, "item_type": "supplies"})

        except Exception as e:
            logger.error(f"Error adding supplies to order: {e}")
            messagebox.showerror("Error", f"Failed to add supplies: {e}")

    def add_tool_to_order(self, tree, quantity_str, parent_window):
        """Add selected tool to the order.

        Args:
            tree: The treeview with tools
            quantity_str: Quantity string
            parent_window: Parent window to close
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a tool.")
            return

        try:
            # Get selected tool
            values = tree.item(selection[0], "values")
            item_id = values[0]
            name = values[1]

            # Parse price
            price_str = values[4]
            price = float(price_str.replace('$', '')) if price_str else 0

            # Parse quantity
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity = 1
            except ValueError:
                quantity = 1

            # Create item dict
            item = {
                'item_id': item_id,
                'item_type': 'tool',
                'name': name,
                'quantity': quantity,
                'unit_price': price
            }

            # Add to item list
            self.item_list.append(item)

            # Update treeview
            self.update_items_treeview()

            # Update totals
            self.update_totals()

            # Close parent window
            for widget in self.winfo_toplevel().winfo_children():
                if widget.winfo_id() == int(parent_window):
                    widget.destroy()
                    break

            # Publish event
            publish("item_selected", {"item_id": item_id, "item_type": "tool"})

        except Exception as e:
            logger.error(f"Error adding tool to order: {e}")
            messagebox.showerror("Error", f"Failed to add tool: {e}")

    def add_custom_item_to_order(self, description, quantity_str, price_str, notes, parent_window):
        """Add custom item to the order.

        Args:
            description: Item description
            quantity_str: Quantity string
            price_str: Price string
            notes: Item notes
            parent_window: Parent window to close
        """
        # Validate inputs
        if not description:
            messagebox.showinfo("Missing Information", "Please enter a description for the item.")
            return

        try:
            # Parse quantity
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity = 1
            except ValueError:
                quantity = 1

            # Parse price
            try:
                price = float(price_str)
                if price < 0:
                    price = 0
            except ValueError:
                price = 0

            # Create item dict
            item = {
                'item_id': None,
                'item_type': 'custom',
                'name': description,
                'quantity': quantity,
                'unit_price': price,
                'notes': notes
            }

            # Add to item list
            self.item_list.append(item)

            # Update treeview
            self.update_items_treeview()

            # Update totals
            self.update_totals()

            # Close parent window
            for widget in self.winfo_toplevel().winfo_children():
                if widget.winfo_id() == int(parent_window):
                    widget.destroy()
                    break

        except Exception as e:
            logger.error(f"Error adding custom item to order: {e}")
            messagebox.showerror("Error", f"Failed to add custom item: {e}")

    def on_edit_item(self):
        """Handle edit item button click."""
        selection = self.items_tree.selection()
        if not selection:
            return

        # Get selected item values
        values = self.items_tree.item(selection[0], "values")
        item_id = values[0]

        # Find item in item list
        item_index = None
        for i, item in enumerate(self.item_list):
            if str(item.get('item_id', '')) == str(item_id):
                item_index = i
                break

        if item_index is None:
            return

        # Get item
        item = self.item_list[item_index]

        # Create edit dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Edit Item")
        dialog.geometry("400x300")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Create main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Item info
        row = 0
        ttk.Label(main_frame, text="Item:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Label(main_frame, text=item.get('name', '')).grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Quantity
        row += 1
        ttk.Label(main_frame, text="Quantity:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        quantity_var = tk.StringVar(value=str(item.get('quantity', 1)))
        quantity_spinbox = ttk.Spinbox(main_frame, from_=1, to=1000, textvariable=quantity_var, width=5)
        quantity_spinbox.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Unit price
        row += 1
        ttk.Label(main_frame, text="Unit Price:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        price_var = tk.StringVar(value=f"{item.get('unit_price', 0):.2f}")
        price_entry = ttk.Entry(main_frame, textvariable=price_var, width=10)
        price_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Notes (only for custom items)
        notes_var = tk.StringVar(value=item.get('notes', ''))
        if item.get('item_type') == 'custom':
            row += 1
            ttk.Label(main_frame, text="Notes:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W + tk.N)

            notes_text = tk.Text(main_frame, height=4, width=30, wrap=tk.WORD)
            notes_text.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

            # Set notes
            if item.get('notes'):
                notes_text.insert("1.0", item.get('notes'))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row + 1, column=0, columnspan=2, padx=5, pady=10, sticky=tk.E)

        ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_edited_item(
                item_index,
                quantity_var.get(),
                price_var.get(),
                notes_var.get() if item.get('item_type') != 'custom' else notes_text.get("1.0", tk.END).strip(),
                dialog
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=(0, 5))

    def save_edited_item(self, item_index, quantity_str, price_str, notes, dialog):
        """Save edited item.

        Args:
            item_index: Index of item in item list
            quantity_str: Quantity string
            price_str: Price string
            notes: Item notes
            dialog: Dialog to close
        """
        try:
            # Parse quantity
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    quantity = 1
            except ValueError:
                quantity = 1

            # Parse price
            try:
                price = float(price_str)
                if price < 0:
                    price = 0
            except ValueError:
                price = 0

            # Update item
            self.item_list[item_index]['quantity'] = quantity
            self.item_list[item_index]['unit_price'] = price

            # Update notes if custom item
            if self.item_list[item_index].get('item_type') == 'custom':
                self.item_list[item_index]['notes'] = notes

            # Update treeview
            self.update_items_treeview()

            # Update totals
            self.update_totals()

            # Close dialog
            dialog.destroy()

        except Exception as e:
            logger.error(f"Error saving edited item: {e}")
            messagebox.showerror("Error", f"Failed to save item: {e}")

    def on_remove_item(self):
        """Handle remove item button click."""
        selection = self.items_tree.selection()
        if not selection:
            return

        # Get selected item values
        values = self.items_tree.item(selection[0], "values")
        item_id = values[0]

        # Confirm removal
        if not messagebox.askyesno("Confirm Removal", "Are you sure you want to remove this item?"):
            return

        # Find and remove item from item list
        for i, item in enumerate(self.item_list):
            if str(item.get('item_id', '')) == str(item_id):
                del self.item_list[i]
                break

        # Update treeview
        self.update_items_treeview()

        # Update totals
        self.update_totals()

    def collect_form_data(self):
        """Collect form data for saving.

        Returns:
            Dictionary with purchase data
        """
        # Get notes from text widget
        notes = self.notes_text.get("1.0", tk.END).strip()

        # Calculate totals
        subtotal = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in self.item_list)

        # Get tax rate
        try:
            tax_rate = float(self.tax_rate_var.get()) / 100
        except ValueError:
            tax_rate = 0

        # Calculate tax
        tax = subtotal * tax_rate

        # Get shipping cost
        try:
            shipping_cost = float(self.shipping_cost_var.get())
        except ValueError:
            shipping_cost = 0

        # Calculate total
        total = subtotal + tax + shipping_cost

        # Create data dictionary
        data = {
            'supplier_id': self.supplier_id_var.get(),
            'status': self.status_var.get(),
            'created_at': self.date_var.get(),
            'expected_at': self.expected_date_var.get(),
            'shipping_method': self.shipping_method_var.get(),
            'tracking_number': self.tracking_number_var.get(),
            'notes': notes,
            'update_inventory': self.update_inventory_var.get(),
            'items': self.item_list,
            'subtotal': subtotal,
            'tax_rate': tax_rate,
            'tax': tax,
            'shipping_cost': shipping_cost,
            'total_amount': total,
            'auto_receive': self.auto_receive_var.get(),
            'send_to_supplier': self.send_to_supplier_var.get()
        }

        return data

    def validate_form(self):
        """Validate form data.

        Returns:
            Tuple of (valid, error_message)
        """
        # Check supplier
        if not self.supplier_id_var.get():
            return False, "Please select a supplier."

        # Check items
        if not self.item_list:
            return False, "Please add at least one item to the purchase order."

        # Check dates
        try:
            datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD."

        if self.expected_date_var.get():
            try:
                datetime.strptime(self.expected_date_var.get(), "%Y-%m-%d")
            except ValueError:
                return False, "Invalid expected date format. Use YYYY-MM-DD."

        return True, ""

    def on_save(self):
        """Handle save button click."""
        # Validate form
        valid, error_message = self.validate_form()
        if not valid:
            messagebox.showerror("Validation Error", error_message)
            return

        # Collect form data
        data = self.collect_form_data()

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            if self.create_new:
                # Create new purchase
                result = purchase_service.create_purchase(data)

                if result:
                    messagebox.showinfo("Success", "Purchase order created successfully.")

                    # Publish event
                    publish("purchase_created", {"purchase_id": result})

                    # Navigate to purchase view
                    self.on_back()
                else:
                    messagebox.showerror("Error", "Failed to create purchase order.")
            else:
                # Update existing purchase
                result = purchase_service.update_purchase(self.purchase_id, data)

                if result:
                    messagebox.showinfo("Success", "Purchase order updated successfully.")

                    # Publish event
                    publish("purchase_updated", {"purchase_id": self.purchase_id})

                    # Navigate to purchase view
                    self.on_back()
                else:
                    messagebox.showerror("Error", "Failed to update purchase order.")

        except Exception as e:
            logger.error(f"Error saving purchase: {e}")
            messagebox.showerror("Error", f"Failed to save purchase: {e}")

    def on_cancel(self):
        """Handle cancel button click."""
        # Confirm cancel if there are changes
        if self.item_list:
            if not messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel? All changes will be lost."):
                return

        # Navigate back to purchase view
        self.on_back()

    def on_back(self):
        """Handle back button click."""
        # Navigate to purchase view
        self.master.show_view("purchase_view")

    def on_edit(self):
        """Handle edit button click in readonly mode."""
        # Create view data
        view_data = {
            "purchase_id": self.purchase_id,
            "readonly": False
        }

        # Navigate to purchase details view in edit mode
        self.master.show_view("purchase_details_view", view_data=view_data)

    def on_print(self):
        """Handle print button click."""
        try:
            # Check if purchase ID exists
            if not self.purchase_id:
                messagebox.showerror("Error", "Please save the purchase order first.")
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Print purchase order
            result = purchase_service.print_purchase_order(self.purchase_id)

            if result:
                messagebox.showinfo(
                    "Print Complete",
                    f"Purchase order has been generated successfully.\n\nFile: {result}"
                )
            else:
                messagebox.showerror("Error", "Failed to generate purchase order.")

        except Exception as e:
            logger.error(f"Error printing purchase order: {e}")
            messagebox.showerror("Error", f"Failed to print purchase order: {e}")

    def on_receive(self):
        """Handle receive items button click."""
        # Navigate to the purchase view to handle receiving
        view_data = {"filter_purchase_id": self.purchase_id}
        self.master.show_view("purchase_view", view_data=view_data)

        # Trigger the receive action
        publish("trigger_receive", {"purchase_id": self.purchase_id})

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create date picker dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Select Date")
        dialog.geometry("300x250")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Create calendar frame
        cal_frame = ttk.Frame(dialog)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Month and year label and navigation
        header_frame = ttk.Frame(cal_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            header_frame,
            text="<",
            width=3,
            command=lambda: self.prev_month(month_year_label, cal_grid)
        ).pack(side=tk.LEFT, padx=5)

        # Initialize with current date
        now = datetime.now()
        self.cal_year = now.year
        self.cal_month = now.month

        month_year_label = ttk.Label(
            header_frame,
            text=f"{now.strftime('%B')} {now.year}",
            font=("", 12, "bold")
        )
        month_year_label.pack(side=tk.LEFT, padx=5, expand=True)

        ttk.Button(
            header_frame,
            text=">",
            width=3,
            command=lambda: self.next_month(month_year_label, cal_grid)
        ).pack(side=tk.LEFT, padx=5)

        # Create calendar grid
        cal_grid = ttk.Frame(cal_frame)
        cal_grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create weekday headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(weekdays):
            ttk.Label(
                cal_grid,
                text=day,
                font=("", 10, "bold"),
                anchor="center"
            ).grid(row=0, column=i, padx=2, pady=2, sticky="nsew")

        # Update calendar with current month
        self.update_calendar(cal_grid, month_year_label, self.cal_year, self.cal_month, date_var, dialog)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    # purchase_details_view.py functions

    def on_receive(self):
        """Handle receive items button click."""
        if not self.purchase_id:
            self.show_error("Error", "No purchase selected for receiving items.")
            return

        if not self._current_purchase:
            self.load_purchase()

        # Create a dialog for receiving items
        dialog = BaseDialog(self.parent, "Receive Purchase Items", width=700, height=600)
        dialog_frame = ttk.Frame(dialog.interior)
        dialog_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Date of receipt
        date_frame = ttk.Frame(dialog_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Date of Receipt:").pack(side=tk.LEFT, padx=(0, 5))
        receive_date_var = tk.StringVar(value=datetime.now().strftime(config.DATE_FORMAT))
        date_entry = ttk.Entry(date_frame, textvariable=receive_date_var, width=15)
        date_entry.pack(side=tk.LEFT)
        ttk.Button(date_frame, text="📅", width=3,
                   command=lambda: self.show_date_picker(receive_date_var)).pack(side=tk.LEFT)

        # Create a treeview to display the items
        tree_frame = ttk.Frame(dialog_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tree = EnhancedTreeview(
            tree_frame,
            columns=("id", "item", "type", "ordered", "received", "remaining", "receive_qty"),
            show="headings",
            height=10
        )
        tree.heading("id", text="ID")
        tree.heading("item", text="Item")
        tree.heading("type", text="Type")
        tree.heading("ordered", text="Ordered")
        tree.heading("received", text="Received")
        tree.heading("remaining", text="Remaining")
        tree.heading("receive_qty", text="Receive")

        tree.column("id", width=50, stretch=False)
        tree.column("item", width=200)
        tree.column("type", width=80, stretch=False)
        tree.column("ordered", width=80, stretch=False, anchor=tk.CENTER)
        tree.column("received", width=80, stretch=False, anchor=tk.CENTER)
        tree.column("remaining", width=80, stretch=False, anchor=tk.CENTER)
        tree.column("receive_qty", width=80, stretch=False, anchor=tk.CENTER)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        # Create dictionary to store item quantity variables
        item_vars = {}

        # Populate the treeview
        service = get_service('purchase_service')
        purchase_items = service.get_purchase_items(self.purchase_id)

        for item in purchase_items:
            # Create a variable to store the quantity to receive
            item_id = item.id
            remaining_qty = item.quantity - item.quantity_received

            if remaining_qty <= 0:
                continue  # Skip fully received items

            item_vars[item_id] = tk.StringVar(value=str(remaining_qty))

            # Item name based on type
            item_name = self._get_item_display_name(item)

            tree.insert("", "end", iid=str(item_id), values=(
                item_id,
                item_name,
                item.item_type,
                item.quantity,
                item.quantity_received,
                remaining_qty,
                remaining_qty
            ))

        # Handler for row selection
        tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # Create spin buttons for each row to adjust quantities
        for item_id, var in item_vars.items():
            col_id = tree.column("receive_qty", "id")

            x, y = tree.bbox(item_id, col_id)[:2]

            # Adjust position to center on the cell
            cell_width = tree.column("receive_qty", "width")

            # Create a frame for the spinbox within the cell
            item_frame = ttk.Frame(tree)
            tree.window_create(item_id, col_id, window=item_frame)

            # Create spinbox with min=0, max=remaining
            remaining = int(tree.item(item_id, "values")[5])
            spinbox = ttk.Spinbox(
                item_frame,
                from_=0,
                to=remaining,
                textvariable=var,
                width=5,
                command=lambda var=var: self.update_receive_quantity(tree, item_vars, var.get())
            )
            spinbox.pack(side=tk.LEFT)

            # Update the item's quantity when spinbox value changes
            var.trace_add("write", lambda name, index, mode, var=var:
            self.update_receive_quantity(tree, item_vars, var.get()))

        # Notes section
        ttk.Label(dialog_frame, text="Notes:").pack(anchor=tk.W, pady=(10, 5))
        notes_text = tk.Text(dialog_frame, height=3, width=50)
        notes_text.pack(fill=tk.X)

        # Buttons
        btn_frame = ttk.Frame(dialog_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="Receive All Items",
            command=lambda: self.process_receive(
                self.purchase_id,
                tree,
                item_vars,
                receive_date_var.get(),
                notes_text.get("1.0", "end-1c"),
                dialog
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.close
        ).pack(side=tk.RIGHT, padx=5)

        dialog.show()

    def on_item_select(self, event):
        """Handle item selection in the treeview.

        Args:
            event: The TreeviewSelect event
        """
        # Implementation can be added if needed
        pass

    def update_receive_quantity(self, tree, item_vars, qty):
        """Update receive quantity for selected item.

        Args:
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            qty: New quantity as string
        """
        # Validate quantity
        try:
            if qty and qty.strip():
                qty_val = int(qty)
                if qty_val < 0:
                    return
            else:
                return
        except ValueError:
            return

        # Update the tree display for the selected item
        selected_id = tree.selection()
        if selected_id:
            item_id = selected_id[0]
            values = list(tree.item(item_id, "values"))
            values[6] = qty
            tree.item(item_id, values=values)

    def process_receive(self, purchase_id, tree, item_vars, receive_date, notes, dialog):
        """Process receive action.

        Args:
            purchase_id: ID of the purchase
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            receive_date: Date of receipt
            notes: Receipt notes
            dialog: Dialog to close on success
        """
        try:
            # Convert receive date
            try:
                receive_date_obj = datetime.strptime(receive_date, config.DATE_FORMAT)
            except ValueError:
                self.show_error("Invalid Date", "Please enter a valid date in the format YYYY-MM-DD.")
                return

            # Collect items to receive
            items_to_receive = []
            for item_id, qty_var in item_vars.items():
                try:
                    qty = int(qty_var.get())
                    if qty > 0:
                        items_to_receive.append({
                            'item_id': int(item_id),
                            'quantity': qty
                        })
                except (ValueError, TypeError):
                    pass

            if not items_to_receive:
                self.show_warning("No Items", "No items selected for receiving.")
                return

            # Call service to receive items
            service = get_service('purchase_service')
            receive_data = {
                'purchase_id': purchase_id,
                'items': items_to_receive,
                'receive_date': receive_date_obj,
                'notes': notes
            }

            result = service.receive_purchase_items(receive_data)

            # Update inventory if successful
            if result:
                messagebox.showinfo("Success", f"Successfully received {len(items_to_receive)} items.")
                dialog.close()

                # Publish event for inventory update
                publish('purchase_updated', {'purchase_id': purchase_id})
                publish('inventory_updated', {'source': 'purchase_receive'})

                # Refresh the view
                self.refresh()
            else:
                self.show_error("Error", "Failed to receive items.")

        except Exception as e:
            logging.error(f"Error receiving purchase items: {str(e)}")
            self.show_error("Error", f"Failed to receive items: {str(e)}")

    def _get_item_display_name(self, item):
        """Get display name for an item.

        Args:
            item: The purchase item

        Returns:
            Display name for the item
        """
        if item.item_type == 'material':
            material_service = get_service('material_service')
            material = material_service.get_by_id(item.item_id)
            return material.name if material else f"Material #{item.item_id}"
        elif item.item_type == 'tool':
            tool_service = get_service('tool_service')
            tool = tool_service.get_by_id(item.item_id)
            return tool.name if tool else f"Tool #{item.item_id}"
        else:
            return f"Item #{item.item_id}"

    def on_update_status(self):
        """Handle update status action."""
        if not self.purchase_id:
            self.show_error("Error", "No purchase selected.")
            return

        if not self._current_purchase:
            self.load_purchase()

        # Create a dialog for updating status
        dialog = BaseDialog(self.parent, "Update Purchase Status", width=500, height=300)
        frame = ttk.Frame(dialog.interior)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Current status
        ttk.Label(frame, text="Current Status:").grid(row=0, column=0, sticky=tk.W, pady=5)
        current_status = self._current_purchase.status.value if self._current_purchase and hasattr(
            self._current_purchase, 'status') else "Unknown"
        status_badge = StatusBadge(frame, current_status, current_status)
        status_badge.grid(row=0, column=1, sticky=tk.W, pady=5)

        # New status
        ttk.Label(frame, text="New Status:").grid(row=1, column=0, sticky=tk.W, pady=5)

        status_options = [status.value for status in PurchaseStatus]
        status_var = tk.StringVar()
        status_combobox = ttk.Combobox(frame, textvariable=status_var, values=status_options, state="readonly",
                                       width=25)
        status_combobox.set(current_status)
        status_combobox.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        notes_text = tk.Text(frame, height=5, width=30)
        notes_text.grid(row=2, column=1, sticky=tk.EW, pady=5)

        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)

        ttk.Button(
            btn_frame,
            text="Update",
            command=lambda: self.update_purchase_status(
                self.purchase_id,
                status_var.get(),
                notes_text.get("1.0", "end-1c"),
                dialog
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.close
        ).pack(side=tk.RIGHT, padx=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

        dialog.show()

    def update_purchase_status(self, purchase_id, status, notes, dialog):
        """Update purchase status.

        Args:
            purchase_id: ID of the purchase
            status: New status value
            notes: Status change notes
            dialog: Dialog to close on success
        """
        try:
            service = get_service('purchase_service')

            result = service.update_purchase_status(purchase_id, status, notes)

            if result:
                messagebox.showinfo("Success", "Purchase status updated successfully.")
                dialog.close()

                # Publish event for update
                publish('purchase_updated', {'purchase_id': purchase_id})

                # Refresh the view
                self.refresh()
            else:
                self.show_error("Error", "Failed to update purchase status.")

        except Exception as e:
            logging.error(f"Error updating purchase status: {str(e)}")
            self.show_error("Error", f"Failed to update status: {str(e)}")

    def on_print(self):
        """Handle print purchase order action."""
        if not self.purchase_id:
            self.show_error("Error", "No purchase selected for printing.")
            return

        if not self._current_purchase:
            self.load_purchase()

        # Create dialog for print options
        dialog = BaseDialog(self.parent, "Print Purchase Order", width=500, height=300)
        frame = ttk.Frame(dialog.interior)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Print options
        options_frame = ttk.LabelFrame(frame, text="Print Options")
        options_frame.pack(fill=tk.X, pady=10)

        # Include options
        include_supplier_info = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include Supplier Information", variable=include_supplier_info).pack(
            anchor=tk.W, padx=10, pady=2)

        include_pricing = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include Pricing Information", variable=include_pricing).pack(anchor=tk.W,
                                                                                                          padx=10,
                                                                                                          pady=2)

        include_company_logo = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include Company Logo", variable=include_company_logo).pack(anchor=tk.W,
                                                                                                        padx=10, pady=2)

        include_signature = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include Signature Line", variable=include_signature).pack(anchor=tk.W,
                                                                                                       padx=10, pady=2)

        # Output options
        output_frame = ttk.LabelFrame(frame, text="Output Options")
        output_frame.pack(fill=tk.X, pady=10)

        output_format = tk.StringVar(value="pdf")
        ttk.Radiobutton(output_frame, text="PDF Document", variable=output_format, value="pdf").pack(anchor=tk.W,
                                                                                                     padx=10, pady=2)
        ttk.Radiobutton(output_frame, text="HTML Document", variable=output_format, value="html").pack(anchor=tk.W,
                                                                                                       padx=10, pady=2)

        # File destination
        file_frame = ttk.Frame(output_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(file_frame, text="Save to:").pack(side=tk.LEFT, padx=(0, 5))

        file_path_var = tk.StringVar(value=f"purchase_order_{self.purchase_id}.pdf")
        file_entry = ttk.Entry(file_frame, textvariable=file_path_var, width=30)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(file_frame, text="Browse...",
                   command=lambda: self._browse_output_file(file_path_var, output_format.get())).pack(side=tk.LEFT)

        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="Preview",
            command=lambda: self._preview_purchase_order(
                include_supplier_info.get(),
                include_pricing.get(),
                include_company_logo.get(),
                include_signature.get(),
                output_format.get()
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Print",
            command=lambda: self._print_purchase_order(
                include_supplier_info.get(),
                include_pricing.get(),
                include_company_logo.get(),
                include_signature.get(),
                output_format.get(),
                file_path_var.get(),
                dialog
            )
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.close
        ).pack(side=tk.RIGHT, padx=5)

        dialog.show()

    def _browse_output_file(self, path_var, format_type):
        """Browse for output file location.

        Args:
            path_var: StringVar to store selected path
            format_type: File format (pdf, html)
        """
        extension = f".{format_type}"
        file_types = [("PDF Files", "*.pdf")] if format_type == "pdf" else [("HTML Files", "*.html")]
        file_types.append(("All Files", "*.*"))

        filename = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=file_types,
            title="Save Purchase Order"
        )

        if filename:
            path_var.set(filename)

    def _preview_purchase_order(self, include_supplier, include_pricing, include_logo, include_signature,
                                output_format):
        """Preview purchase order before printing.

        Args:
            include_supplier: Whether to include supplier info
            include_pricing: Whether to include pricing info
            include_logo: Whether to include company logo
            include_signature: Whether to include signature line
            output_format: Output format (pdf, html)
        """
        if not self.purchase_id or not self._current_purchase:
            self.show_error("Error", "No purchase data available for preview.")
            return

        try:
            service = get_service('purchase_service')

            # Generate a temporary preview file
            options = {
                'include_supplier_info': include_supplier,
                'include_pricing': include_pricing,
                'include_company_logo': include_logo,
                'include_signature': include_signature,
                'output_format': output_format,
                'preview_mode': True
            }

            preview_file = service.generate_purchase_order_document(self.purchase_id, options)

            if preview_file:
                # Open the preview file with default application
                self._open_with_default_app(preview_file)
            else:
                self.show_error("Preview Error", "Failed to generate preview.")

        except Exception as e:
            logging.error(f"Error generating purchase order preview: {str(e)}")
            self.show_error("Preview Error", f"Failed to generate preview: {str(e)}")

    def _print_purchase_order(self, include_supplier, include_pricing, include_logo, include_signature,
                              output_format, file_path, dialog):
        """Print or save purchase order.

        Args:
            include_supplier: Whether to include supplier info
            include_pricing: Whether to include pricing info
            include_logo: Whether to include company logo
            include_signature: Whether to include signature line
            output_format: Output format (pdf, html)
            file_path: Path to save the file
            dialog: Dialog to close on success
        """
        if not self.purchase_id or not self._current_purchase:
            self.show_error("Error", "No purchase data available for printing.")
            return

        if not file_path:
            self.show_warning("No File Path", "Please specify a file path for saving the purchase order.")
            return

        try:
            service = get_service('purchase_service')

            # Generate the purchase order document
            options = {
                'include_supplier_info': include_supplier,
                'include_pricing': include_pricing,
                'include_company_logo': include_logo,
                'include_signature': include_signature,
                'output_format': output_format,
                'output_path': file_path
            }

            result = service.generate_purchase_order_document(self.purchase_id, options)

            if result:
                messagebox.showinfo("Success", f"Purchase order saved to {file_path}")
                dialog.close()

                # Ask if user wants to open the file
                if messagebox.askyesno("Open File", "Do you want to open the saved file?"):
                    self._open_with_default_app(file_path)
            else:
                self.show_error("Print Error", "Failed to generate purchase order document.")

        except Exception as e:
            logging.error(f"Error generating purchase order document: {str(e)}")
            self.show_error("Print Error", f"Failed to generate document: {str(e)}")

    def _open_with_default_app(self, file_path):
        """Open a file with the default system application.

        Args:
            file_path: Path to the file to open
        """
        try:
            import os
            import platform
            import subprocess

            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux and other Unix-like
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            logging.error(f"Error opening file: {str(e)}")
            self.show_warning("Open File Error", "Could not open the file with the default application.")

    def update_receive_quantity(self, tree, item_vars, qty):
        """Update receive quantity for selected item.

        Args:
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            qty: New quantity as string
        """
        selection = tree.selection()
        if not selection:
            return

        # Get selected item
        item_values = tree.item(selection[0], "values")
        item_id = item_values[0]
        ordered = int(item_values[2])
        received = int(item_values[3])
        max_receive = ordered - received

        # Validate quantity
        try:
            new_qty = int(qty)
            if new_qty < 0:
                new_qty = 0
            elif new_qty > max_receive:
                new_qty = max_receive
        except ValueError:
            new_qty = 0

        # Update variable
        if item_id in item_vars:
            item_vars[item_id].set(str(new_qty))

        # Update tree
        tree.item(
            selection[0],
            values=(
                item_id,
                item_values[1],
                ordered,
                received,
                new_qty,
                "Pending"
            )
        )

    def process_receive(self, purchase_id, tree, item_vars, receive_date, notes, dialog):
        """Process receive action.

        Args:
            purchase_id: ID of the purchase
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            receive_date: Date of receipt
            notes: Receipt notes
            dialog: Dialog to close on success
        """
        try:
            # Create receipt data
            receipt_data = {
                'purchase_id': purchase_id,
                'receive_date': receive_date,
                'notes': notes,
                'items': []
            }

            # Add items with quantities to receive
            for item_id, qty_var in item_vars.items():
                try:
                    qty = int(qty_var.get())
                    if qty > 0:
                        receipt_data['items'].append({
                            'item_id': item_id,
                            'quantity': qty
                        })
                except ValueError:
                    pass

            # Validate at least one item
            if not receipt_data['items']:
                messagebox.showerror("Error", "Please enter at least one item to receive.")
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Process receipt
            result = purchase_service.receive_purchase_items(receipt_data)

            if result:
                messagebox.showinfo("Success", "Items received successfully.")
                dialog.destroy()

                # Publish event
                publish("purchase_updated", {"purchase_id": purchase_id})
                publish("inventory_updated", {})

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to receive items.")

        except Exception as e:
            logger.error(f"Error receiving items: {e}")
            messagebox.showerror("Error", f"Failed to receive items: {e}")

    def on_update_status(self):
        """Handle update status action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get purchase details
            purchase = purchase_service.get_purchase(selected_id)

            if not purchase:
                messagebox.showerror("Error", f"Could not find purchase with ID {selected_id}")
                return

            # Get current status
            current_status = purchase.get('status', '')
            if hasattr(current_status, 'name'):
                current_status = current_status.name

            # Create status dialog
            dialog = tk.Toplevel(self.winfo_toplevel())
            dialog.title("Update Purchase Status")
            dialog.geometry("400x250")
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()

            # Create main frame
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Current status
            ttk.Label(main_frame, text=f"Current Status: {current_status}").pack(anchor=tk.W, pady=(0, 10))

            # New status
            ttk.Label(main_frame, text="New Status:").pack(anchor=tk.W)

            # Status options
            statuses = [status.name for status in PurchaseStatus]
            status_var = tk.StringVar(value=current_status)

            status_combo = ttk.Combobox(
                main_frame,
                textvariable=status_var,
                values=statuses,
                state="readonly",
                width=20
            )
            status_combo.pack(anchor=tk.W, pady=(5, 10))

            # Notes
            ttk.Label(main_frame, text="Status Change Notes:").pack(anchor=tk.W)

            notes_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=notes_var, width=40).pack(fill=tk.X, pady=(5, 10))

            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Button(
                button_frame,
                text="Update",
                command=lambda: self.update_purchase_status(
                    selected_id,
                    status_var.get(),
                    notes_var.get(),
                    dialog
                ),
                style="Accent.TButton"
            ).pack(side=tk.RIGHT, padx=(5, 0))

            ttk.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=(0, 5))

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            messagebox.showerror("Error", f"Failed to update status: {e}")

    def update_purchase_status(self, purchase_id, status, notes, dialog):
        """Update purchase status.

        Args:
            purchase_id: ID of the purchase
            status: New status value
            notes: Status change notes
            dialog: Dialog to close on success
        """
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Update status
            result = purchase_service.update_purchase_status(
                purchase_id,
                status,
                notes
            )

            if result:
                messagebox.showinfo("Success", "Status updated successfully.")
                dialog.destroy()

                # Publish event
                publish("purchase_updated", {"purchase_id": purchase_id})

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to update status.")

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            messagebox.showerror("Error", f"Failed to update status: {e}")

    def on_print(self):
        """Handle print purchase order action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Print purchase order
            result = purchase_service.print_purchase_order(selected_id)

            if result:
                messagebox.showinfo(
                    "Print Complete",
                    f"Purchase order has been generated successfully.\n\nFile: {result}"
                )
            else:
                messagebox.showerror("Error", "Failed to generate purchase order.")

        except Exception as e:
            logger.error(f"Error printing purchase order: {e}")
            messagebox.showerror("Error", f"Failed to print purchase order: {e}")

