# utils/notifications.py
import time
import tkinter as tk
import threading
from enum import Enum
from queue import Queue
from tkinter import ttk
from typing import Optional, Callable, Dict, Any


class NotificationType(Enum):
    """
    Enum defining types of notifications with their corresponding value.

    Each notification type maps to a specific visual style and behavior.
    """
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'


class StatusNotification:
    """
    Status notification manager for displaying user notifications.

    This class provides a UI component for showing various types of notifications
    with support for queuing, progress indicators, and callbacks.
    """

    def __init__(self, parent: tk.Widget):
        """
        Initialize the status notification manager.

        Args:
            parent: Parent tkinter widget
        """
        self.parent = parent
        self.notification_queue = Queue()
        self.current_notification = None
        self.notification_thread = None
        self.is_running = True

        # Create UI components
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ttk.Label(self.frame, text='')
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(self.frame, mode='indeterminate', length=100)

        # Setup and start
        self.setup_styles()
        self.start_processor()

    def setup_styles(self):
        """
        Setup notification styles using ttk.Style.

        Configures different visual styles for each notification type.
        """
        style = ttk.Style()
        style.configure('Info.TLabel', foreground='black', background='#e3f2fd')
        style.configure('Success.TLabel', foreground='dark green', background='#e8f5e9')
        style.configure('Warning.TLabel', foreground='dark orange', background='#fff3e0')
        style.configure('Error.TLabel', foreground='dark red', background='#ffebee')

    def start_processor(self):
        """
        Start notification processing thread.

        Creates and starts a daemon thread to process notifications from the queue.
        """
        self.notification_thread = threading.Thread(target=self._process_notifications, daemon=True)
        self.notification_thread.start()

    def _process_notifications(self):
        """
        Process notifications from queue.

        Continuously monitors the queue and displays notifications as they arrive.
        """
        while self.is_running:
            if not self.notification_queue.empty():
                notification = self.notification_queue.get()
                self.parent.after(0, lambda: self._show_notification(notification))
            time.sleep(0.1)

    def _show_notification(self, notification: dict):
        """
        Show notification in the UI.

        Args:
            notification: Dictionary containing notification details
        """
        try:
            message = notification['message']
            ntype = notification['type']
            duration = notification.get('duration', 3000)
            progress = notification.get('progress', False)
            callback = notification.get('callback')

            # Configure label with appropriate style and message
            self.status_label.configure(style=f'{ntype.value.title()}.TLabel', text=message)

            # Show or hide progress bar
            if progress:
                self.progress.pack(side=tk.RIGHT, padx=5)
                self.progress.start()
            else:
                self.progress.stop()
                self.progress.pack_forget()

            # Auto-clear notification after duration if set
            if duration > 0:
                self.parent.after(duration, lambda: self._clear_notification(callback))

        except Exception as e:
            print(f'Error showing notification: {e}')

    def _clear_notification(self, callback: Optional[Callable] = None):
        """
        Clear current notification.

        Args:
            callback: Optional function to call after clearing
        """
        self.status_label.configure(text='', style='TLabel')
        self.progress.stop()
        self.progress.pack_forget()

        if callback:
            callback()

    def show_info(self, message: str, duration: int = 3000):
        """
        Show info notification.

        Args:
            message: Text to display
            duration: How long to show the notification (ms)
        """
        self.notification_queue.put({
            'type': NotificationType.INFO,
            'message': message,
            'duration': duration
        })

    def show_success(self, message: str, duration: int = 3000):
        """
        Show success notification.

        Args:
            message: Text to display
            duration: How long to show the notification (ms)
        """
        self.notification_queue.put({
            'type': NotificationType.SUCCESS,
            'message': message,
            'duration': duration
        })

    def show_warning(self, message: str, duration: int = 3000):
        """
        Show warning notification.

        Args:
            message: Text to display
            duration: How long to show the notification (ms)
        """
        self.notification_queue.put({
            'type': NotificationType.WARNING,
            'message': message,
            'duration': duration
        })

    def show_error(self, message: str, duration: int = 5000):
        """
        Show error notification.

        Args:
            message: Text to display
            duration: How long to show the notification (ms)
        """
        self.notification_queue.put({
            'type': NotificationType.ERROR,
            'message': message,
            'duration': duration
        })

    def show_progress(self, message: str, callback: Optional[Callable] = None):
        """
        Show progress notification with indeterminate progress bar.

        Args:
            message: Text to display
            callback: Optional function to call when progress completes
        """
        self.notification_queue.put({
            'type': NotificationType.INFO,
            'message': message,
            'progress': True,
            'duration': 0,
            'callback': callback
        })

    def clear(self):
        """
        Clear current notification immediately.
        """
        self._clear_notification()

    def cleanup(self):
        """
        Cleanup resources before destroying the widget.

        Stops the notification thread cleanly.
        """
        self.is_running = False
        if self.notification_thread and self.notification_thread.is_alive():
            self.notification_thread.join(timeout=1.0)