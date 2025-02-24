

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class SupplierView(ttk.Frame):

    pass
@inject(MaterialService)
def handle_return(self, event=None):
    pass
"""Handle Return key press"""
pass

@inject(MaterialService)
def handle_escape(self, event=None):
    pass
"""Handle Escape key press"""
pass

@inject(MaterialService)
def show_search_dialog(self):
    pass
"""Open dialog to search suppliers"""
try:
    pass
search_dialog = tk.Toplevel(self)
search_dialog.title('Search Suppliers')
search_dialog.geometry('400x300')
search_fields = ['company_name', 'contact_person',
'email_address', 'phone_number']
entry_widgets = {}
for i, field in enumerate(search_fields):
    pass
label = ttk.Label(search_dialog, text=field.replace('_',
' ').title())
label.grid(row=i, column=0, padx=5, pady=5, sticky='w')
entry = ttk.Entry(search_dialog, width=30)
entry.grid(row=i, column=1, padx=5, pady=5)
entry_widgets[field] = entry

def perform_search():
    pass
try:
    pass
conditions = []
params = []
for field, widget in entry_widgets.items():
    pass
value = widget.get().strip()
if value:
    pass
conditions.append(f'{field} LIKE ?')
params.append(f'%{value}%')
if not conditions:
    pass
messagebox.showinfo('Search',
'Please enter at least one search term')
return
self.db.connect()
query = f"SELECT * FROM {TABLES['SUPPLIER']}"
if conditions:
    pass
query += ' WHERE ' + ' AND '.join(conditions)
results = self.db.execute_query(query, tuple(params))
for item in self.tree.get_children():
    pass
self.tree.delete(item)
for row in results:
    pass
self.tree.insert('', 'end', values=row)
search_dialog.destroy()
if not results:
    pass
messagebox.showinfo('Search',
'No matching suppliers found')
except Exception as e:
    pass
error_msg = 'Search failed'
log_error(e, error_msg)
ErrorHandler.show_error('Search Error', error_msg, e)
finally:
self.db.disconnect()
button_frame = ttk.Frame(search_dialog)
button_frame.grid(row=len(search_fields),
column=0, columnspan=2, pady=10)
ttk.Button(button_frame, text='Search', command=perform_search
).pack(side=tk.LEFT, padx=5)
ttk.Button(button_frame, text='Cancel', command=search_dialog.
destroy).pack(side=tk.LEFT, padx=5)
except Exception as e:
    pass
error_msg = 'Failed to create search dialog'
log_error(e, error_msg)
ErrorHandler.show_error('Dialog Error', error_msg, e)

@inject(MaterialService)
def show_filter_dialog(self):
    pass
"""Open dialog to filter suppliers"""
try:
    pass
filter_dialog = tk.Toplevel(self)
filter_dialog.title('Filter Suppliers')
filter_dialog.geometry('400x400')
filter_options = {'business_type': ['All', 'Manufacturer',
'Wholesaler', 'Distributor', 'Retailer'], 'payment_terms':
['All', 'Net 30', 'Net 60', 'Net 90', 'Prepaid'], 'country':
['All']}
try:
    pass
self.db.connect()
query = (
f"SELECT DISTINCT country FROM {TABLES['SUPPLIER']} WHERE country IS NOT NULL"
)
countries = self.db.execute_query(query)
if countries:
    pass
filter_options['country'].extend([country[0] for
country in countries])
except Exception as e:
    pass
logger.error(f'Failed to fetch countries: {e}')
finally:
self.db.disconnect()
filter_widgets = {}
row = 0
for field, options in filter_options.items():
    pass
label = ttk.Label(filter_dialog, text=field.replace('_',
' ').title())
label.grid(row=row, column=0, padx=5, pady=5, sticky='w')
combo = ttk.Combobox(
filter_dialog, values=options, state='readonly', width=30)
combo.set('All')
combo.grid(row=row, column=1, padx=5, pady=5)
filter_widgets[field] = combo
row += 1

def apply_filters():
    pass
try:
    pass
criteria = {}
for field, widget in filter_widgets.items():
    pass
value = widget.get()
if value and value != 'All':
    pass
criteria[field] = value
query = f"SELECT * FROM {TABLES['SUPPLIER']}"
params = []
if criteria:
    pass
conditions = []
for field, value in criteria.items():
    pass
conditions.append(f'{field} = ?')
params.append(value)
query += ' WHERE ' + ' AND '.join(conditions)
self.db.connect()
results = self.db.execute_query(query, tuple(params))
for item in self.tree.get_children():
    pass
self.tree.delete(item)
for row in results:
    pass
self.tree.insert('', 'end', values=row)
filter_dialog.destroy()
if not results:
    pass
messagebox.showinfo('Filter',
'No suppliers match the selected criteria')
except Exception as e:
    pass
error_msg = 'Filter operation failed'
log_error(e, error_msg)
ErrorHandler.show_error('Filter Error', error_msg, e)
finally:
self.db.disconnect()

def reset_filters():
    pass
try:
    pass
for widget in filter_widgets.values():
    pass
widget.set('All')
self.load_data()
except Exception as e:
    pass
error_msg = 'Failed to reset filters'
log_error(e, error_msg)
ErrorHandler.show_error('Reset Error', error_msg, e)
button_frame = ttk.Frame(filter_dialog)
button_frame.grid(row=row, column=0, columnspan=2, pady=10)
ttk.Button(button_frame, text='Apply', command=apply_filters).pack(
side=tk.LEFT, padx=5)
ttk.Button(button_frame, text='Reset', command=reset_filters).pack(
side=tk.LEFT, padx=5)
ttk.Button(button_frame, text='Cancel', command=filter_dialog.
destroy).pack(side=tk.LEFT, padx=5)
except Exception as e:
    pass
error_msg = 'Failed to create filter dialog'
log_error(e, error_msg)
ErrorHandler.show_error('Dialog Error', error_msg, e)

@check_database_connection
@inject(MaterialService)
def save_table(self):
    pass
"""Save the current table data to a file"""
try:
    pass
file_path = filedialog.asksaveasfilename(defaultextension=
'.csv', filetypes=[('CSV files', '*.csv'), ('Excel files',
'*.xlsx'), ('All files', '*.*')])
if not file_path:
    pass
return
data = [self.columns]
for item in self.tree.get_children():
    pass
data.append(self.tree.item(item)['values'])
if file_path.endswith('.csv'):
    pass
with open(file_path, 'w', newline='', encoding='utf-8') as f:
    pass
writer = csv.writer(f)
writer.writerows(data)
elif file_path.endswith('.xlsx'):
    pass
df = pd.DataFrame(data[1:], columns=data[0])
df.to_excel(file_path, index=False)
logger.info(f'Table saved to: {file_path}')
messagebox.showinfo('Success', 'Table saved successfully')
except Exception as e:
    pass
error_msg = 'Failed to save table'
log_error(e, error_msg)
ErrorHandler.show_error('Save Error', error_msg, e)

@inject(MaterialService)
def __init__(self, parent):
    pass
try:
    pass
super().__init__(parent)
self.db = DatabaseManager(get_database_path())
self.field_mapping = {'Company Name': 'company_name',
'Contact Person': 'contact_person', 'Phone Number':
'phone_number', 'Email Address': 'email_address', 'Website':
'website', 'Street Address': 'street_address', 'City':
'city', 'State/Province': 'state_province', 'Postal Code':
'postal_code', 'Country': 'country', 'Tax ID': 'tax_id',
'Business Type': 'business_type', 'Payment Terms':
'payment_terms', 'Currency': 'currency', 'Bank Details':
'bank_details', 'Products Offered': 'products_offered',
'Lead Time': 'lead_time', 'Last Order Date':
'last_order_date', 'Notes': 'notes'}
self.reverse_mapping = {v: k for k, v in self.field_mapping.items()
}
self.db.connect()
self.undo_stack = []
self.redo_stack = []
self.setup_toolbar()
self.setup_table()
self.load_data()
logger.info('SupplierView initialized successfully')
except Exception as init_error:
    pass
logger.error(f'Supplier View Initialization Error: {init_error}')
ErrorHandler.show_error('Initialization Error',
'Failed to initialize Supplier View', init_error)
raise

@inject(MaterialService)
def setup_toolbar(self):
    pass
"""Create the toolbar with all buttons"""
toolbar = ttk.Frame(self)
toolbar.pack(fill=tk.X, padx=5, pady=5)
left_frame = ttk.Frame(toolbar)
left_frame.pack(side=tk.LEFT, fill=tk.X)
ttk.Button(left_frame, text='ADD', command=self.show_add_dialog).pack(
side=tk.LEFT, padx=2)
ttk.Button(left_frame, text='Search', command=self.show_search_dialog
).pack(side=tk.LEFT, padx=2)
ttk.Button(left_frame, text='Filter', command=self.show_filter_dialog
).pack(side=tk.LEFT, padx=2)
right_frame = ttk.Frame(toolbar)
right_frame.pack(side=tk.RIGHT, fill=tk.X)
ttk.Button(right_frame, text='Save', command=self.save_table).pack(side
=tk.RIGHT, padx=2)
ttk.Button(right_frame, text='Load', command=self.load_table).pack(side
=tk.RIGHT, padx=2)
ttk.Button(right_frame, text='Undo', command=self.undo).pack(side=
tk.RIGHT, padx=2)
ttk.Button(right_frame, text='Redo', command=self.redo).pack(side=
tk.RIGHT, padx=2)
ttk.Button(right_frame, text='Reset View', command=self.reset_view
).pack(side=tk.RIGHT, padx=2)

@inject(MaterialService)
def setup_table(self):
    pass
"""Create the main table view"""
table_frame = ttk.Frame(self)
table_frame.pack(expand=True, fill='both', padx=5, pady=5)
self.columns = list(self.field_mapping.keys())
vsb = ttk.Scrollbar(table_frame, orient='vertical')
hsb = ttk.Scrollbar(table_frame, orient='horizontal')
self.tree = ttk.Treeview(table_frame, columns=self.columns, show=
'headings', selectmode='extended', yscrollcommand=vsb.set,
xscrollcommand=hsb.set)
vsb.configure(command=self.tree.yview)
hsb.configure(command=self.tree.xview)
for col in self.columns:
    pass
self.tree.heading(col, text=col, command=lambda c=col: self.
sort_column(c))
if col in ['Notes', 'Products Offered', 'Bank Details']:
    pass
width = 200
elif col in ['Street Address', 'Email Address', 'Website']:
    pass
width = 150
else:
width = 100
self.tree.column(col, width=width, minwidth=50)
self.tree.grid(row=0, column=0, sticky='nsew')
vsb.grid(row=0, column=1, sticky='ns')
hsb.grid(row=1, column=0, sticky='ew')
table_frame.grid_columnconfigure(0, weight=1)
table_frame.grid_rowconfigure(0, weight=1)
self.tree.bind('<Double-1>', self.on_double_click)
self.tree.bind('<Delete>', self.delete_selected)

@check_database_connection
@inject(MaterialService)
def load_data(self):
    pass
"""Load supplier data from the database and populate the treeview"""
try:
    pass
logger.debug('Loading supplier data')
if not self.db or not self.db.conn:
    pass
self.db.connect()
if not self.db.table_exists(TABLES['SUPPLIER']):
    pass
raise DatabaseError(
f"Table {TABLES['SUPPLIER']} does not exist")
query = f"SELECT * FROM {TABLES['SUPPLIER']}"
results = self.db.execute_query(query)
for item in self.tree.get_children():
    pass
self.tree.delete(item)
if results:
    pass
for row in results:
    pass
self.tree.insert('', 'end', values=row)
logger.info(f'Loaded {len(results)} suppliers')
else:
logger.info('No suppliers found in database')
except Exception as e:
    pass
error_msg = f'Failed to load supplier data: {str(e)}'
logger.error(error_msg)
ErrorHandler.show_error('Load Error', error_msg, e)
raise

@inject(MaterialService)
def load_table(self):
    pass
"""Alias for load_data method"""
self.load_data()

@inject(MaterialService)
def reset_view(self):
    pass
"""Reset the view to show all suppliers"""
try:
    pass
logger.debug('Resetting view')
self.load_data()
logger.info('View reset successfully')
except Exception as e:
    pass
error_msg = 'Failed to reset view'
log_error(e, error_msg)
ErrorHandler.show_error('Reset Error', error_msg, e)

@inject(MaterialService)
def show_add_dialog(self):
    pass
"""Open dialog to add a new supplier"""
try:
    pass
add_dialog = tk.Toplevel(self)
add_dialog.title('Add New Supplier')
add_dialog.geometry('400x600')
canvas = tk.Canvas(add_dialog)
scrollbar = ttk.Scrollbar(add_dialog, orient='vertical',
command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)
scrollable_frame.bind('<Configure>', lambda e: canvas.configure
(scrollregion=canvas.bbox('all')))
canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
canvas.configure(yscrollcommand=scrollbar.set)
field_mapping = {'Company Name': 'company_name',
'Contact Person': 'contact_person', 'Phone Number':
'phone_number', 'Email Address': 'email_address', 'Website':
'website', 'Street Address': 'street_address', 'City':
'city', 'State/Province': 'state_province', 'Postal Code':
'postal_code', 'Country': 'country', 'Tax ID': 'tax_id',
'Business Type': 'business_type', 'Payment Terms':
'payment_terms', 'Currency': 'currency', 'Bank Details':
'bank_details', 'Products Offered': 'products_offered',
'Lead Time': 'lead_time', 'Last Order Date':
'last_order_date', 'Notes': 'notes'}
entry_widgets = {}
for i, (display_name, db_field) in enumerate(field_mapping.items()
):
label = ttk.Label(scrollable_frame, text=display_name)
label.grid(row=i, column=0, padx=5, pady=5, sticky='w')
entry = ttk.Entry(scrollable_frame, width=40)
entry.grid(row=i, column=1, padx=5, pady=5)
entry_widgets[db_field] = entry

def save_supplier():
    pass
try:
    pass
data = {field: widget.get().strip() for field, widget in
entry_widgets.items()}
if not data['company_name']:
    pass
messagebox.showerror('Error',
'Company Name is required')
return
self.db.connect()
if self.db.insert_record(TABLES['SUPPLIER'], data):
    pass
self.undo_stack.append(('add', data))
self.redo_stack.clear()
self.load_data()
add_dialog.destroy()
messagebox.showinfo('Success',
'Supplier added successfully')
else:
raise DatabaseError('Failed to add supplier')
except Exception as e:
    pass
error_msg = f'Failed to add supplier: {str(e)}'
log_error(e, error_msg)
ErrorHandler.show_error('Add Error', error_msg, e)
finally:
self.db.disconnect()
button_frame = ttk.Frame(scrollable_frame)
button_frame.grid(row=len(field_mapping), column=0, columnspan=
2, pady=10)
ttk.Button(button_frame, text='Save', command=save_supplier).pack(
side=tk.LEFT, padx=5)
ttk.Button(button_frame, text='Cancel', command=add_dialog.destroy
).pack(side=tk.LEFT, padx=5)
canvas.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')
except Exception as e:
    pass
error_msg = 'Failed to create add dialog'
log_error(e, error_msg)
ErrorHandler.show_error('Dialog Error', error_msg, e)

@check_database_connection
@inject(MaterialService)
def delete_selected(self, event=None):
    pass
"""Delete selected supplier(s)"""
try:
    pass
selected_items = self.tree.selection()
if not selected_items:
    pass
logger.debug('No items selected for deletion')
messagebox.showinfo('Delete', 'No suppliers selected')
return
if not messagebox.askyesno('Confirm Delete',
f'Are you sure you want to delete {len(selected_items)} supplier(s)?'
):
return
logger.debug(
f'Attempting to delete {len(selected_items)} suppliers')
deleted_items = []
self.db.begin_transaction()
try:
    pass
for item in selected_items:
    pass
values = self.tree.item(item)['values']
if self.db.delete_record(TABLES['SUPPLIER'],
'company_name = ?', (values[0],)):
deleted_items.append((item, values))
self.tree.delete(item)
self.db.commit_transaction()
self.undo_stack.append(('delete', deleted_items))
self.redo_stack.clear()
logger.info(
f'Successfully deleted {len(deleted_items)} suppliers')
messagebox.showinfo('Success',
f'{len(deleted_items)} supplier(s) deleted')
except Exception as e:
    pass
self.db.rollback_transaction()
raise e
except Exception as e:
    pass
error_msg = 'Failed to delete suppliers'
log_error(e, error_msg)
ErrorHandler.show_error('Delete Error', error_msg, e)

@inject(MaterialService)
def on_double_click(self, event):
    pass
"""Handle double-click event for editing"""
try:
    pass
selected_item = self.tree.selection()
if not selected_item:
    pass
return
item = selected_item[0]
column = self.tree.identify_column(event.x)
column_id = int(column[1]) - 1
if column_id >= 0 and column_id < len(self.columns):
    pass
self.start_cell_edit(item, self.columns[column_id])
except Exception as e:
    pass
error_msg = 'Failed to handle double-click'
log_error(e, error_msg)
ErrorHandler.show_error('Edit Error', error_msg, e)

@inject(MaterialService)
def start_cell_edit(self, item, column):
    pass
"""Start editing a cell"""
try:
    pass
current_value = self.tree.set(item, column)
edit_dialog = tk.Toplevel(self)
edit_dialog.title(f'Edit {column}')
x, y, _, _ = self.tree.bbox(item, column)
edit_dialog.geometry(
f'+{x + self.winfo_rootx()}+{y + self.winfo_rooty()}')
entry = ttk.Entry(edit_dialog)
entry.insert(0, current_value)
entry.pack(padx=5, pady=5)
entry.focus_set()

def save_edit(event=None):
    pass
try:
    pass
new_value = entry.get()
if new_value != current_value:
    pass
db_column = self.field_mapping[column]
self.db.connect()
data = {db_column: new_value}
company_name = self.tree.item(item)['values'][0]
if self.db.update_record(TABLES['SUPPLIER'], data,
'company_name = ?', (company_name,)):
self.tree.set(item, column, new_value)
self.undo_stack.append(('edit', item, column,
current_value, new_value))
self.redo_stack.clear()
edit_dialog.destroy()
except Exception as e:
    pass
error_msg = 'Failed to save edit'
log_error(e, error_msg)
ErrorHandler.show_error('Edit Error', error_msg, e)
finally:
self.db.disconnect()

def cancel_edit(event=None):
    pass
edit_dialog.destroy()
entry.bind('<Return>', save_edit)
entry.bind('<Escape>', cancel_edit)
button_frame = ttk.Frame(edit_dialog)
button_frame.pack(fill=tk.X, padx=5, pady=5)
ttk.Button(button_frame, text='Save', command=save_edit).pack(side
=tk.LEFT, padx=5)
ttk.Button(button_frame, text='Cancel', command=cancel_edit).pack(
side=tk.LEFT, padx=5)
except Exception as e:
    pass
error_msg = 'Failed to start cell edit'
log_error(e, error_msg)
ErrorHandler.show_error('Edit Error', error_msg, e)

@inject(MaterialService)
def undo(self):
    pass
"""Undo last action"""
try:
    pass
if not self.undo_stack:
    pass
return
action = self.undo_stack.pop()
action_type = action[0]
self.db.connect()
if action_type == 'edit':
    pass
item, column, old_value, new_value = action[1:]
data = {column: old_value}
if self.db.update_record(TABLES['SUPPLIER'], data,
'company_name = ?', (self.tree.item(item)['values'][0],)):
self.tree.set(item, column, old_value)
self.redo_stack.append(('edit', item, column, old_value,
new_value))
elif action_type == 'delete':
    pass
deleted_items = action[1]
restored_items = []
for item, values in deleted_items:
    pass
data = dict(zip(self.columns, values))
if self.db.insert_record(TABLES['SUPPLIER'], data):
    pass
new_item = self.tree.insert('', 'end', values=values)
restored_items.append((new_item, values))
self.redo_stack.append(('undelete', restored_items))
elif action_type == 'add':
    pass
company_name = action[1]['company_name']
if self.db.delete_record(TABLES['SUPPLIER'],
'company_name = ?', (company_name,)):
for item in self.tree.get_children():
    pass
if self.tree.item(item)['values'][0] == company_name:
    pass
self.tree.delete(item)
break
self.redo_stack.append(('readd', action[1]))
except Exception as e:
    pass
error_msg = 'Failed to undo action'
log_error(e, error_msg)
ErrorHandler.show_error('Undo Error', error_msg, e)
finally:
self.db.disconnect()

@inject(MaterialService)
def redo(self):
    pass
"""Redo last undone action"""
try:
    pass
if not self.redo_stack:
    pass
return
action = self.redo_stack.pop()
action_type = action[0]
self.db.connect()
if action_type == 'edit':
    pass
item, column, old_value, new_value = action[1:]
data = {column: new_value}
if self.db.update_record(TABLES['SUPPLIER'], data,
'company_name = ?', (self.tree.item(item)['values'][0],)):
self.tree.set(item, column, new_value)
self.undo_stack.append(('edit', item, column, old_value,
new_value))
elif action_type == 'undelete':
    pass
restored_items = action[1]
deleted_items = []
for item, values in restored_items:
    pass
if self.db.delete_record(TABLES['SUPPLIER'],
'company_name = ?', (values[0],)):
self.tree.delete(item)
deleted_items.append((item, values))
self.undo_stack.append(('delete', deleted_items))
elif action_type == 'readd':
    pass
data = action[1]
if self.db.insert_record(TABLES['SUPPLIER'], data):
    pass
values = [data[col] for col in self.columns]
self.tree.insert('', 'end', values=values)
self.undo_stack.append(('add', data))
except Exception as e:
    pass
error_msg = 'Failed to redo action'
log_error(e, error_msg)
ErrorHandler.show_error('Redo Error', error_msg, e)
finally:
self.db.disconnect()

@inject(MaterialService)
def sort_column(self, column):
    pass
"""Sort tree contents when a column header is clicked"""
try:
    pass
logger.debug(f'Sorting by column: {column}')
items = [(self.tree.set(item, column), item) for item in self.
tree.get_children('')]
items.sort(reverse=getattr(self, '_sort_reverse', False))
for index, (_, item) in enumerate(items):
    pass
self.tree.move(item, '', index)
self._sort_reverse = not getattr(self, '_sort_reverse', False)
for col in self.columns:
    pass
if col == column:
    pass
indicator = '▼' if self._sort_reverse else '▲'
self.tree.heading(col, text=
f"{col.replace('_', ' ').title()} {indicator}")
else:
self.tree.heading(col, text=col.replace('_', ' ').title())
except Exception as e:
    pass
error_msg = f'Failed to sort column: {column}'
log_error(e, error_msg)
ErrorHandler.show_error('Sort Error', error_msg, e)
