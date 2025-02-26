# gui/leatherworking/cutting_layout.py
"""
Cutting layout module for leatherworking projects.
Helps optimize cutting patterns to minimize waste.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class LeatherPiece:
    """Represents a piece of leather with its dimensions and properties."""
    name: str
    width: float
    height: float
    grain_direction: bool = False  # True if grain direction matters


class LeatherCuttingView(BaseView):
    """Tool for creating and optimizing leather cutting layouts."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the leather cutting layout view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        logger.info("Initializing Leather Cutting Layout tool")

        # Initialize collections
        self.leather_pieces = []
        self.leather_size = {"width": 50, "height": 50}  # Default size in cm

        # Setup UI
        self._setup_layout()

        # Add some sample pieces for demonstration
        self._add_sample_pieces()

        logger.info("Leather Cutting Layout tool initialized")

    def _setup_layout(self):
        """Set up the main layout."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Leather Cutting Layout Tool", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Top controls panel
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Left controls for leather hide settings
        left_controls = ttk.LabelFrame(controls_frame, text="Leather Hide Settings")
        left_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Leather dimensions
        dim_frame = ttk.Frame(left_controls)
        dim_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dim_frame, text="Hide Width (cm):").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.DoubleVar(value=self.leather_size["width"])
        width_spin = ttk.Spinbox(dim_frame, from_=10, to=200, increment=5, textvariable=self.width_var, width=5)
        width_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(dim_frame, text="Hide Height (cm):").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.DoubleVar(value=self.leather_size["height"])
        height_spin = ttk.Spinbox(dim_frame, from_=10, to=200, increment=5, textvariable=self.height_var, width=5)
        height_spin.pack(side=tk.LEFT, padx=5)

        # Update button
        ttk.Button(left_controls, text="Update Hide Size", command=self._update_hide_size).pack(pady=5)

        # Right controls for piece addition
        right_controls = ttk.LabelFrame(controls_frame, text="Add Pattern Piece")
        right_controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Piece inputs
        piece_frame = ttk.Frame(right_controls)
        piece_frame.pack(fill=tk.X, pady=5)

        ttk.Label(piece_frame, text="Name:").pack(side=tk.LEFT, padx=5)
        self.piece_name_var = tk.StringVar()
        ttk.Entry(piece_frame, textvariable=self.piece_name_var, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Label(piece_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        self.piece_width_var = tk.DoubleVar(value=10)
        ttk.Spinbox(piece_frame, from_=1, to=100, increment=0.5, textvariable=self.piece_width_var, width=5).pack(
            side=tk.LEFT, padx=5)

        ttk.Label(piece_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        self.piece_height_var = tk.DoubleVar(value=5)
        ttk.Spinbox(piece_frame, from_=1, to=100, increment=0.5, textvariable=self.piece_height_var, width=5).pack(
            side=tk.LEFT, padx=5)

        grain_frame = ttk.Frame(right_controls)
        grain_frame.pack(fill=tk.X, pady=5)

        self.grain_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(grain_frame, text="Grain Direction Matters", variable=self.grain_var).pack(side=tk.LEFT, padx=5)

        # Add button
        ttk.Button(right_controls, text="Add Piece", command=self._add_piece).pack(pady=5)

        # Middle section - split into two panels
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left panel - Pieces list
        pieces_frame = ttk.LabelFrame(middle_frame, text="Pattern Pieces")
        pieces_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Pieces table
        pieces_columns = ("name", "width", "height", "grain", "area")
        self.pieces_tree = ttk.Treeview(pieces_frame, columns=pieces_columns, show="headings", selectmode="browse")

        self.pieces_tree.heading("name", text="Piece Name")
        self.pieces_tree.heading("width", text="Width (cm)")
        self.pieces_tree.heading("height", text="Height (cm)")
        self.pieces_tree.heading("grain", text="Grain Direction")
        self.pieces_tree.heading("area", text="Area (cm²)")

        self.pieces_tree.column("name", width=100)
        self.pieces_tree.column("width", width=80, anchor=tk.CENTER)
        self.pieces_tree.column("height", width=80, anchor=tk.CENTER)
        self.pieces_tree.column("grain", width=100, anchor=tk.CENTER)
        self.pieces_tree.column("area", width=80, anchor=tk.CENTER)

        pieces_scrollbar = ttk.Scrollbar(pieces_frame, orient=tk.VERTICAL, command=self.pieces_tree.yview)
        self.pieces_tree.configure(yscrollcommand=pieces_scrollbar.set)

        self.pieces_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pieces_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind delete key to remove piece
        self.pieces_tree.bind("<Delete>", lambda e: self._remove_selected_piece())

        # Right panel - Layout canvas
        canvas_frame = ttk.LabelFrame(middle_frame, text="Cutting Layout")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Canvas for drawing the layout
        self.canvas = tk.Canvas(canvas_frame, bg="white", bd=1, relief="solid")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom section - buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Optimize Layout", command=self._optimize_layout).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self._clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Layout", command=self._export_layout).pack(side=tk.RIGHT, padx=5)

        # Status information
        self.status_var = tk.StringVar(value="Ready. Add pieces and set hide dimensions.")
        ttk.Label(main_frame, textvariable=self.status_var, relief="sunken", anchor=tk.W).pack(fill=tk.X, pady=(10, 0))

    def _update_hide_size(self):
        """Update leather hide size and redraw the canvas."""
        try:
            width = self.width_var.get()
            height = self.height_var.get()

            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")

            self.leather_size["width"] = width
            self.leather_size["height"] = height

            self._draw_layout()

            self.status_var.set(f"Hide size updated to {width}cm × {height}cm")
            logger.info(f"Updated hide size to {width}cm × {height}cm")

        except Exception as e:
            logger.error(f"Error updating hide size: {str(e)}", exc_info=True)
            self.show_error("Input Error", f"Invalid dimensions: {str(e)}")

    def _add_piece(self):
        """Add a new pattern piece to the list."""
        try:
            name = self.piece_name_var.get().strip()
            width = self.piece_width_var.get()
            height = self.piece_height_var.get()
            grain = self.grain_var.get()

            if not name:
                raise ValueError("Piece name is required")

            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")

            # Create piece
            piece = LeatherPiece(name=name, width=width, height=height, grain_direction=grain)
            self.leather_pieces.append(piece)

            # Calculate area
            area = width * height

            # Add to treeview
            grain_text = "Yes" if grain else "No"
            self.pieces_tree.insert("", "end",
                                    values=(name, f"{width:.1f}", f"{height:.1f}", grain_text, f"{area:.1f}"))

            # Clear inputs
            self.piece_name_var.set("")

            # Redraw layout
            self._draw_layout()

            logger.info(f"Added piece: {name}, {width}cm × {height}cm")
            self.status_var.set(f"Added piece: {name}")

        except Exception as e:
            logger.error(f"Error adding piece: {str(e)}", exc_info=True)
            self.show_error("Input Error", f"Invalid piece data: {str(e)}")

    def _remove_selected_piece(self):
        """Remove the selected piece from the list."""
        selection = self.pieces_tree.selection()
        if not selection:
            return

        try:
            item_id = selection[0]
            index = self.pieces_tree.index(item_id)

            # Remove from treeview and list
            self.pieces_tree.delete(item_id)
            if 0 <= index < len(self.leather_pieces):
                del self.leather_pieces[index]

            # Redraw layout
            self._draw_layout()

            logger.info("Removed selected piece")
            self.status_var.set("Piece removed")

        except Exception as e:
            logger.error(f"Error removing piece: {str(e)}", exc_info=True)
            self.show_error("Error", f"Error removing piece: {str(e)}")

    def _draw_layout(self):
        """Draw the current layout on the canvas."""
        # Clear canvas
        self.canvas.delete("all")

        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet realized, wait for update
            self.after(100, self._draw_layout)
            return

        # Calculate scale factor to fit the hide
        scale_x = (canvas_width - 20) / self.leather_size["width"]
        scale_y = (canvas_height - 20) / self.leather_size["height"]
        scale = min(scale_x, scale_y)

        # Draw hide outline
        hide_width = self.leather_size["width"] * scale
        hide_height = self.leather_size["height"] * scale
        self.canvas.create_rectangle(
            10, 10, 10 + hide_width, 10 + hide_height,
            outline="black", width=2, fill="#d2b48c"  # Tan color for leather
        )

        # Draw grid lines (every 10cm)
        grid_spacing = 10 * scale
        for x in range(10, int(10 + hide_width) + 1, int(grid_spacing)):
            self.canvas.create_line(x, 10, x, 10 + hide_height, fill="#dddddd", dash=(2, 4))

        for y in range(10, int(10 + hide_height) + 1, int(grid_spacing)):
            self.canvas.create_line(10, y, 10 + hide_width, y, fill="#dddddd", dash=(2, 4))

        # If no pieces, just show the empty hide
        if not self.leather_pieces:
            # Draw text
            self.canvas.create_text(
                10 + hide_width / 2, 10 + hide_height / 2,
                text=f"Leather Hide\n{self.leather_size['width']}cm × {self.leather_size['height']}cm",
                font=("Helvetica", 12), justify="center", fill="#666666"
            )
            return

        # Simple layout algorithm - just pack pieces from left to right, top to bottom
        # This is a basic implementation that could be improved with a proper packing algorithm
        current_x = 10
        current_y = 10
        row_height = 0
        colors = ["#a52a2a", "#cd853f", "#8b4513", "#d2691e", "#b8860b", "#deb887"]  # Brown tones for pieces

        for i, piece in enumerate(self.leather_pieces):
            color = colors[i % len(colors)]
            piece_width = piece.width * scale
            piece_height = piece.height * scale

            # Check if piece fits in current row
            if current_x + piece_width > 10 + hide_width:
                # Move to next row
                current_x = 10
                current_y += row_height + 5
                row_height = 0

            # Check if piece fits vertically
            if current_y + piece_height > 10 + hide_height:
                # Can't fit any more pieces
                self.canvas.create_text(
                    current_x + 50, current_y + 20,
                    text="Not enough space for all pieces!",
                    font=("Helvetica", 10), fill="red"
                )
                break

            # Draw piece
            self.canvas.create_rectangle(
                current_x, current_y, current_x + piece_width, current_y + piece_height,
                outline="black", width=1, fill=color
            )

            # Draw piece label
            self.canvas.create_text(
                current_x + piece_width / 2, current_y + piece_height / 2,
                text=piece.name, font=("Helvetica", 8), fill="white"
            )

            # Draw dimensions
            dim_text = f"{piece.width}×{piece.height}"
            self.canvas.create_text(
                current_x + piece_width / 2, current_y + piece_height - 8,
                text=dim_text, font=("Helvetica", 7), fill="white"
            )

            # Draw grain direction indicator if needed
            if piece.grain_direction:
                # Draw arrow indicating grain direction
                arrow_y = current_y + 10
                self.canvas.create_line(
                    current_x + 10, arrow_y, current_x + piece_width - 10, arrow_y,
                    arrow="last", fill="white", width=2
                )

            # Update position and row height
            current_x += piece_width + 5
            row_height = max(row_height, piece_height)

        # Draw total area and utilization statistics
        total_area = sum(p.width * p.height for p in self.leather_pieces)
        hide_area = self.leather_size["width"] * self.leather_size["height"]
        utilization = (total_area / hide_area) * 100 if hide_area > 0 else 0

        self.canvas.create_text(
            10, 10 + hide_height + 10,
            text=f"Total Pieces: {len(self.leather_pieces)} | Pieces Area: {total_area:.1f} cm² | " +
                 f"Hide Area: {hide_area:.1f} cm² | Utilization: {utilization:.1f}%",
            font=("Helvetica", 9), anchor="w"
        )

    def _optimize_layout(self):
        """Optimize the cutting layout to minimize waste."""
        # This would implement a more sophisticated packing algorithm
        # For this implementation, we'll just sort pieces by size
        try:
            if not self.leather_pieces:
                messagebox.showinfo("Optimize", "No pieces to optimize.")
                return

            # Sort pieces by height (largest first)
            self.leather_pieces.sort(key=lambda p: p.height * p.width, reverse=True)

            # Update the treeview
            for item in self.pieces_tree.get_children():
                self.pieces_tree.delete(item)

            for piece in self.leather_pieces:
                area = piece.width * piece.height
                grain_text = "Yes" if piece.grain_direction else "No"
                self.pieces_tree.insert("", "end", values=(
                    piece.name, f"{piece.width:.1f}", f"{piece.height:.1f}",
                    grain_text, f"{area:.1f}"
                ))

            # Redraw the layout
            self._draw_layout()

            self.status_var.set("Layout optimized (sorted by size)")
            logger.info("Optimized layout")

        except Exception as e:
            logger.error(f"Error optimizing layout: {str(e)}", exc_info=True)
            self.show_error("Error", f"Failed to optimize layout: {str(e)}")

    def _export_layout(self):
        """Export the current layout."""
        # In a real implementation, this would save the layout to a file
        messagebox.showinfo("Export", "Layout export would be implemented here")
        logger.info("Layout export requested")

    def _clear_all(self):
        """Clear all pieces and reset the view."""
        # Confirm
        if messagebox.askyesno("Clear All", "Remove all pieces?"):
            # Clear treeview
            for item in self.pieces_tree.get_children():
                self.pieces_tree.delete(item)

            # Clear pieces list
            self.leather_pieces.clear()

            # Redraw layout
            self._draw_layout()

            self.status_var.set("All pieces cleared")
            logger.info("Cleared all pieces")

    def _add_sample_pieces(self):
        """Add some sample pieces for demonstration."""
        sample_pieces = [
            LeatherPiece("Wallet Front", 10, 8, False),
            LeatherPiece("Wallet Back", 10, 8, False),
            LeatherPiece("Card Pocket", 9, 6, True),
            LeatherPiece("Card Pocket", 9, 6, True),
            LeatherPiece("Card Pocket", 9, 6, True),
            LeatherPiece("Bill Pocket", 18, 8, True)
        ]

        for piece in sample_pieces:
            self.leather_pieces.append(piece)

            area = piece.width * piece.height
            grain_text = "Yes" if piece.grain_direction else "No"
            self.pieces_tree.insert("", "end", values=(
                piece.name, f"{piece.width:.1f}", f"{piece.height:.1f}",
                grain_text, f"{area:.1f}"
            ))

        # Initial draw
        self.after(100, self._draw_layout)

        logger.info("Added sample pieces")


class MockApp:
    """Mock application class for standalone testing."""

    def get_service(self, service_type):
        """Mock service getter.

        Args:
            service_type: The service interface to get

        Returns:
            None
        """
        return None


def main():
    """Main function for standalone testing."""
    root = tk.Tk()
    root.title("Leather Cutting Layout Tool")
    root.geometry("1000x800")

    app = MockApp()
    view = LeatherCuttingView(root, app)
    view.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()