import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import time
from enum import Enum
from queue import Queue
import threading


class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class StatusNotification:
    """Status notification manager"""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.notification_queue = Queue()
        self.current_notification = None
        self.notification_thread = None
        self.is_running = True

        # Create notification frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Status label
        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            length=100
        )

        # Configure styles
        self.setup_styles()

        # Start notification processor
        self.start_processor()

    def setup_styles(self):
        """Setup notification styles"""
        style = ttk.Style()

        # Info style
        style.configure(
            "Info.TLabel",
            foreground="black",
            background="#e3f2fd"
        )

        # Success style
        style.configure(
            "Success.TLabel",
            foreground="dark green",
            background="#e8f5e9"
        )

        # Warning style
        style.configure(
            "Warning.TLabel",
            foreground="dark orange",
            background="#fff3e0"
        )

        # Error style
        style.configure(
            "Error.TLabel",
            foreground="dark red",
            background="#ffebee"
        )

    def start_processor(self):
        """Start notification processing thread"""
        self.notification_thread = threading.Thread(
            target=self._process_notifications,
            daemon=True
        )
        self.notification_thread.start()

    def _process_notifications(self):
        """Process notifications from queue"""
        while self.is_running:
            if not self.notification_queue.empty():
                notification = self.notification_queue.get()
                # Schedule the notification display on the main thread
                self.parent.after(0, lambda: self._show_notification(notification))
            time.sleep(0.1)

    def _show_notification(self, notification: dict):
        """Show notification"""
        try:
            message = notification['message']
            ntype = notification['type']
            duration = notification.get('duration', 3000)
            progress = notification.get('progress', False)
            callback = notification.get('callback')

            # Update label style and text
            self.status_label.configure(
                style=f"{ntype.value.title()}.TLabel",
                text=message
            )

            # Show/hide progress bar
            if progress:
                self.progress.pack(side=tk.RIGHT, padx=5)
                self.progress.start()
            else:
                self.progress.stop()
                self.progress.pack_forget()

            # Schedule notification removal
            if duration > 0:
                self.parent.after(duration, lambda: self._clear_notification(callback))
        except Exception as e:
            print(f"Error showing notification: {e}")

    def _clear_notification(self, callback: Optional[Callable] = None):
        """Clear current notification"""
        self.status_label.configure(text="", style="TLabel")
        self.progress.stop()
        self.progress.pack_forget()

        if callback:
            callback()

    def show_info(self, message: str, duration: int = 3000):
        """Show info notification"""
        self.notification_queue.put({
            'type': NotificationType.INFO,
            'message': message,
            'duration': duration
        })

    def show_success(self, message: str, duration: int = 3000):
        """Show success notification"""
        self.notification_queue.put({
            'type': NotificationType.SUCCESS,
            'message': message,
            'duration': duration
        })

    def show_warning(self, message: str, duration: int = 3000):
        """Show warning notification"""
        self.notification_queue.put({
            'type': NotificationType.WARNING,
            'message': message,
            'duration': duration
        })

    def show_error(self, message: str, duration: int = 5000):
        """Show error notification"""
        self.notification_queue.put({
            'type': NotificationType.ERROR,
            'message': message,
            'duration': duration
        })

    def show_progress(self, message: str, callback: Optional[Callable] = None):
        """Show progress notification"""
        self.notification_queue.put({
            'type': NotificationType.INFO,
            'message': message,
            'progress': True,
            'duration': 0,
            'callback': callback
        })

    def clear(self):
        """Clear current notification"""
        self._clear_notification()

    def cleanup(self):
        """Cleanup resources"""
        self.is_running = False
        if self.notification_thread and self.notification_thread.is_alive():
            self.notification_thread.join(timeout=1.0)
