# gui/views/patterns/pattern_file_viewer.py
"""
Pattern file viewer for viewing pattern files in various formats.

Provides a specialized view for displaying pattern files (SVG, PDF, images)
with zoom, pan, and measurement functionality.
"""

import logging
import os
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional, Tuple

from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS
from gui.utils.service_access import get_service

logger = logging.getLogger(__name__)


class PatternFileViewer(BaseDialog):
    """
    Dialog for viewing pattern files with specialized viewing capabilities.
    """

    def __init__(self, parent, file_id=None, file_path=None, file_type=None):
        """
        Initialize the pattern file viewer.

        Args:
            parent: The parent widget
            file_id: ID of the file to view from database (None for local files)
            file_path: Path to a local file (None for database files)
            file_type: File type override (optional)
        """
        self.file_id = file_id
        self.file_path = file_path
        self.file_type_override = file_type

        self.file_data = None
        self.file_content = None
        self.file_type = None
        self.temp_file = None

        # Viewer state
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_x = 0
        self.last_y = 0
        self.measuring = False
        self.measure_start = None
        self.measure_end = None
        self.measure_line = None
        self.measure_text = None

        # Determine title based on available info
        title = "Pattern File Viewer"
        if file_id:
            title = "View Pattern File"
        elif file_path:
            title = f"View: {os.path.basename(file_path)}"

        # Call parent constructor
        super().__init__(parent, title=title, width=800, height=600)

    def create_layout(self):
        """Create the dialog layout."""
        # Create toolbar
        toolbar = ttk.Frame(self.dialog_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=5)

        # File info section
        info_frame = ttk.Frame(toolbar)
        info_frame.pack(side=tk.LEFT)

        self.file_name_var = tk.StringVar(value="Loading file...")
        ttk.Label(
            info_frame,
            textvariable=self.file_name_var,
            font=("TkDefaultFont", 11, "bold")
        ).pack(anchor="w")

        self.file_info_var = tk.StringVar(value="")
        ttk.Label(
            info_frame,
            textvariable=self.file_info_var,
            foreground=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Zoom controls
        zoom_frame = ttk.Frame(toolbar)
        zoom_frame.pack(side=tk.RIGHT)

        zoom_out_btn = ttk.Button(
            zoom_frame,
            text="-",
            width=2,
            command=self.zoom_out
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.zoom_var = tk.StringVar(value="100%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var, width=5)
        zoom_label.pack(side=tk.LEFT, padx=(0, 5))

        zoom_in_btn = ttk.Button(
            zoom_frame,
            text="+",
            width=2,
            command=self.zoom_in
        )
        zoom_in_btn.pack(side=tk.LEFT)

        # Tool buttons
        tools_frame = ttk.Frame(toolbar)
        tools_frame.pack(side=tk.RIGHT, padx=(0, 20))

        # Pan tool
        self.pan_var = tk.BooleanVar(value=False)
        pan_btn = ttk.Checkbutton(
            tools_frame,
            text="Pan",
            variable=self.pan_var,
            command=self.toggle_pan
        )
        pan_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Measure tool
        self.measure_var = tk.BooleanVar(value=False)
        measure_btn = ttk.Checkbutton(
            tools_frame,
            text="Measure",
            variable=self.measure_var,
            command=self.toggle_measure
        )
        measure_btn.pack(side=tk.LEFT)

        # Create main viewing area with scrollbars
        view_frame = ttk.Frame(self.dialog_frame)
        view_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Add canvas and scrollbars
        self.h_scrollbar = ttk.Scrollbar(view_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = ttk.Scrollbar(view_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(
            view_frame,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
            bg="white"
        )

        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create status bar
        status_frame = ttk.Frame(self.dialog_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.status_var = tk.StringVar(value="Loading file...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)

        self.coords_var = tk.StringVar(value="")
        coords_label = ttk.Label(status_frame, textvariable=self.coords_var)
        coords_label.pack(side=tk.RIGHT)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<Motion>", self.on_mouse_hover)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/MacOS
        self.canvas.bind("<Button-4>", lambda e: self.on_mouse_wheel(e, 1))  # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self.on_mouse_wheel(e, -1))  # Linux scroll down

        # Load file
        self.load_file()

        # Create buttons
        button_frame = ttk.Frame(self.dialog_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        if self.file_id or self.file_path:
            save_btn = ttk.Button(
                button_frame,
                text="Save Copy As...",
                command=self.on_save_copy
            )
            save_btn.pack(side=tk.LEFT)

            if self.file_type in ["svg", "pdf", "png", "jpg", "jpeg"]:
                print_btn = ttk.Button(
                    button_frame,
                    text="Print...",
                    command=self.on_print
                )
                print_btn.pack(side=tk.LEFT, padx=(5, 0))

        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.close
        )
        close_btn.pack(side=tk.RIGHT)

    def load_file(self):
        """Load file data and display it."""
        try:
            if self.file_id:
                # Load file from database
                service = get_service("IPatternService")

                # Get file data
                self.file_data = service.get_pattern_file(self.file_id)

                if not self.file_data:
                    self.status_var.set("Error: File not found.")
                    messagebox.showerror("Error", "File not found.")
                    return

                # Get file content
                self.file_content = self.file_data.get("content")

                # Get file type
                self.file_type = self.file_data.get("file_type", "").lower()

                # Update file info
                self.file_name_var.set(self.file_data.get("name", "Unknown"))

                # Format size
                size = self.file_data.get("size", 0)
                size_text = self._format_file_size(size)

                # Get date
                date = self.file_data.get("created_at", "")
                if date:
                    if isinstance(date, str):
                        date = date[:10]

                self.file_info_var.set(f"{self.file_type.upper()} - {size_text} - Added: {date}")

            elif self.file_path:
                # Load file from path
                if not os.path.exists(self.file_path):
                    self.status_var.set("Error: File not found.")
                    messagebox.showerror("Error", "File not found.")
                    return

                # Read file content
                with open(self.file_path, "rb") as f:
                    self.file_content = f.read()

                # Get file type from extension or override
                if self.file_type_override:
                    self.file_type = self.file_type_override.lower()
                else:
                    _, ext = os.path.splitext(self.file_path)
                    self.file_type = ext[1:].lower()

                # Update file info
                self.file_name_var.set(os.path.basename(self.file_path))

                # Get file size
                size = os.path.getsize(self.file_path)
                size_text = self._format_file_size(size)

                # Get file modification date
                import datetime
                modified_time = os.path.getmtime(self.file_path)
                date = datetime.datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d")

                self.file_info_var.set(f"{self.file_type.upper()} - {size_text} - Modified: {date}")

            else:
                self.status_var.set("Error: No file specified.")
                messagebox.showerror("Error", "No file specified.")
                return

            # Display file
            self.display_file()

        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def display_file(self):
        """Display the file content on the canvas."""
        if not self.file_content:
            return

        # Create a temporary file for display if needed
        if self.temp_file:
            try:
                os.unlink(self.temp_file)
            except:
                pass
            self.temp_file = None

        # Handle different file types
        if self.file_type == "svg":
            self._display_svg()
        elif self.file_type in ["png", "jpg", "jpeg"]:
            self._display_image()
        elif self.file_type == "pdf":
            self._display_pdf()
        else:
            self._display_unsupported()

    def _display_svg(self):
        """Display SVG file on canvas."""
        try:
            # SVG display requires creating a temporary file and loading it with tkinter
            fd, self.temp_file = tempfile.mkstemp(suffix=".svg")
            os.close(fd)

            with open(self.temp_file, "wb") as f:
                f.write(self.file_content)

            # Check if PIL and svglib are available
            try:
                from PIL import Image, ImageTk
                import io
                import cairosvg

                # Convert SVG to PNG using cairosvg
                png_data = cairosvg.svg2png(
                    bytestring=self.file_content,
                    scale=self.zoom_level
                )

                # Load the PNG data with PIL
                image = Image.open(io.BytesIO(png_data))

                # Create a PhotoImage for the canvas
                self.photo_image = ImageTk.PhotoImage(image)

                # Display image
                self.canvas.delete("all")
                self.image_id = self.canvas.create_image(0, 0, image=self.photo_image, anchor="nw")

                # Update canvas scrollregion
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                # Update status
                self.status_var.set(f"SVG Image: {image.width} × {image.height}px")

            except ImportError:
                # Fallback - display error message
                self.canvas.delete("all")
                self.canvas.create_text(
                    400, 300,
                    text="SVG Viewer requires the PIL, cairosvg packages.\nPlease install these packages to view SVG files.",
                    font=("TkDefaultFont", 12),
                    fill="red",
                    justify="center"
                )

                # Update status
                self.status_var.set("Error: Missing required packages for SVG display.")

        except Exception as e:
            logger.error(f"Error displaying SVG: {str(e)}")
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 300,
                text=f"Error displaying SVG file:\n{str(e)}",
                font=("TkDefaultFont", 12),
                fill="red",
                justify="center"
            )
            self.status_var.set("Error displaying SVG file.")

    def _display_image(self):
        """Display image file (PNG, JPG) on canvas."""
        try:
            # Check if PIL is available
            try:
                from PIL import Image, ImageTk
                import io

                # Load the image from binary data
                image = Image.open(io.BytesIO(self.file_content))

                # Apply zoom
                if self.zoom_level != 1.0:
                    width = int(image.width * self.zoom_level)
                    height = int(image.height * self.zoom_level)
                    image = image.resize((width, height), Image.LANCZOS)

                # Create a PhotoImage for the canvas
                self.photo_image = ImageTk.PhotoImage(image)

                # Display image
                self.canvas.delete("all")
                self.image_id = self.canvas.create_image(0, 0, image=self.photo_image, anchor="nw")

                # Update canvas scrollregion
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                # Update status
                self.status_var.set(f"Image: {image.width} × {image.height}px")

            except ImportError:
                # Fallback - try with tkinter's PhotoImage for PNG
                if self.file_type == "png":
                    # Create a temporary file for the image
                    fd, self.temp_file = tempfile.mkstemp(suffix=".png")
                    os.close(fd)

                    with open(self.temp_file, "wb") as f:
                        f.write(self.file_content)

                    # Load with tkinter
                    self.photo_image = tk.PhotoImage(file=self.temp_file)

                    # Display image
                    self.canvas.delete("all")
                    self.image_id = self.canvas.create_image(0, 0, image=self.photo_image, anchor="nw")

                    # Update canvas scrollregion
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                    # Update status
                    self.status_var.set(f"Image: {self.photo_image.width()} × {self.photo_image.height()}px")

                else:
                    # JPG not supported with standard tkinter
                    self.canvas.delete("all")
                    self.canvas.create_text(
                        400, 300,
                        text="Image viewer requires the PIL package.\nPlease install this package to view JPG files.",
                        font=("TkDefaultFont", 12),
                        fill="red",
                        justify="center"
                    )

                    # Update status
                    self.status_var.set("Error: Missing required packages for image display.")

        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}")
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 300,
                text=f"Error displaying image file:\n{str(e)}",
                font=("TkDefaultFont", 12),
                fill="red",
                justify="center"
            )
            self.status_var.set("Error displaying image file.")

    def _display_pdf(self):
        """Display PDF file on canvas."""
        try:
            # PDF display requires creating a temporary file and using a PDF library
            fd, self.temp_file = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

            with open(self.temp_file, "wb") as f:
                f.write(self.file_content)

            # Check if pdf2image is available
            try:
                from pdf2image import convert_from_path
                from PIL import Image, ImageTk

                # Convert first page of PDF to image
                pages = convert_from_path(self.temp_file, dpi=100 * self.zoom_level, first_page=1, last_page=1)

                if pages:
                    # Get first page
                    image = pages[0]

                    # Create a PhotoImage for the canvas
                    self.photo_image = ImageTk.PhotoImage(image)

                    # Display image
                    self.canvas.delete("all")
                    self.image_id = self.canvas.create_image(0, 0, image=self.photo_image, anchor="nw")

                    # Update canvas scrollregion
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

                    # Update status
                    self.status_var.set(f"PDF Page 1: {image.width} × {image.height}px")

                    # TODO: Add PDF page navigation
                else:
                    self.canvas.delete("all")
                    self.canvas.create_text(
                        400, 300,
                        text="No pages found in PDF file.",
                        font=("TkDefaultFont", 12),
                        fill="red",
                        justify="center"
                    )
                    self.status_var.set("Error: No pages found in PDF file.")

            except ImportError:
                # Fallback - display error message
                self.canvas.delete("all")
                self.canvas.create_text(
                    400, 300,
                    text="PDF Viewer requires the pdf2image and poppler packages.\nPlease install these packages to view PDF files.",
                    font=("TkDefaultFont", 12),
                    fill="red",
                    justify="center"
                )

                # Update status
                self.status_var.set("Error: Missing required packages for PDF display.")

        except Exception as e:
            logger.error(f"Error displaying PDF: {str(e)}")
            self.canvas.delete("all")
            self.canvas.create_text(
                400, 300,
                text=f"Error displaying PDF file:\n{str(e)}",
                font=("TkDefaultFont", 12),
                fill="red",
                justify="center"
            )
            self.status_var.set("Error displaying PDF file.")

    def _display_unsupported(self):
        """Display message for unsupported file types."""
        self.canvas.delete("all")
        self.canvas.create_text(
            400, 300,
            text=f"Unsupported file type: {self.file_type}\n\nPlease use an external viewer for this file type.",
            font=("TkDefaultFont", 12),
            fill="red",
            justify="center"
        )
        self.status_var.set(f"Unsupported file type: {self.file_type}")

    def _format_file_size(self, size_bytes):
        """
        Format file size for display.

        Args:
            size_bytes: The file size in bytes

        Returns:
            A formatted string with appropriate units
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def zoom_in(self):
        """Increase zoom level and redisplay."""
        self.zoom_level *= 1.2
        self.update_zoom_display()
        self.display_file()

    def zoom_out(self):
        """Decrease zoom level and redisplay."""
        self.zoom_level /= 1.2
        self.update_zoom_display()
        self.display_file()

    def update_zoom_display(self):
        """Update zoom level display."""
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_var.set(f"{zoom_percent}%")

    def toggle_pan(self):
        """Toggle pan mode."""
        if self.pan_var.get():
            # Enable pan, disable measure
            self.measure_var.set(False)
            self.measuring = False
            self.canvas.config(cursor="fleur")  # Hand cursor
        else:
            self.canvas.config(cursor="")  # Default cursor

    def toggle_measure(self):
        """Toggle measure mode."""
        if self.measure_var.get():
            # Enable measure, disable pan
            self.pan_var.set(False)
            self.measuring = True
            self.canvas.config(cursor="crosshair")  # Crosshair cursor

            # Reset measurement
            self.measure_start = None
            self.measure_end = None

            # Remove any existing measurement
            if self.measure_line:
                self.canvas.delete(self.measure_line)
                self.measure_line = None

            if self.measure_text:
                self.canvas.delete(self.measure_text)
                self.measure_text = None
        else:
            self.measuring = False
            self.canvas.config(cursor="")  # Default cursor

    def on_mouse_down(self, event):
        """
        Handle mouse button press.

        Args:
            event: The mouse event
        """
        if self.pan_var.get():
            # Start panning
            self.is_panning = True
            self.last_x = event.x
            self.last_y = event.y
            self.canvas.config(cursor="fleur")

        elif self.measuring and not self.measure_start:
            # Start measuring
            self.measure_start = (event.x, event.y)

            # Convert to canvas coordinates
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            # Draw starting point
            point_radius = 3
            self.measure_point = self.canvas.create_oval(
                canvas_x - point_radius, canvas_y - point_radius,
                canvas_x + point_radius, canvas_y + point_radius,
                fill="red", outline="white"
            )

    def on_mouse_up(self, event):
        """
        Handle mouse button release.

        Args:
            event: The mouse event
        """
        if self.is_panning:
            # End panning
            self.is_panning = False

        elif self.measuring and self.measure_start:
            # End measuring
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            if self.measure_start:
                start_x = self.canvas.canvasx(self.measure_start[0])
                start_y = self.canvas.canvasy(self.measure_start[1])

                # Only draw if mouse moved
                if (start_x != canvas_x or start_y != canvas_y):
                    # Draw the measurement line
                    if self.measure_line:
                        self.canvas.delete(self.measure_line)

                    self.measure_line = self.canvas.create_line(
                        start_x, start_y, canvas_x, canvas_y,
                        fill="red", width=2, dash=(4, 2)
                    )

                    # Calculate distance in pixels
                    dx = canvas_x - start_x
                    dy = canvas_y - start_y
                    dist_px = (dx ** 2 + dy ** 2) ** 0.5

                    # Convert to real-world units (assuming 100dpi for now)
                    # This would need to be adjusted based on actual scale
                    dist_mm = dist_px * 25.4 / 100  # Convert to mm

                    # Display measurement
                    if self.measure_text:
                        self.canvas.delete(self.measure_text)

                    # Position text in middle of line
                    text_x = start_x + dx / 2
                    text_y = start_y + dy / 2 - 10

                    self.measure_text = self.canvas.create_text(
                        text_x, text_y,
                        text=f"{dist_mm:.1f} mm",
                        fill="red",
                        font=("TkDefaultFont", 9, "bold"),
                        background="white"
                    )

                    # Reset for next measurement
                    self.measure_start = None

    def on_mouse_move(self, event):
        """
        Handle mouse movement with button held.

        Args:
            event: The mouse event
        """
        if self.is_panning:
            # Pan the canvas
            dx = event.x - self.last_x
            dy = event.y - self.last_y

            self.canvas.xview_scroll(-dx, "units")
            self.canvas.yview_scroll(-dy, "units")

            self.last_x = event.x
            self.last_y = event.y

        elif self.measuring and self.measure_start:
            # Update measurement preview
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)

            start_x = self.canvas.canvasx(self.measure_start[0])
            start_y = self.canvas.canvasy(self.measure_start[1])

            # Draw or update temporary line
            if self.measure_line:
                self.canvas.delete(self.measure_line)

            self.measure_line = self.canvas.create_line(
                start_x, start_y, canvas_x, canvas_y,
                fill="red", width=2, dash=(4, 2)
            )

            # Calculate and display distance
            dx = canvas_x - start_x
            dy = canvas_y - start_y
            dist_px = (dx ** 2 + dy ** 2) ** 0.5

            # Convert to real-world units (assuming 100dpi for now)
            dist_mm = dist_px * 25.4 / 100

            if self.measure_text:
                self.canvas.delete(self.measure_text)

            text_x = start_x + dx / 2
            text_y = start_y + dy / 2 - 10

            self.measure_text = self.canvas.create_text(
                text_x, text_y,
                text=f"{dist_mm:.1f} mm",
                fill="red",
                font=("TkDefaultFont", 9, "bold"),
                background="white"
            )

    def on_mouse_hover(self, event):
        """
        Handle mouse hover (no button).

        Args:
            event: The mouse event
        """
        # Update coordinates display
        canvas_x = int(self.canvas.canvasx(event.x))
        canvas_y = int(self.canvas.canvasy(event.y))

        self.coords_var.set(f"X: {canvas_x}, Y: {canvas_y}")

    def on_mouse_wheel(self, event, direction=None):
        """
        Handle mouse wheel for zooming.

        Args:
            event: The mouse wheel event
            direction: Force scroll direction (for Linux)
        """
        # Determine scroll direction
        if direction is not None:
            # Linux scroll events
            delta = direction
        else:
            # Windows/MacOS
            delta = event.delta

        # Zoom in or out based on scroll direction
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def on_save_copy(self):
        """Handle save copy button click."""
        if not self.file_content:
            messagebox.showerror("Error", "No file content to save.")
            return

        try:
            # Get file type
            file_type = self.file_type.upper()

            # Get file name
            if self.file_id:
                initial_file = self.file_data.get("name", "pattern_file")
            elif self.file_path:
                initial_file = os.path.basename(self.file_path)
            else:
                initial_file = "pattern_file"

            # Configure file dialog
            file_types = [(f"{file_type} Files", f"*.{self.file_type}"), ("All Files", "*.*")]
            default_ext = f".{self.file_type}"

            # Show save dialog
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=file_types,
                initialfile=initial_file,
                title="Save Copy As"
            )

            if file_path:
                # Save file
                with open(file_path, "wb") as f:
                    f.write(self.file_content)

                messagebox.showinfo("Save Complete", f"File saved to:\n{file_path}")

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def on_print(self):
        """Handle print button click."""
        if not self.file_content:
            messagebox.showerror("Error", "No file content to print.")
            return

        try:
            # Create temporary file if needed
            if not self.temp_file:
                fd, self.temp_file = tempfile.mkstemp(suffix=f".{self.file_type}")
                os.close(fd)

                with open(self.temp_file, "wb") as f:
                    f.write(self.file_content)

            # Check file type
            if self.file_type == "pdf":
                self._print_pdf()
            elif self.file_type in ["svg", "png", "jpg", "jpeg"]:
                self._print_image()
            else:
                messagebox.showerror("Error", f"Printing not supported for {self.file_type.upper()} files.")

        except Exception as e:
            logger.error(f"Error printing file: {str(e)}")
            messagebox.showerror("Error", f"Failed to print file: {str(e)}")

    def _print_pdf(self):
        """Print PDF file."""
        # Check platform
        import platform
        import subprocess

        if platform.system() == "Windows":
            # Windows - use the default PDF viewer to print
            os.startfile(self.temp_file, "print")

        elif platform.system() == "Darwin":  # macOS
            # Use lp command
            subprocess.call(["lp", self.temp_file])

        else:  # Linux
            # Use lp or xdg-open
            try:
                subprocess.call(["lp", self.temp_file])
            except:
                # Try with default viewer
                subprocess.call(["xdg-open", self.temp_file])

    def _print_image(self):
        """Print image file."""
        try:
            # Convert to PDF first for better printing
            from PIL import Image
            import io

            # Create a PDF from the image
            fd, pdf_file = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)

            # Load image
            if self.file_type == "svg":
                try:
                    import cairosvg
                    # Convert SVG to PDF
                    cairosvg.svg2pdf(
                        bytestring=self.file_content,
                        write_to=pdf_file
                    )
                except ImportError:
                    # Fallback - use PIL to convert image
                    import cairosvg
                    png_data = cairosvg.svg2png(bytestring=self.file_content)
                    image = Image.open(io.BytesIO(png_data))
                    image.save(pdf_file, "PDF", resolution=100.0)

            else:
                # Load image with PIL
                image = Image.open(io.BytesIO(self.file_content))
                image.save(pdf_file, "PDF", resolution=100.0)

            # Print the PDF
            import platform
            import subprocess

            if platform.system() == "Windows":
                # Windows - use the default PDF viewer to print
                os.startfile(pdf_file, "print")

            elif platform.system() == "Darwin":  # macOS
                # Use lp command
                subprocess.call(["lp", pdf_file])

            else:  # Linux
                # Use lp or xdg-open
                try:
                    subprocess.call(["lp", pdf_file])
                except:
                    # Try with default viewer
                    subprocess.call(["xdg-open", pdf_file])

            # Clean up
            try:
                os.unlink(pdf_file)
            except:
                pass

        except Exception as e:
            logger.error(f"Error printing image: {str(e)}")
            messagebox.showerror("Error", f"Failed to print image: {str(e)}")

            # Fallback - try to open the file with default viewer
            self._open_with_default_viewer()

    def _open_with_default_viewer(self):
        """Open file with default system viewer."""
        if not self.temp_file:
            return

        import platform
        import subprocess

        try:
            if platform.system() == "Windows":
                os.startfile(self.temp_file)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", self.temp_file])
            else:  # Linux
                subprocess.call(["xdg-open", self.temp_file])
        except Exception as e:
            logger.error(f"Error opening file with default viewer: {str(e)}")

    def close(self):
        """Override close to clean up temporary files."""
        # Clean up temporary file
        if self.temp_file:
            try:
                os.unlink(self.temp_file)
            except:
                pass

        # Call parent close
        super().close()