"""
Image and SVG viewer component.
Provides a widget for displaying and interacting with images and SVG files.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, Tuple, Union
import os
import io
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

# Try to import svglib for SVG support
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

    SVG_SUPPORT = True
except ImportError:
    logger.warning("svglib and reportlab not available. SVG support will be limited.")
    SVG_SUPPORT = False


class ImageViewer(ttk.Frame):
    """
    Widget for displaying and interacting with images.

    Features:
    - Image loading from file or data
    - SVG support
    - Zooming and panning
    - Fit-to-width/height options
    - Image rotation
    """

    def __init__(self, parent: tk.Widget, image_path: Optional[str] = None,
                 image_data: Optional[bytes] = None,
                 max_size: Optional[Tuple[int, int]] = None,
                 keep_aspect: bool = True, bg_color: str = "#ffffff",
                 show_toolbar: bool = True, **kwargs):
        """
        Initialize the image viewer.

        Args:
            parent: Parent widget
            image_path: Optional path to image file
            image_data: Optional image data as bytes
            max_size: Optional maximum size (width, height) for the image
            keep_aspect: Whether to maintain aspect ratio
            bg_color: Background color
            show_toolbar: Whether to show the toolbar
            **kwargs: Additional arguments for ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Store parameters
        self.image_path = image_path
        self.image_data = image_data
        self.max_size = max_size
        self.keep_aspect = keep_aspect
        self.bg_color = bg_color

        # Initialize state variables
        self.pil_image = None
        self.tk_image = None
        self.zoom_level = 1.0
        self.rotation_angle = 0
        self.drag_data = {"x": 0, "y": 0, "dragging": False}

        # Create the viewer
        self._create_viewer(show_toolbar)

        # Load image if provided
        if image_path:
            self.load_image_from_file(image_path)
        elif image_data:
            self.load_image_from_data(image_data)

        logger.debug(f"Image viewer initialized")

    def _create_viewer(self, show_toolbar: bool):
        """
        Create the image viewer components.

        Args:
            show_toolbar: Whether to show the toolbar
        """
        # Create main layout
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Canvas
        self.columnconfigure(0, weight=1)

        # Create toolbar if requested
        if show_toolbar:
            self._create_toolbar()

        # Create canvas for image
        self.canvas = tk.Canvas(
            self,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.grid(row=1, column=0, sticky=tk.NSEW)

        # Add scrollbars
        self.h_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        self.h_scrollbar.grid(row=2, column=0, sticky=tk.EW)

        self.v_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.v_scrollbar.grid(row=1, column=1, sticky=tk.NS)

        # Configure canvas to use scrollbars
        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )

        # Bind events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux scroll down

        # Configure resize handler
        self.bind("<Configure>", self._on_resize)

    def _create_toolbar(self):
        """Create the toolbar with image controls."""
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # Zoom controls
        zoom_out_btn = ttk.Button(
            toolbar,
            text="−",
            width=2,
            command=lambda: self.zoom(0.9)
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=2)

        zoom_reset_btn = ttk.Button(
            toolbar,
            text="100%",
            width=5,
            command=self.zoom_reset
        )
        zoom_reset_btn.pack(side=tk.LEFT, padx=2)

        zoom_in_btn = ttk.Button(
            toolbar,
            text="+",
            width=2,
            command=lambda: self.zoom(1.1)
        )
        zoom_in_btn.pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Fit controls
        fit_width_btn = ttk.Button(
            toolbar,
            text="Fit Width",
            command=self.fit_to_width
        )
        fit_width_btn.pack(side=tk.LEFT, padx=2)

        fit_height_btn = ttk.Button(
            toolbar,
            text="Fit Height",
            command=self.fit_to_height
        )
        fit_height_btn.pack(side=tk.LEFT, padx=2)

        fit_window_btn = ttk.Button(
            toolbar,
            text="Fit Window",
            command=self.fit_to_window
        )
        fit_window_btn.pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Rotation controls
        rotate_left_btn = ttk.Button(
            toolbar,
            text="⟲",
            width=2,
            command=lambda: self.rotate(-90)
        )
        rotate_left_btn.pack(side=tk.LEFT, padx=2)

        rotate_right_btn = ttk.Button(
            toolbar,
            text="⟳",
            width=2,
            command=lambda: self.rotate(90)
        )
        rotate_right_btn.pack(side=tk.LEFT, padx=2)

    def load_image_from_file(self, filepath: str) -> bool:
        """
        Load image from a file.

        Args:
            filepath: Path to the image file

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Check for SVG files
            if filepath.lower().endswith('.svg') and SVG_SUPPORT:
                # Convert SVG to PIL Image
                drawing = svg2rlg(filepath)
                png_data = renderPM.drawToString(drawing, fmt='PNG')
                self.pil_image = Image.open(io.BytesIO(png_data))
            else:
                # Load with PIL
                self.pil_image = Image.open(filepath)

            # Store the path
            self.image_path = filepath
            self.image_data = None

            # Reset view
            self.zoom_level = 1.0
            self.rotation_angle = 0

            # Display the image
            self._display_image()

            logger.debug(f"Loaded image from file: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error loading image from file {filepath}: {e}")
            return False

    def load_image_from_data(self, data: bytes, format: Optional[str] = None) -> bool:
        """
        Load image from bytes data.

        Args:
            data: Image data as bytes
            format: Optional image format (e.g., 'PNG', 'JPEG')

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Handle SVG data
            if format == 'SVG' and SVG_SUPPORT:
                # Convert SVG to PIL Image
                svg_file = io.BytesIO(data)
                drawing = svg2rlg(svg_file)
                png_data = renderPM.drawToString(drawing, fmt='PNG')
                self.pil_image = Image.open(io.BytesIO(png_data))
            else:
                # Load with PIL
                self.pil_image = Image.open(io.BytesIO(data))

            # Store the data
            self.image_path = None
            self.image_data = data

            # Reset view
            self.zoom_level = 1.0
            self.rotation_angle = 0

            # Display the image
            self._display_image()

            logger.debug(f"Loaded image from data")
            return True

        except Exception as e:
            logger.error(f"Error loading image from data: {e}")
            return False

    def _display_image(self):
        """Display the current image on the canvas."""
        if not self.pil_image:
            return

        # Apply rotation if any
        if self.rotation_angle:
            rotated_image = self.pil_image.rotate(
                angle=self.rotation_angle,
                expand=True,
                resample=Image.BICUBIC
            )
        else:
            rotated_image = self.pil_image

        # Calculate dimensions based on zoom level
        width = int(rotated_image.width * self.zoom_level)
        height = int(rotated_image.height * self.zoom_level)

        # If max size is specified, constrain dimensions
        if self.max_size:
            max_width, max_height = self.max_size
            if width > max_width or height > max_height:
                # Calculate scale factor to fit within max size
                scale_w = max_width / width if width > max_width else 1.0
                scale_h = max_height / height if height > max_height else 1.0

                # Use the smaller scale factor to ensure both constraints are met
                scale = min(scale_w, scale_h)

                # Adjust zoom level and recalculate dimensions
                self.zoom_level *= scale
                width = int(rotated_image.width * self.zoom_level)
                height = int(rotated_image.height * self.zoom_level)

        # Resize the image
        resized_image = rotated_image.resize((width, height), Image.Resampling.LANCZOS)

        # Convert to Tkinter image
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # Update canvas
        self.canvas.delete("image")
        self.image_id = self.canvas.create_image(
            0, 0,  # Initial position (top-left)
            anchor=tk.NW,
            image=self.tk_image,
            tags="image"
        )

        # Configure canvas scrollregion
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def zoom(self, factor: float):
        """
        Zoom the image by the specified factor.

        Args:
            factor: Zoom factor (>1 to zoom in, <1 to zoom out)
        """
        if not self.pil_image:
            return

        # Update zoom level
        old_zoom = self.zoom_level
        self.zoom_level *= factor

        # Ensure reasonable zoom limits
        self.zoom_level = min(max(0.1, self.zoom_level), 10.0)

        # Display the image with new zoom level
        self._display_image()

        logger.debug(f"Zoomed image: factor={factor}, zoom_level={self.zoom_level}")

    def zoom_reset(self):
        """Reset zoom to 100%."""
        if not self.pil_image:
            return

        self.zoom_level = 1.0
        self._display_image()

        logger.debug("Reset zoom to 100%")

    def fit_to_width(self):
        """Fit the image to the canvas width."""
        if not self.pil_image:
            return

        # Get the current canvas width
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not yet fully initialized
            self.update_idletasks()
            canvas_width = self.canvas.winfo_width()

        # Calculate the scaling factor
        if self.rotation_angle in [90, 270]:
            # Handle rotated image
            image_width = self.pil_image.height
        else:
            image_width = self.pil_image.width

        if image_width > 0:
            self.zoom_level = canvas_width / image_width
            self._display_image()

            logger.debug(f"Fit to width: zoom_level={self.zoom_level}")

    def fit_to_height(self):
        """Fit the image to the canvas height."""
        if not self.pil_image:
            return

        # Get the current canvas height
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1:  # Canvas not yet fully initialized
            self.update_idletasks()
            canvas_height = self.canvas.winfo_height()

        # Calculate the scaling factor
        if self.rotation_angle in [90, 270]:
            # Handle rotated image
            image_height = self.pil_image.width
        else:
            image_height = self.pil_image.height

        if image_height > 0:
            self.zoom_level = canvas_height / image_height
            self._display_image()

            logger.debug(f"Fit to height: zoom_level={self.zoom_level}")

    def fit_to_window(self):
        """Fit the image to the canvas window."""
        if not self.pil_image:
            return

        # Get the current canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet fully initialized
            self.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

        # Calculate the scaling factors
        if self.rotation_angle in [90, 270]:
            # Handle rotated image
            image_width = self.pil_image.height
            image_height = self.pil_image.width
        else:
            image_width = self.pil_image.width
            image_height = self.pil_image.height

        if image_width > 0 and image_height > 0:
            scale_w = canvas_width / image_width
            scale_h = canvas_height / image_height

            # Use the smaller scale factor to ensure the image fits
            self.zoom_level = min(scale_w, scale_h)
            self._display_image()

            logger.debug(f"Fit to window: zoom_level={self.zoom_level}")

    def rotate(self, angle: int):
        """
        Rotate the image by the specified angle.

        Args:
            angle: Rotation angle in degrees
        """
        if not self.pil_image:
            return

        # Update rotation angle (normalized to 0-359)
        self.rotation_angle = (self.rotation_angle + angle) % 360

        # Display the rotated image
        self._display_image()

        logger.debug(f"Rotated image: angle={angle}, total={self.rotation_angle}")

    def _on_resize(self, event):
        """Handle resize events."""
        # If we're maintaining aspect ratio, adjust the image when the widget resizes
        if self.keep_aspect and hasattr(self, 'pil_image') and self.pil_image:
            # Wait a bit to ensure the canvas has been resized
            self.after(100, self.fit_to_window)

    def _on_mouse_down(self, event):
        """Handle mouse button press event."""
        # Start dragging
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True

        # Change cursor
        self.canvas.configure(cursor="fleur")

    def _on_mouse_drag(self, event):
        """Handle mouse drag event."""
        if not self.drag_data["dragging"]:
            return

        # Calculate the distance moved
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]

        # Move the canvas view
        self.canvas.xview_scroll(-dx, "units")
        self.canvas.yview_scroll(-dy, "units")

        # Update the drag position
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_mouse_up(self, event):
        """Handle mouse button release event."""
        # End dragging
        self.drag_data["dragging"] = False

        # Restore cursor
        self.canvas.configure(cursor="")

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel event for zooming."""
        if not self.pil_image:
            return

        # Determine zoom direction and factor
        if event.num == 4 or event.delta > 0:
            # Zoom in
            self.zoom(1.1)
        elif event.num == 5 or event.delta < 0:
            # Zoom out
            self.zoom(0.9)

    def get_image(self) -> Optional[Image.Image]:
        """
        Get the current image.

        Returns:
            The current PIL Image or None if no image is loaded
        """
        return self.pil_image

    def save_image(self, filepath: str, format: Optional[str] = None) -> bool:
        """
        Save the current image to a file.

        Args:
            filepath: Path to save the image
            format: Optional image format (e.g., 'PNG', 'JPEG')

        Returns:
            True if saving was successful, False otherwise
        """
        if not self.pil_image:
            return False

        try:
            # Apply current rotation
            if self.rotation_angle:
                rotated_image = self.pil_image.rotate(
                    angle=self.rotation_angle,
                    expand=True,
                    resample=Image.BICUBIC
                )
            else:
                rotated_image = self.pil_image

            # Save the image
            rotated_image.save(filepath, format=format)

            logger.debug(f"Saved image to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving image to {filepath}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Image Viewer Demo")
    root.geometry("800x600")

    # Create a frame for the viewer
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


    # Create file browse button
    def open_image():
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.tiff;*.svg"),
                ("All files", "*.*")
            ],
            title="Open Image"
        )
        if filepath:
            viewer.load_image_from_file(filepath)


    browse_frame = ttk.Frame(root)
    browse_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    browse_button = ttk.Button(
        browse_frame,
        text="Open Image",
        command=open_image
    )
    browse_button.pack(side=tk.LEFT)

    # Create the image viewer with a default image
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_image = os.path.join(script_dir, "sample.png")

    # Try a sample image if it exists
    if os.path.exists(sample_image):
        viewer = ImageViewer(frame, image_path=sample_image)
    else:
        viewer = ImageViewer(frame)

    viewer.pack(fill=tk.BOTH, expand=True)

    root.mainloop()