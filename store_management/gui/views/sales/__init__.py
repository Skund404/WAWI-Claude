# gui/views/sales/__init__.py
"""
Sales and Customer Management module.

This module contains views for managing customers and sales,
including customer listings, sales records, invoicing, and payment processing.
"""

from gui.views.sales.customer_view import CustomerView
from gui.views.sales.customer_details_dialog import CustomerDetailsDialog
from gui.views.sales.sales_view import SalesView
from gui.views.sales.sales_details_view import SalesDetailsView
from gui.views.sales.sales_item_dialog import SalesItemDialog
from gui.views.sales.invoice_generator import InvoiceGenerator