from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Quick fix for the storage view to debug data loading issues.
"""
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(
level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("storage_view_fix")


def manually_load_storage_view():
    pass
"""
Manually create and load the storage view to debug issues.
"""
from database.session import get_db_session
from database.models.storage import Storage
from application import Application

logger.info("Starting manual storage view loading")
app = Application()
root = tk.Tk()
root.title("Storage View Debug")
root.geometry("800x600")
frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)
columns = ("id", "name", "location", "capacity",
"occupancy", "type", "status")
tree = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    pass
tree.heading(col, text=col.capitalize())
tree.column(col, width=100)
vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
hsb.pack(side=tk.BOTTOM, fill=tk.X)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
try:
    pass
session = get_db_session()
storage_locations = session.query(Storage).all()
logger.info(f"Found {len(storage_locations)} storage locations")
for storage in storage_locations:
    pass
tree.insert(
"",
tk.END,
values=(
storage.id,
storage.name,
storage.location,
storage.capacity,
storage.current_occupancy,
storage.type,
storage.status,
),
)
button_frame = ttk.Frame(root)
button_frame.pack(fill=tk.X, pady=5)

def refresh_data():
    pass
for item in tree.get_children():
    pass
tree.delete(item)
session = get_db_session()
storage_locations = session.query(Storage).all()
logger.info(
f"Refreshed: Found {len(storage_locations)} storage locations")
for storage in storage_locations:
    pass
tree.insert(
"",
tk.END,
values=(
storage.id,
storage.name,
storage.location,
storage.capacity,
storage.current_occupancy,
storage.type,
storage.status,
),
)
session.close()

refresh_btn = ttk.Button(
button_frame, text="Refresh", command=refresh_data)
refresh_btn.pack(side=tk.LEFT, padx=5)
close_btn = ttk.Button(
button_frame, text="Close", command=root.destroy)
close_btn.pack(side=tk.RIGHT, padx=5)
logger.info("Starting main loop")
root.mainloop()
except Exception as e:
    pass
logger.error(f"Error loading storage data: {str(e)}", exc_info=True)
finally:
if "session" in locals():
    pass
session.close()


if __name__ == "__main__":
    pass
manually_load_storage_view()
