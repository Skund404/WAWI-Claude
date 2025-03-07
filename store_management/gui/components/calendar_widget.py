"""
Calendar widget for date selection.
Provides a custom calendar date picker component.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, Union
import calendar
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


class CalendarWidget(ttk.Frame):
    """
    Calendar widget for date selection.

    Features:
    - Month and year navigation
    - Today button
    - Week number display (optional)
    - First day of week selection
    - Highlighted today date
    - Custom event callbacks
    """

    def __init__(self, parent: tk.Widget,
                 selected_date: Optional[Union[date, datetime]] = None,
                 on_date_select: Optional[Callable[[date], None]] = None,
                 show_week_numbers: bool = False,
                 first_day_of_week: int = calendar.MONDAY,
                 **kwargs):
        """
        Initialize the calendar widget.

        Args:
            parent: Parent widget
            selected_date: Initially selected date (default: today)
            on_date_select: Callback function when a date is selected
            show_week_numbers: Whether to show week numbers
            first_day_of_week: First day of week (0 = Monday, 6 = Sunday)
            **kwargs: Additional arguments for ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Store parameters
        self.show_week_numbers = show_week_numbers
        self.first_day_of_week = first_day_of_week
        self.on_date_select = on_date_select

        # Initialize dates
        self.today = date.today()
        self.selected_date = self.today

        if selected_date:
            if isinstance(selected_date, datetime):
                self.selected_date = selected_date.date()
            else:
                self.selected_date = selected_date

        # Current displayed month and year
        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year

        # Create the widget
        self._create_calendar()

        logger.debug("Calendar widget initialized")

    def _create_calendar(self):
        """Create the calendar layout."""
        # Create header with month/year display and navigation
        self._create_header()

        # Create the calendar grid
        self._create_calendar_grid()

        # Create footer with Today button
        self._create_footer()

        # Draw the initial calendar
        self._draw_calendar()

    def _create_header(self):
        """Create the calendar header with navigation controls."""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        # Previous year button
        self.prev_year_btn = ttk.Button(
            header_frame,
            text="<<",
            width=2,
            command=self._prev_year
        )
        self.prev_year_btn.pack(side=tk.LEFT, padx=2)

        # Previous month button
        self.prev_month_btn = ttk.Button(
            header_frame,
            text="<",
            width=2,
            command=self._prev_month
        )
        self.prev_month_btn.pack(side=tk.LEFT, padx=2)

        # Month/Year display
        self.month_year_var = tk.StringVar()
        self.month_year_label = ttk.Label(
            header_frame,
            textvariable=self.month_year_var,
            anchor=tk.CENTER,
            width=15
        )
        self.month_year_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Next month button
        self.next_month_btn = ttk.Button(
            header_frame,
            text=">",
            width=2,
            command=self._next_month
        )
        self.next_month_btn.pack(side=tk.RIGHT, padx=2)

        # Next year button
        self.next_year_btn = ttk.Button(
            header_frame,
            text=">>",
            width=2,
            command=self._next_year
        )
        self.next_year_btn.pack(side=tk.RIGHT, padx=2)

    def _create_calendar_grid(self):
        """Create the calendar grid for days."""
        # Create frame for the calendar grid
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)

        # Create and configure grid
        for i in range(7):  # 7 columns for days
            self.calendar_frame.columnconfigure(i + (1 if self.show_week_numbers else 0), weight=1)

        for i in range(7):  # 7 rows (header + 6 rows of days)
            self.calendar_frame.rowconfigure(i, weight=1)

        # Create day header labels
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days = days[self.first_day_of_week:] + days[:self.first_day_of_week]

        # Week number header if needed
        if self.show_week_numbers:
            wk_label = ttk.Label(
                self.calendar_frame,
                text="Wk",
                anchor=tk.CENTER,
                style="Calendar.TLabel"
            )
            wk_label.grid(row=0, column=0, sticky=tk.NSEW, padx=1, pady=1)

        # Day headers
        for i, day in enumerate(days):
            col = i + (1 if self.show_week_numbers else 0)
            day_label = ttk.Label(
                self.calendar_frame,
                text=day,
                anchor=tk.CENTER,
                style="Calendar.TLabel"
            )
            day_label.grid(row=0, column=col, sticky=tk.NSEW, padx=1, pady=1)

        # Create buttons for days
        self.day_buttons = []
        start_col = 1 if self.show_week_numbers else 0

        for row in range(6):
            row_buttons = []

            # Week number labels if needed
            if self.show_week_numbers:
                week_label = ttk.Label(
                    self.calendar_frame,
                    text="",
                    anchor=tk.CENTER,
                    style="Week.TLabel"
                )
                week_label.grid(row=row + 1, column=0, sticky=tk.NSEW, padx=1, pady=1)
                row_buttons.append(week_label)

            # Day buttons
            for col in range(7):
                day_button = ttk.Button(
                    self.calendar_frame,
                    text="",
                    width=3,
                    style="Calendar.TButton",
                    command=lambda r=row, c=col: self._on_day_click(r, c)
                )
                day_button.grid(
                    row=row + 1,
                    column=col + start_col,
                    sticky=tk.NSEW,
                    padx=1,
                    pady=1
                )
                row_buttons.append(day_button)

            self.day_buttons.append(row_buttons)

    def _create_footer(self):
        """Create the calendar footer with the Today button."""
        footer_frame = ttk.Frame(self)
        footer_frame.pack(fill=tk.X, pady=(5, 0))

        # Today button
        self.today_btn = ttk.Button(
            footer_frame,
            text="Today",
            command=self._go_to_today
        )
        self.today_btn.pack(side=tk.RIGHT)

    def _draw_calendar(self):
        """Draw the calendar for the current month/year."""
        # Update month/year label
        month_name = calendar.month_name[self.current_month]
        self.month_year_var.set(f"{month_name} {self.current_year}")

        # Get the first day of the month
        first_day = date(self.current_year, self.current_month, 1)

        # Get the number of days in the month
        if self.current_month == 12:
            last_day = date(self.current_year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)

        days_in_month = last_day.day

        # Get the day of the week for the first day (0 = Monday, 6 = Sunday)
        first_weekday = first_day.weekday()

        # Adjust for first day of week
        first_weekday = (first_weekday - self.first_day_of_week) % 7

        # Clear previous calendar
        for row in range(6):
            for col in range(7):
                button_idx = col + (1 if self.show_week_numbers else 0)
                if button_idx < len(self.day_buttons[row]):
                    self.day_buttons[row][button_idx].configure(
                        text="",
                        state=tk.DISABLED,
                        style="Calendar.TButton"
                    )

        # Set week numbers if needed
        if self.show_week_numbers:
            for row in range(6):
                # Calculate date for the Monday of this week
                week_date = first_day + timedelta(days=(row * 7) - first_weekday)
                week_num = week_date.isocalendar()[1]

                self.day_buttons[row][0].configure(
                    text=str(week_num)
                )

        # Fill in the calendar
        day = 1
        for row in range(6):
            for col in range(7):
                button_idx = col + (1 if self.show_week_numbers else 0)

                if (row == 0 and col < first_weekday) or day > days_in_month:
                    # Empty or disabled days
                    continue

                # Calculate the current date
                current_date = date(self.current_year, self.current_month, day)

                # Configure button text and state
                self.day_buttons[row][button_idx].configure(
                    text=str(day),
                    state=tk.NORMAL
                )

                # Style for today and selected date
                if current_date == self.today:
                    self.day_buttons[row][button_idx].configure(
                        style="Today.TButton"
                    )

                if current_date == self.selected_date:
                    self.day_buttons[row][button_idx].configure(
                        style="Selected.TButton"
                    )

                # Store the date in the button tags
                self.day_buttons[row][button_idx].date = current_date

                day += 1

    def _on_day_click(self, row: int, col: int):
        """
        Handle day button click.

        Args:
            row: Button row
            col: Button column
        """
        # Calculate actual button index
        button_idx = col + (1 if self.show_week_numbers else 0)
        button = self.day_buttons[row][button_idx]

        # Check if button has a date
        if hasattr(button, 'date'):
            # Update selected date
            self.selected_date = button.date

            # Redraw calendar
            self._draw_calendar()

            # Call callback if provided
            if self.on_date_select:
                self.on_date_select(self.selected_date)

    def _prev_year(self):
        """Go to the previous year."""
        self.current_year -= 1
        self._draw_calendar()

    def _next_year(self):
        """Go to the next year."""
        self.current_year += 1
        self._draw_calendar()

    def _prev_month(self):
        """Go to the previous month."""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._draw_calendar()

    def _next_month(self):
        """Go to the next month."""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._draw_calendar()

    def _go_to_today(self):
        """Go to today's date."""
        self.current_month = self.today.month
        self.current_year = self.today.year
        self.selected_date = self.today
        self._draw_calendar()

        # Call callback if provided
        if self.on_date_select:
            self.on_date_select(self.selected_date)

    def get_date(self) -> date:
        """
        Get the currently selected date.

        Returns:
            The selected date
        """
        return self.selected_date

    def set_date(self, new_date: Union[date, datetime, str]):
        """
        Set the calendar date.

        Args:
            new_date: Date to set (date object, datetime object, or YYYY-MM-DD string)
        """
        try:
            # Parse the date if it's a string
            if isinstance(new_date, str):
                parts = new_date.split('-')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    new_date = date(year, month, day)
                else:
                    raise ValueError("Date string must be in YYYY-MM-DD format")

            # Extract date from datetime if needed
            if isinstance(new_date, datetime):
                new_date = new_date.date()

            # Update current month and year
            self.current_month = new_date.month
            self.current_year = new_date.year
            self.selected_date = new_date

            # Redraw calendar
            self._draw_calendar()

        except Exception as e:
            logger.error(f"Error setting date: {e}")

    @staticmethod
    def create_date_picker(parent: tk.Widget, label_text: str = "",
                           initial_date: Optional[date] = None,
                           callback: Optional[Callable[[date], None]] = None) -> ttk.Frame:
        """
        Create a date picker with label and entry field.

        Args:
            parent: Parent widget
            label_text: Label text
            initial_date: Initial date
            callback: Callback function when date changes

        Returns:
            Frame containing the date picker
        """
        frame = ttk.Frame(parent)

        # Create label if provided
        if label_text:
            label = ttk.Label(frame, text=label_text)
            label.pack(side=tk.LEFT, padx=(0, 5))

        # Create StringVar to hold the date text
        date_var = tk.StringVar()
        if initial_date:
            date_var.set(initial_date.strftime("%Y-%m-%d"))
        else:
            date_var.set(date.today().strftime("%Y-%m-%d"))

        # Create entry field
        entry = ttk.Entry(frame, textvariable=date_var, width=12)
        entry.pack(side=tk.LEFT)

        # Create button to show calendar
        calendar_button = ttk.Button(
            frame,
            text="📅",
            width=3
        )
        calendar_button.pack(side=tk.LEFT, padx=(5, 0))

        # Function to show calendar popup
        def show_calendar():
            # Get the current date from the entry
            try:
                current_date = datetime.strptime(date_var.get(), "%Y-%m-%d").date()
            except ValueError:
                current_date = date.today()

            # Create a toplevel for the calendar
            top = tk.Toplevel(frame)
            top.title("Select Date")
            top.transient(parent)
            top.grab_set()

            # Function to handle date selection
            def on_select(selected_date):
                date_var.set(selected_date.strftime("%Y-%m-%d"))
                top.destroy()
                if callback:
                    callback(selected_date)

            # Create calendar widget
            calendar = CalendarWidget(
                top,
                selected_date=current_date,
                on_date_select=on_select,
                padding=10
            )
            calendar.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Center the dialog on the parent
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (top.winfo_reqwidth() // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (top.winfo_reqheight() // 2)
            top.geometry(f"+{x}+{y}")

        # Bind button to show calendar
        calendar_button.configure(command=show_calendar)

        # Bind Enter key in entry to show calendar
        entry.bind("<Return>", lambda event: show_calendar())

        return frame


# Add styles for the calendar widget
def setup_calendar_styles():
    """Configure ttk styles for the calendar widget."""
    style = ttk.Style()

    # Day button styles
    style.configure("Calendar.TButton",
                    width=3,
                    padding=2)

    style.configure("Today.TButton",
                    background="#e3f2fd",
                    foreground="blue")

    style.configure("Selected.TButton",
                    background="#1a73e8",
                    foreground="white")

    # Calendar label styles
    style.configure("Calendar.TLabel",
                    font=("", 9, "bold"),
                    background="#f5f5f5",
                    padding=2)

    style.configure("Week.TLabel",
                    font=("", 8),
                    background="#f5f5f5",
                    foreground="gray")


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Calendar Widget Demo")
    root.geometry("500x400")

    # Set up styles
    setup_calendar_styles()

    # Create a frame for the calendar
    frame = ttk.Frame(root, padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    # Label for selected date
    selected_label = ttk.Label(frame, text="Selected Date: None")
    selected_label.pack(pady=(0, 10))


    # Callback function for date selection
    def on_date_select(selected_date):
        selected_label.config(text=f"Selected Date: {selected_date}")


    # Create calendar widget
    calendar = CalendarWidget(
        frame,
        on_date_select=on_date_select,
        show_week_numbers=True
    )
    calendar.pack(fill=tk.BOTH, expand=True)

    # Create separator
    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    # Create date picker example
    date_picker_label = ttk.Label(frame, text="Date Picker Example:")
    date_picker_label.pack(anchor=tk.W, pady=(10, 5))

    # Create date picker
    date_picker = CalendarWidget.create_date_picker(
        frame,
        label_text="Select Date:",
        callback=on_date_select
    )
    date_picker.pack(anchor=tk.W, pady=5)

    root.mainloop()