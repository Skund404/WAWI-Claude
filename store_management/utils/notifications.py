

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class NotificationType(Enum):
    pass
INFO = 'info'
SUCCESS = 'success'
WARNING = 'warning'
ERROR = 'error'


class StatusNotification:
    pass
"""Status notification manager"""

@inject(MaterialService)
def __init__(self, parent: tk.Widget):
    pass
self.parent = parent
self.notification_queue = Queue()
self.current_notification = None
self.notification_thread = None
self.is_running = True
self.frame = ttk.Frame(parent)
self.frame.pack(fill=tk.X, side=tk.BOTTOM)
self.status_label = ttk.Label(self.frame, text='')
self.status_label.pack(side=tk.LEFT, padx=5)
self.progress = ttk.Progressbar(self.frame, mode='indeterminate',
length=100)
self.setup_styles()
self.start_processor()

@inject(MaterialService)
def setup_styles(self):
    pass
"""Setup notification styles"""
style = ttk.Style()
style.configure('Info.TLabel', foreground='black', background='#e3f2fd'
)
style.configure('Success.TLabel', foreground='dark green',
background='#e8f5e9')
style.configure('Warning.TLabel', foreground='dark orange',
background='#fff3e0')
style.configure('Error.TLabel', foreground='dark red',
background='#ffebee')

@inject(MaterialService)
def start_processor(self):
    pass
"""Start notification processing thread"""
self.notification_thread = threading.Thread(target=self.
_process_notifications, daemon=True)
self.notification_thread.start()

@inject(MaterialService)
def _process_notifications(self):
    pass
"""Process notifications from queue"""
while self.is_running:
    pass
if not self.notification_queue.empty():
    pass
notification = self.notification_queue.get()
self.parent.after(0, lambda: self._show_notification(
notification))
time.sleep(0.1)

@inject(MaterialService)
def _show_notification(self, notification: dict):
    pass
"""Show notification"""
try:
    pass
message = notification['message']
ntype = notification['type']
duration = notification.get('duration', 3000)
progress = notification.get('progress', False)
callback = notification.get('callback')
self.status_label.configure(
style=f'{ntype.value.title()}.TLabel', text=message)
if progress:
    pass
self.progress.pack(side=tk.RIGHT, padx=5)
self.progress.start()
else:
self.progress.stop()
self.progress.pack_forget()
if duration > 0:
    pass
self.parent.after(duration, lambda: self.
_clear_notification(callback))
except Exception as e:
    pass
print(f'Error showing notification: {e}')

@inject(MaterialService)
def _clear_notification(self, callback: Optional[Callable] = None):
    pass
"""Clear current notification"""
self.status_label.configure(text='', style='TLabel')
self.progress.stop()
self.progress.pack_forget()
if callback:
    pass
callback()

@inject(MaterialService)
def show_info(self, message: str, duration: int = 3000):
    pass
"""Show info notification"""
self.notification_queue.put({'type': NotificationType.INFO,
'message': message, 'duration': duration})

@inject(MaterialService)
def show_success(self, message: str, duration: int = 3000):
    pass
"""Show success notification"""
self.notification_queue.put({'type': NotificationType.SUCCESS,
'message': message, 'duration': duration})

@inject(MaterialService)
def show_warning(self, message: str, duration: int = 3000):
    pass
"""Show warning notification"""
self.notification_queue.put({'type': NotificationType.WARNING,
'message': message, 'duration': duration})

@inject(MaterialService)
def show_error(self, message: str, duration: int = 5000):
    pass
"""Show error notification"""
self.notification_queue.put({'type': NotificationType.ERROR,
'message': message, 'duration': duration})

@inject(MaterialService)
def show_progress(self, message: str, callback: Optional[Callable] = None):
    pass
"""Show progress notification"""
self.notification_queue.put({'type': NotificationType.INFO,
'message': message, 'progress': True, 'duration': 0, 'callback':
callback})

@inject(MaterialService)
def clear(self):
    pass
"""Clear current notification"""
self._clear_notification()

@inject(MaterialService)
def cleanup(self):
    pass
"""Cleanup resources"""
self.is_running = False
if self.notification_thread and self.notification_thread.is_alive():
    pass
self.notification_thread.join(timeout=1.0)
