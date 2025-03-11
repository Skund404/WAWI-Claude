# views/purchases/supplier_details_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import SupplierStatus

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class SupplierDetailsDialog(BaseDialog):
    """Dialog for viewing, creating and editing supplier details."""

    def __init__(self, parent, **kwargs):
        """Initialize the supplier details dialog.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                supplier_id: ID of the supplier to view/edit (None for new suppliers)
                create_new: Whether to create a new supplier
                readonly: Whether the dialog is in read-only mode
        """
        self.supplier_id = kwargs.get('supplier_id')
        self.create_new = kwargs.get('create_new', False)
        self.readonly = kwargs.get('readonly', False)

        # Set title based on mode
        if self.create_new:
            title = "Create New Supplier"
        elif self.readonly:
            title = "Supplier Details"
        else:
            title = "Edit Supplier"

        # Initialize form variables
        self._initialize_form_variables()

        # Initialize dialog
        super().__init__(
            parent,
            title=title,
            width=800,
            height=600,
            modal=True
        )

    def _initialize_form_variables(self):
        """Initialize form variables for data binding."""
        # Basic info
        self.name_var = tk.StringVar()
        self.status_var = tk.StringVar(value=SupplierStatus.ACTIVE.name)
        self.active_since_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.notes_var = tk.StringVar()

        # Contact info
        self.contact_name_var = tk.StringVar()
        self.contact_email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.website_var = tk.StringVar()

        # Address info
        self.address_line1_var = tk.StringVar()
        self.address_line2_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.postal_code_var = tk.StringVar()
        self.country_var = tk.StringVar()

        # Payment info
        self.payment_terms_var = tk.StringVar()
        self.tax_id_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="USD")
        self.preferred_payment_method_var = tk.StringVar()

        # Initialize custom fields dict
        self.custom_fields = {}

    def create_layout(self):
        """Create the dialog layout."""
        # Create main frame
        main_frame = ttk.Frame(self.dialog_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create header with status badge
        self.create_header_section(main_frame)

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

        # Create tabs
        self.create_basic_info_tab(notebook)
        self.create_contact_tab(notebook)
        self.create_address_tab(notebook)
        self.create_payment_tab(notebook)
        self.create_purchase_history_tab(notebook)
        self.create_notes_tab(notebook)

        # Create buttons section
        self.create_buttons_section(main_frame)

        # Load supplier data if editing
        if self.supplier_id:
            self.load_supplier_data()

        # Update UI state based on mode
        self.update_ui_state()

    def create_header_section(self, parent):
        """Create header section with supplier overview.

        Args:
            parent: The parent widget
        """
        # Create header frame
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        # Left side with supplier name
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        if self.create_new:
            header_text = "New Supplier"
            self.supplier_name_label = ttk.Label(
                left_frame,
                text=header_text,
                font=("", 16, "bold")
            )
        else:
            self.supplier_name_label = ttk.Label(
                left_frame,
                text="Loading...",
                font=("", 16, "bold")
            )

        self.supplier_name_label.pack(anchor=tk.W)

        if not self.create_new:
            supplier_id_text = f"ID: {self.supplier_id}" if self.supplier_id else ""
            self.supplier_id_label = ttk.Label(
                left_frame,
                text=supplier_id_text,
                style="Secondary.TLabel"
            )
            self.supplier_id_label.pack(anchor=tk.W)

        # Right side with status badge
        right_frame = ttk.Frame(header_frame)
        right_frame.pack(side=tk.RIGHT, padx=(20, 0))

        if not self.create_new:
            self.status_badge = StatusBadge(
                right_frame,
                text="Loading...",
                status_value="ACTIVE"
            )
            self.status_badge.pack(side=tk.RIGHT)

            ttk.Label(right_frame, text="Status:").pack(side=tk.RIGHT, padx=(0, 5))

    def create_basic_info_tab(self, notebook):
        """Create the basic information tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Basic Information")

        # Create form frame
        form_frame = ttk.Frame(tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Supplier name
        row = 0
        ttk.Label(form_frame, text="Supplier Name:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Status
        row += 1
        ttk.Label(form_frame, text="Status:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        statuses = [status.name for status in SupplierStatus]
        self.status_combo = ttk.Combobox(
            form_frame,
            textvariable=self.status_var,
            values=statuses,
            state="readonly",
            width=20
        )
        self.status_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Active since
        row += 1
        ttk.Label(form_frame, text="Active Since:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        date_frame = ttk.Frame(form_frame)
        date_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        self.active_since_entry = ttk.Entry(date_frame, textvariable=self.active_since_var, width=15)
        self.active_since_entry.pack(side=tk.LEFT)

        self.calendar_btn = ttk.Button(
            date_frame,
            text="...",
            width=3,
            command=lambda: self.show_date_picker(self.active_since_var)
        )
        self.calendar_btn.pack(side=tk.LEFT, padx=(5, 0))

        # Custom fields
        row += 1
        ttk.Label(form_frame, text="Custom Fields:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        # Frame for custom fields
        self.custom_fields_frame = ttk.Frame(form_frame)
        self.custom_fields_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Add button for custom fields
        self.add_field_btn = ttk.Button(
            self.custom_fields_frame,
            text="Add Field",
            command=self.add_custom_field
        )
        self.add_field_btn.pack(anchor=tk.W)

    def create_contact_tab(self, notebook):
        """Create the contact information tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Contact Information")

        # Create form frame
        form_frame = ttk.Frame(tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Contact name
        row = 0
        ttk.Label(form_frame, text="Contact Name:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.contact_name_entry = ttk.Entry(form_frame, textvariable=self.contact_name_var, width=40)
        self.contact_name_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Contact email
        row += 1
        ttk.Label(form_frame, text="Contact Email:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.contact_email_entry = ttk.Entry(form_frame, textvariable=self.contact_email_var, width=40)
        self.contact_email_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Phone
        row += 1
        ttk.Label(form_frame, text="Phone:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.phone_entry = ttk.Entry(form_frame, textvariable=self.phone_var, width=20)
        self.phone_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Website
        row += 1
        ttk.Label(form_frame, text="Website:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.website_entry = ttk.Entry(form_frame, textvariable=self.website_var, width=40)
        self.website_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

    def create_address_tab(self, notebook):
        """Create the address tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Address")

        # Create form frame
        form_frame = ttk.Frame(tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Address line 1
        row = 0
        ttk.Label(form_frame, text="Address Line 1:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.address_line1_entry = ttk.Entry(form_frame, textvariable=self.address_line1_var, width=40)
        self.address_line1_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Address line 2
        row += 1
        ttk.Label(form_frame, text="Address Line 2:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.address_line2_entry = ttk.Entry(form_frame, textvariable=self.address_line2_var, width=40)
        self.address_line2_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # City
        row += 1
        ttk.Label(form_frame, text="City:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.city_entry = ttk.Entry(form_frame, textvariable=self.city_var, width=30)
        self.city_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # State & Postal Code
        row += 1
        ttk.Label(form_frame, text="State/Province:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        state_zip_frame = ttk.Frame(form_frame)
        state_zip_frame.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        self.state_entry = ttk.Entry(state_zip_frame, textvariable=self.state_var, width=20)
        self.state_entry.pack(side=tk.LEFT)

        ttk.Label(state_zip_frame, text="Postal Code:").pack(side=tk.LEFT, padx=(20, 5))

        self.postal_code_entry = ttk.Entry(state_zip_frame, textvariable=self.postal_code_var, width=15)
        self.postal_code_entry.pack(side=tk.LEFT)

        # Country
        row += 1
        ttk.Label(form_frame, text="Country:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.country_entry = ttk.Entry(form_frame, textvariable=self.country_var, width=30)
        self.country_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

    def create_payment_tab(self, notebook):
        """Create the payment tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Payment Information")

        # Create form frame
        form_frame = ttk.Frame(tab)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Configure grid
        form_frame.columnconfigure(1, weight=1)

        # Payment terms
        row = 0
        ttk.Label(form_frame, text="Payment Terms:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.payment_terms_entry = ttk.Entry(form_frame, textvariable=self.payment_terms_var, width=30)
        self.payment_terms_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Tax ID
        row += 1
        ttk.Label(form_frame, text="Tax ID:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
        self.tax_id_entry = ttk.Entry(form_frame, textvariable=self.tax_id_var, width=20)
        self.tax_id_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Currency
        row += 1
        ttk.Label(form_frame, text="Currency:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY"]
        self.currency_combo = ttk.Combobox(
            form_frame,
            textvariable=self.currency_var,
            values=currencies,
            state="readonly",
            width=10
        )
        self.currency_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

        # Preferred payment method
        row += 1
        ttk.Label(form_frame, text="Preferred Payment:").grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)

        payment_methods = ["ACH", "Wire Transfer", "Credit Card", "Check", "PayPal", "Other"]
        self.payment_method_combo = ttk.Combobox(
            form_frame,
            textvariable=self.preferred_payment_method_var,
            values=payment_methods,
            state="readonly",
            width=20
        )
        self.payment_method_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)

    def create_purchase_history_tab(self, notebook):
        """Create the purchase history tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Purchase History")

        # Create content frame
        content_frame = ttk.Frame(tab)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview for purchase history
        self.history_tree = ttk.Treeview(
            content_frame,
            columns=("id", "date", "amount", "status", "items"),
            show="headings",
            selectmode="browse"
        )

        # Set column headings
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("amount", text="Amount")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("items", text="Items")

        # Configure column widths
        self.history_tree.column("id", width=50, stretch=False)
        self.history_tree.column("date", width=100, stretch=False)
        self.history_tree.column("amount", width=100, stretch=False)
        self.history_tree.column("status", width=100, stretch=False)
        self.history_tree.column("items", width=200, stretch=True)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)

        # Place widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        actions_frame = ttk.Frame(tab)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            actions_frame,
            text="View Purchase",
            command=self.on_view_purchase
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            actions_frame,
            text="Create Purchase",
            command=self.on_create_purchase
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            actions_frame,
            text="Export History",
            command=self.on_export_history
        ).pack(side=tk.RIGHT, padx=5)

        # Bind double-click
        self.history_tree.bind("<Double-1>", self.on_view_purchase)

    def create_notes_tab(self, notebook):
        """Create the notes tab."""
        # Create tab frame
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Notes")

        # Create notes frame
        notes_frame = ttk.Frame(tab)
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create text editor
        self.notes_text = tk.Text(
            notes_frame,
            wrap=tk.WORD,
            height=15,
            width=60
        )
        self.notes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        self.notes_text.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create formatting toolbar
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Add date button
        ttk.Button(
            toolbar,
            text="Add Date",
            width=10,
            command=self.add_date_to_notes
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Add signature button
        ttk.Button(
            toolbar,
            text="Add Signature",
            width=12,
            command=self.add_signature_to_notes
        ).pack(side=tk.LEFT, padx=5)

    def create_buttons_section(self, parent):
        """Create buttons section.

        Args:
            parent: The parent widget
        """
        # Create buttons frame
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create Save button
        self.save_btn = ttk.Button(
            buttons_frame,
            text="Save",
            command=self.on_save,
            style="Accent.TButton"
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5)

        # Create Cancel button
        self.cancel_btn = ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self.close
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Create Edit button (for readonly mode)
        self.edit_btn = ttk.Button(
            buttons_frame,
            text="Edit",
            command=self.on_edit,
            style="Accent.TButton"
        )

        # Create button to view all purchases
        if not self.create_new:
            self.all_purchases_btn = ttk.Button(
                buttons_frame,
                text="View All Purchases",
                command=self.on_view_all_purchases
            )
            self.all_purchases_btn.pack(side=tk.LEFT, padx=5)

    def load_supplier_data(self):
        """Load supplier data from the service."""
        try:
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Get supplier data
            supplier = supplier_service.get_supplier(self.supplier_id)

            if not supplier:
                messagebox.showerror("Error", f"Could not find supplier with ID {self.supplier_id}")
                self.close()
                return

            # Update header
            self.supplier_name_label.config(text=supplier.get('name', 'Unknown Supplier'))

            # Update status badge if exists
            if hasattr(self, 'status_badge'):
                status = supplier.get('status', 'UNKNOWN')
                if isinstance(status, SupplierStatus):
                    status = status.name
                self.status_badge.set_text(status, status)

            # Populate form fields
            self.name_var.set(supplier.get('name', ''))
            self.status_var.set(supplier.get('status', ''))

            # Format active_since date
            active_since = supplier.get('active_since')
            if active_since:
                if isinstance(active_since, datetime):
                    active_since = active_since.strftime('%Y-%m-%d')
                self.active_since_var.set(active_since)

            # Contact info
            self.contact_name_var.set(supplier.get('contact_name', ''))
            self.contact_email_var.set(supplier.get('contact_email', ''))
            self.phone_var.set(supplier.get('phone', ''))
            self.website_var.set(supplier.get('website', ''))

            # Address info
            address = supplier.get('address', {})
            self.address_line1_var.set(address.get('line1', ''))
            self.address_line2_var.set(address.get('line2', ''))
            self.city_var.set(address.get('city', ''))
            self.state_var.set(address.get('state', ''))
            self.postal_code_var.set(address.get('postal_code', ''))
            self.country_var.set(address.get('country', ''))

            # Payment info
            payment_info = supplier.get('payment_info', {})
            self.payment_terms_var.set(payment_info.get('terms', ''))
            self.tax_id_var.set(payment_info.get('tax_id', ''))
            self.currency_var.set(payment_info.get('currency', 'USD'))
            self.preferred_payment_method_var.set(payment_info.get('preferred_method', ''))

            # Notes
            if supplier.get('notes'):
                self.notes_text.delete('1.0', tk.END)
                self.notes_text.insert('1.0', supplier.get('notes', ''))

            # Custom fields
            custom_fields = supplier.get('custom_fields', {})
            if custom_fields:
                for field, value in custom_fields.items():
                    self.add_custom_field(field, value)

            # Load purchase history
            self.load_purchase_history(supplier)

        except Exception as e:
            logger.error(f"Error loading supplier data: {e}")
            messagebox.showerror("Error", f"Failed to load supplier data: {e}")

    def load_purchase_history(self, supplier):
        """Load purchase history data.

        Args:
            supplier: Supplier data object
        """
        try:
            # Clear existing items
            self.history_tree.delete(*self.history_tree.get_children())

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get purchase history
            purchases = purchase_service.get_supplier_purchases(self.supplier_id)

            # Insert into treeview
            for purchase in purchases:
                # Format date
                purchase_date = purchase.get('created_at', '')
                if isinstance(purchase_date, datetime):
                    purchase_date = purchase_date.strftime('%Y-%m-%d')

                # Format amount
                amount = purchase.get('total_amount', 0)
                if isinstance(amount, (int, float)):
                    amount = f"${amount:.2f}"

                # Format status
                status = purchase.get('status', '')

                # Format items count
                items_count = len(purchase.get('items', []))

                # Insert into tree
                self.history_tree.insert(
                    '',
                    'end',
                    values=(
                        purchase.get('id', ''),
                        purchase_date,
                        amount,
                        status,
                        f"{items_count} items"
                    )
                )

        except Exception as e:
            logger.error(f"Error loading purchase history: {e}")
            # Don't show error message, just log it

    def update_ui_state(self):
        """Update UI elements based on current state (readonly/edit)."""
        # Set all fields readonly in readonly mode
        readonly_state = "readonly" if self.readonly else "normal"
        disabled_state = tk.DISABLED if self.readonly else tk.NORMAL

        # Basic info
        self.name_entry.config(state=readonly_state)
        self.status_combo.config(state=readonly_state)
        self.active_since_entry.config(state=readonly_state)
        self.calendar_btn.config(state=disabled_state)

        # Add field button
        if hasattr(self, 'add_field_btn'):
            self.add_field_btn.config(state=disabled_state)

        # Contact info
        self.contact_name_entry.config(state=readonly_state)
        self.contact_email_entry.config(state=readonly_state)
        self.phone_entry.config(state=readonly_state)
        self.website_entry.config(state=readonly_state)

        # Address info
        self.address_line1_entry.config(state=readonly_state)
        self.address_line2_entry.config(state=readonly_state)
        self.city_entry.config(state=readonly_state)
        self.state_entry.config(state=readonly_state)
        self.postal_code_entry.config(state=readonly_state)
        self.country_entry.config(state=readonly_state)

        # Payment info
        self.payment_terms_entry.config(state=readonly_state)
        self.tax_id_entry.config(state=readonly_state)
        self.currency_combo.config(state=readonly_state)
        self.payment_method_combo.config(state=readonly_state)

        # Notes
        self.notes_text.config(state=tk.NORMAL if not self.readonly else tk.DISABLED)

        # Buttons
        if self.readonly:
            # Hide Save/Cancel, show Edit
            self.save_btn.pack_forget()
            self.cancel_btn.pack_forget()
            self.edit_btn.pack(side=tk.RIGHT, padx=5)
        else:
            # Hide Edit, show Save/Cancel
            if hasattr(self, 'edit_btn'):
                self.edit_btn.pack_forget()
            self.cancel_btn.pack(side=tk.RIGHT, padx=5)
            self.save_btn.pack(side=tk.RIGHT, padx=5)

    def add_custom_field(self, field_name=None, field_value=None):
        """Add a custom field to the supplier data."""
        if self.readonly:
            return

        # If no field name/value provided, show dialog to create
        if field_name is None:
            dialog = tk.Toplevel(self.dialog_frame)
            dialog.title("Add Custom Field")
            dialog.geometry("300x150")
            dialog.transient(self.dialog_frame)
            dialog.grab_set()

            # Create form
            form_frame = ttk.Frame(dialog, padding=10)
            form_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(form_frame, text="Field Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            name_var = tk.StringVar()
            ttk.Entry(form_frame, textvariable=name_var, width=20).grid(row=0, column=1, padx=5, pady=5,
                                                                        sticky=tk.W + tk.E)

            ttk.Label(form_frame, text="Field Value:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            value_var = tk.StringVar()
            ttk.Entry(form_frame, textvariable=value_var, width=20).grid(row=1, column=1, padx=5, pady=5,
                                                                         sticky=tk.W + tk.E)

            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            ttk.Button(
                button_frame,
                text="Add",
                command=lambda: self.on_add_field(name_var.get(), value_var.get(), dialog)
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            return

        # Create field frame
        field_frame = ttk.Frame(self.custom_fields_frame)
        field_frame.pack(fill=tk.X, pady=2, before=self.add_field_btn)

        # Create field label and entry
        ttk.Label(field_frame, text=f"{field_name}:").pack(side=tk.LEFT, padx=(0, 5))

        # Create string var for field value
        var = tk.StringVar(value=field_value if field_value else "")

        # Store var in custom fields dict
        self.custom_fields[field_name] = var

        # Create entry
        entry = ttk.Entry(field_frame, textvariable=var, width=30)
        entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Create delete button
        if not self.readonly:
            ttk.Button(
                field_frame,
                text="X",
                width=2,
                command=lambda f=field_frame, name=field_name: self.remove_custom_field(f, name)
            ).pack(side=tk.RIGHT, padx=(5, 0))

    def on_add_field(self, name, value, dialog):
        """Handle adding a custom field from dialog.

        Args:
            name: Field name
            value: Field value
            dialog: The dialog to close
        """
        if not name:
            messagebox.showerror("Error", "Field name is required.")
            return

        # Close dialog
        dialog.destroy()

        # Add field
        self.add_custom_field(name, value)

    def remove_custom_field(self, field_frame, field_name):
        """Remove a custom field.

        Args:
            field_frame: The field frame to remove
            field_name: The field name to remove from dictionary
        """
        # Remove from UI
        field_frame.destroy()

        # Remove from dictionary
        if field_name in self.custom_fields:
            del self.custom_fields[field_name]

    def add_date_to_notes(self):
        """Add current date to notes at cursor position."""
        if self.readonly:
            return

        current_date = datetime.now().strftime("%Y-%m-%d")
        self.notes_text.insert(tk.INSERT, current_date)

    def add_signature_to_notes(self):
        """Add user signature to notes at cursor position."""
        if self.readonly:
            return

        # Get current user from session or settings
        try:
            # This is a placeholder - implement actual username retrieval
            # in a real application
            username = "Current User"

            # Format signature
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            signature = f"\n-- {username} ({current_date})"

            # Insert at cursor position
            self.notes_text.insert(tk.INSERT, signature)

        except Exception as e:
            logger.error(f"Error adding signature: {e}")

    def on_view_purchase(self, event=None):
        """Handle viewing a purchase from history.

        Args:
            event: The event that triggered this action
        """
        # Get selected purchase
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a purchase first.")
            return

        # Get purchase ID
        values = self.history_tree.item(selection[0], "values")
        purchase_id = values[0]

        # Create view data
        view_data = {
            "purchase_id": purchase_id,
            "readonly": True
        }

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

        # Close this dialog
        self.close()

    def on_create_purchase(self):
        """Handle create new purchase button click."""
        # Create view data
        view_data = {
            "supplier_id": self.supplier_id,
            "supplier_name": self.name_var.get(),
            "create_new": True
        }

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

        # Close this dialog
        self.close()

    def on_export_history(self):
        """Handle export purchase history button click."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Export purchase history
            result = purchase_service.export_supplier_purchases(self.supplier_id)

            if result:
                messagebox.showinfo(
                    "Export Complete",
                    f"Purchase history has been exported successfully.\n\nFile: {result}"
                )
            else:
                messagebox.showerror("Error", "Failed to export purchase history.")

        except Exception as e:
            logger.error(f"Error exporting purchase history: {e}")
            messagebox.showerror("Error", f"Failed to export purchase history: {e}")

    def on_view_all_purchases(self):
        """Handle view all purchases button click."""
        # Create view data
        view_data = {
            "filter_supplier_id": self.supplier_id,
            "filter_supplier_name": self.name_var.get()
        }

        # Navigate to purchase view
        self.master.show_view("purchase_view", view_data=view_data)

        # Close this dialog
        self.close()

    def on_edit(self):
        """Handle edit button click from read-only mode."""
        # Switch to edit mode
        self.readonly = False

        # Update UI state
        self.update_ui_state()

    def on_save(self):
        """Handle save button click."""
        # Validate form
        if not self.validate_form():
            return

        # Collect form data
        data = self.collect_form_data()

        try:
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            if self.create_new:
                # Create new supplier
                result = supplier_service.create_supplier(data)

                if result:
                    messagebox.showinfo("Success", "Supplier created successfully.")

                    # Publish event
                    publish("supplier_created", {"supplier_id": result})

                    # Close dialog
                    self.result = True
                    self.close()
                else:
                    messagebox.showerror("Error", "Failed to create supplier.")
            else:
                # Update existing supplier
                result = supplier_service.update_supplier(self.supplier_id, data)

                if result:
                    messagebox.showinfo("Success", "Supplier updated successfully.")

                    # Publish event
                    publish("supplier_updated", {"supplier_id": self.supplier_id})

                    # Close dialog
                    self.result = True
                    self.close()
                else:
                    messagebox.showerror("Error", "Failed to update supplier.")

        except Exception as e:
            logger.error(f"Error saving supplier: {e}")
            messagebox.showerror("Error", f"Failed to save supplier: {e}")

    def validate_form(self):
        """Validate the form data.

        Returns:
            True if the form is valid, False otherwise
        """
        # Check required fields
        if not self.name_var.get():
            messagebox.showerror("Validation Error", "Supplier name is required.")
            return False

        # Validate email format
        email = self.contact_email_var.get()
        if email and '@' not in email:
            messagebox.showerror("Validation Error", "Invalid email format.")
            return False

        # Validate date format
        active_since = self.active_since_var.get()
        if active_since:
            try:
                datetime.strptime(active_since, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
                return False

        return True

    def collect_form_data(self):
        """Collect form data into a dictionary.

        Returns:
            Dictionary of form data
        """
        # Basic info
        data = {
            'name': self.name_var.get(),
            'status': self.status_var.get(),
            'active_since': self.active_since_var.get(),

            # Contact info
            'contact_name': self.contact_name_var.get(),
            'contact_email': self.contact_email_var.get(),
            'phone': self.phone_var.get(),
            'website': self.website_var.get(),

            # Address info
            'address': {
                'line1': self.address_line1_var.get(),
                'line2': self.address_line2_var.get(),
                'city': self.city_var.get(),
                'state': self.state_var.get(),
                'postal_code': self.postal_code_var.get(),
                'country': self.country_var.get()
            },

            # Payment info
            'payment_info': {
                'terms': self.payment_terms_var.get(),
                'tax_id': self.tax_id_var.get(),
                'currency': self.currency_var.get(),
                'preferred_method': self.preferred_payment_method_var.get()
            },

            # Notes
            'notes': self.notes_text.get('1.0', tk.END).strip(),

            # Custom fields
            'custom_fields': {field: var.get() for field, var in self.custom_fields.items()}
        }

        return data

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        if self.readonly:
            return

        # Create date picker dialog
        dialog = tk.Toplevel(self.dialog_frame)
        dialog.title("Select Date")
        dialog.geometry("300x250")
        dialog.resizable(False, False)
        dialog.transient(self.dialog_frame)
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

    def update_calendar(self, frame, label, year, month, date_var, dialog):
        """Update the calendar display based on selected month and year.

        Args:
            frame: Calendar frame
            label: Month/year label
            year: Year to display
            month: Month to display
            date_var: Variable to update with selected date
            dialog: Dialog to close on selection
        """
        # Update month/year label
        month_name = datetime(year, month, 1).strftime('%B')
        label.config(text=f"{month_name} {year}")

        # Clear existing calendar buttons
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.destroy()

        # Calculate first day of month (0 = Monday, 6 = Sunday)
        first_day = datetime(year, month, 1).weekday()

        # Get number of days in month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        days_in_month = last_day.day

        # Create calendar buttons
        day = 1
        for row in range(1, 7):  # 6 weeks max
            if day > days_in_month:
                break

            for col in range(7):  # 7 days per week
                if row == 1 and col < first_day:
                    # Empty cell before first day
                    continue

                if day > days_in_month:
                    # Break if we've reached the end of the month
                    break

                # Create button for day
                btn = tk.Button(
                    frame,
                    text=str(day),
                    width=3,
                    height=1,
                    command=lambda d=day: self.select_day(d, year, month, date_var, dialog)
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

                day += 1

    def select_day(self, day, year, month, date_var, dialog):
        """Select a day in the calendar.

        Args:
            day: The day number to select
            year: The year
            month: The month
            date_var: The variable to update
            dialog: The dialog to close
        """
        # Format selected date
        selected_date = datetime(year, month, day).strftime("%Y-%m-%d")

        # Update variable
        date_var.set(selected_date)

        # Close dialog
        dialog.destroy()

    def prev_month(self, label, frame):
        """Go to previous month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month/year
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1

        # Update calendar
        self.update_calendar(frame, label, self.cal_year, self.cal_month, None, None)

    def next_month(self, label, frame):
        """Go to next month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month/year
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1

        # Update calendar
        self.update_calendar(frame, label, self.cal_year, self.cal_month, None, None)