# gui/leatherworking/cutting_layout.py
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService


@dataclass
class LeatherPiece:
    """Represents a piece of leather with its dimensions and properties."""
    id: int
    name: str
    width: float
    height: float
    rotation_allowed: bool = True
    x: float = 0.0
    y: float = 0.0
    color: str = "#A0522D"  # Default brown color


class LeatherCuttingView(BaseView):
    """
    Interactive leather cutting layout tool.

    This view allows users to:
    - Define the dimensions of a leather hide
    - Add pattern pieces with specific dimensions
    - Visualize the optimal cutting layout
    - Calculate material utilization and waste
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the leather cutting layout view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.hide_width = 100.0  # cm
        self.hide_height = 60.0  # cm
        self.pieces = []
        self.next_id = 1
        self.selected_piece = None
        self.drag_data = {"x": 0, "y": 0, "item": None}

        self._setup_layout()
        self._add_sample_pieces()

    def set_status(self, message: str):
        """Set the status message in the application."""
        # Assuming you have a status label in your UI to display messages
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        else:
            logging.info(message)  # Fallback to logging if no status label exists

    def _setup_layout(self):
        """Set up the main layout."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="Leather Cutting Layout",
                  font=("TkDefaultFont", 14, "bold")).pack(side=tk.LEFT)

        # Split into two panels - left for controls, right for canvas
        content_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left control panel
        control_panel = ttk.Frame(content_frame)

        # Hide size settings
        hide_frame = ttk.LabelFrame(control_panel, text="Leather Hide Size")
        hide_frame.pack(fill=tk.X, padx=5, pady=5)

        hide_grid = ttk.Frame(hide_frame)
        hide_grid.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(hide_grid, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.hide_width_var = tk.DoubleVar(value=self.hide_width)
        ttk.Spinbox(hide_grid, from_=10, to=500, increment=5, textvariable=self.hide_width_var,
                    width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(hide_grid, text="Height:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.hide_height_var = tk.DoubleVar(value=self.hide_height)
        ttk.Spinbox(hide_grid, from_=10, to=500, increment=5, textvariable=self.hide_height_var,
                    width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(hide_grid, text="cm").grid(row=0, column=2, sticky=tk.W)
        ttk.Label(hide_grid, text="cm").grid(row=1, column=2, sticky=tk.W)

        ttk.Button(hide_grid, text="Update", command=self._update_hide_size).grid(
            row=2, column=0, columnspan=3, pady=5)

        # Piece controls
        pieces_frame = ttk.LabelFrame(control_panel, text="Pattern Pieces")
        pieces_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        pieces_grid = ttk.Frame(pieces_frame)
        pieces_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Piece input fields
        ttk.Label(pieces_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece_name_var = tk.StringVar()
        ttk.Entry(pieces_grid, textvariable=self.piece_name_var, width=20).grid(
            row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(pieces_grid, text="Width:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece_width_var = tk.DoubleVar(value=10.0)
        ttk.Spinbox(pieces_grid, from_=1, to=200, increment=0.5, textvariable=self.piece_width_var,
                    width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(pieces_grid, text="cm").grid(row=1, column=2, sticky=tk.W)

        ttk.Label(pieces_grid, text="Height:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece_height_var = tk.DoubleVar(value=10.0)
        ttk.Spinbox(pieces_grid, from_=1, to=200, increment=0.5, textvariable=self.piece_height_var,
                    width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(pieces_grid, text="cm").grid(row=2, column=2, sticky=tk.W)

        self.rotation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(pieces_grid, text="Allow rotation", variable=self.rotation_var).grid(
            row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Piece buttons
        buttons_frame = ttk.Frame(pieces_grid)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=5)

        ttk.Button(buttons_frame, text="Add Piece", command=self._add_piece).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="Remove Selected", command=self._remove_selected_piece).pack(side=tk.LEFT,
                                                                                                    padx=2)

        # Piece list
        ttk.Label(pieces_grid, text="Pieces:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)

        # Create listbox with scrollbar
        list_frame = ttk.Frame(pieces_grid)
        list_frame.grid(row=6, column=0, columnspan=3, sticky=tk.NSEW, padx=5, pady=5)

        self.pieces_listbox = tk.Listbox(list_frame, height=10)
        self.pieces_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.pieces_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pieces_listbox.configure(yscrollcommand=scrollbar.set)

        # Make the listbox items expand if the window is resized
        pieces_grid.columnconfigure(1, weight=1)
        pieces_grid.rowconfigure(6, weight=1)

        # Layout actions
        actions_frame = ttk.Frame(control_panel)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(actions_frame, text="Optimize Layout", command=self._optimize_layout).pack(
            fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Export Layout", command=self._export_layout).pack(
            fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="Clear All", command=self._clear_all).pack(
            fill=tk.X, pady=2)

        # Add control panel to the PanedWindow
        content_frame.add(control_panel, weight=1)

        # Right side with canvas for layout view
        canvas_frame = ttk.Frame(content_frame)

        # Canvas and stats
        stats_frame = ttk.Frame(canvas_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(stats_frame, text="Material utilization:").pack(side=tk.LEFT, padx=5)
        self.utilization_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_frame, textvariable=self.utilization_var, font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.LEFT, padx=5)

        ttk.Label(stats_frame, text="Waste:").pack(side=tk.LEFT, padx=5)
        self.waste_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_frame, textvariable=self.waste_var, font=("TkDefaultFont", 10, "bold")).pack(
            side=tk.LEFT, padx=5)

        # Canvas for drawing the layout
        self.canvas_frame = ttk.LabelFrame(canvas_frame, text="Layout View")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas bindings for drag and select
        self.canvas.tag_bind("piece", "<ButtonPress-1>", self._on_piece_select)
        self.canvas.tag_bind("piece", "<B1-Motion>", self._on_piece_drag)
        self.canvas.tag_bind("piece", "<ButtonRelease-1>", self._on_piece_drop)

        # Add canvas frame to the PanedWindow
        content_frame.add(canvas_frame, weight=2)

        # Draw initial layout
        self._draw_layout()

    def _update_hide_size(self):
        """Update leather hide size and redraw the canvas."""
        try:
            self.hide_width = self.hide_width_var.get()
            self.hide_height = self.hide_height_var.get()

            # Validate
            if self.hide_width <= 0 or self.hide_height <= 0:
                messagebox.showwarning("Invalid Size", "Width and height must be greater than zero.")
                return

            self._draw_layout()
            self.set_status(f"Hide size updated to {self.hide_width} x {self.hide_height} cm")
        except Exception as e:
            logging.error(f"Error updating hide size: {e}")
            messagebox.showerror("Error", f"Failed to update hide size: {e}")

    def _add_piece(self):
        """Add a new pattern piece to the list."""
        try:
            name = self.piece_name_var.get()
            if not name:
                name = f"Piece {self.next_id}"

            width = self.piece_width_var.get()
            height = self.piece_height_var.get()

            # Validate
            if width <= 0 or height <= 0:
                messagebox.showwarning("Invalid Size", "Width and height must be greater than zero.")
                return

            if width > self.hide_width and height > self.hide_height:
                messagebox.showwarning("Piece Too Large",
                                       "Piece dimensions exceed hide size in both directions.")
                return

            rotation_allowed = self.rotation_var.get()

            # Create the piece with random but visually distinct color
            colors = ["#A0522D", "#8B4513", "#CD853F", "#D2691E", "#B8860B", "#BC8F8F"]
            import random
            color = colors[self.next_id % len(colors)]

            # Create piece
            piece = LeatherPiece(
                id=self.next_id,
                name=name,
                width=width,
                height=height,
                rotation_allowed=rotation_allowed,
                color=color
            )

            self.pieces.append(piece)
            self.next_id += 1

            # Update listbox
            self.pieces_listbox.insert(tk.END, f"{piece.name} ({piece.width} x {piece.height} cm)")

            # Redraw
            self._draw_layout()
            self.set_status(f"Added piece: {name}")

            # Clear inputs
            self.piece_name_var.set("")

        except Exception as e:
            logging.error(f"Error adding piece: {e}")
            messagebox.showerror("Error", f"Failed to add piece: {e}")

    def _remove_selected_piece(self):
        """Remove the selected piece from the list."""
        try:
            selection = self.pieces_listbox.curselection()
            if not selection:
                # Try to use canvas selection if listbox has no selection
                if self.selected_piece is not None:
                    idx = next((i for i, p in enumerate(self.pieces) if p.id == self.selected_piece), None)
                    if idx is not None:
                        self.pieces.pop(idx)
                        self.pieces_listbox.delete(idx)
                        self.selected_piece = None
                        self._draw_layout()
                        self.set_status("Piece removed")
                return

            # Get the selected index
            idx = selection[0]

            # Get piece before deleting
            piece = self.pieces[idx]

            # Remove piece
            self.pieces.pop(idx)
            self.pieces_listbox.delete(idx)

            # If removed piece was selected, clear selection
            if self.selected_piece == piece.id:
                self.selected_piece = None

            # Redraw
            self._draw_layout()
            self.set_status(f"Removed piece: {piece.name}")

        except Exception as e:
            logging.error(f"Error removing piece: {e}")
            messagebox.showerror("Error", f"Failed to remove piece: {e}")

    def _draw_layout(self):
        """Draw the current layout on the canvas."""
        try:
            # Clear canvas
            self.canvas.delete("all")

            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Min size for initial render
            if canvas_width < 50:
                canvas_width = 500
            if canvas_height < 50:
                canvas_height = 400

            # Calculate scale factor
            scale_x = (canvas_width - 20) / self.hide_width
            scale_y = (canvas_height - 20) / self.hide_height
            scale = min(scale_x, scale_y)

            # Draw leather hide
            hide_width_px = self.hide_width * scale
            hide_height_px = self.hide_height * scale

            # Center the hide on the canvas
            x_offset = (canvas_width - hide_width_px) / 2
            y_offset = (canvas_height - hide_height_px) / 2

            # Draw the hide with a leather-like texture
            self.canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + hide_width_px, y_offset + hide_height_px,
                fill="#D2B48C", outline="#8B4513", width=2, tags="hide"
            )

            # Create a stipple pattern to simulate leather texture
            for i in range(100):
                import random
                dot_x = x_offset + random.uniform(0, hide_width_px)
                dot_y = y_offset + random.uniform(0, hide_height_px)
                dot_size = random.uniform(1, 3)
                dot_color = random.choice(["#8B4513", "#A0522D", "#CD853F"])

                self.canvas.create_oval(
                    dot_x - dot_size, dot_y - dot_size,
                    dot_x + dot_size, dot_y + dot_size,
                    fill=dot_color, outline="", tags="texture"
                )

            # Draw grid lines (every 10cm)
            for x in range(0, int(self.hide_width) + 10, 10):
                if x > 0 and x < self.hide_width:
                    x_px = x_offset + x * scale
                    self.canvas.create_line(
                        x_px, y_offset, x_px, y_offset + hide_height_px,
                        fill="#CCCCCC", dash=(2, 4), tags="grid"
                    )

            for y in range(0, int(self.hide_height) + 10, 10):
                if y > 0 and y < self.hide_height:
                    y_px = y_offset + y * scale
                    self.canvas.create_line(
                        x_offset, y_px, x_offset + hide_width_px, y_px,
                        fill="#CCCCCC", dash=(2, 4), tags="grid"
                    )

            # Calculate utilization
            total_area = self.hide_width * self.hide_height
            used_area = sum(p.width * p.height for p in self.pieces)
            utilization = min(used_area / total_area * 100, 100) if total_area > 0 else 0
            waste = 100 - utilization

            self.utilization_var.set(f"{utilization:.1f}%")
            self.waste_var.set(f"{waste:.1f}%")

            # Draw pieces
            for piece in self.pieces:
                # Convert piece coordinates to canvas pixels
                x1 = x_offset + piece.x * scale
                y1 = y_offset + piece.y * scale
                x2 = x1 + piece.width * scale
                y2 = y1 + piece.height * scale

                # Draw the piece
                outline_width = 2
                if self.selected_piece == piece.id:
                    outline_width = 3

                piece_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=piece.color, outline="black",
                    width=outline_width, tags=("piece", f"piece_{piece.id}")
                )

                # Add text label
                self.canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=f"{piece.name}\n{piece.width}x{piece.height}",
                    fill="white", font=("TkDefaultFont", 8), tags=("label", f"label_{piece.id}")
                )

                # Check if piece extends beyond the hide boundaries
                if (piece.x < 0 or
                        piece.y < 0 or
                        piece.x + piece.width > self.hide_width or
                        piece.y + piece.height > self.hide_height):
                    # Highlight the piece as out of bounds
                    self.canvas.itemconfig(piece_id, outline="red", width=3)

        except Exception as e:
            logging.error(f"Error drawing layout: {e}")
            messagebox.showerror("Error", f"Failed to draw layout: {e}")

    def _on_piece_select(self, event):
        """Handle piece selection on the canvas."""
        try:
            # Get canvas item under mouse
            item = event.widget.find_withtag("current")[0]
            tags = self.canvas.gettags(item)

            # Extract piece ID
            for tag in tags:
                if tag.startswith("piece_"):
                    piece_id = int(tag.split("_")[1])
                    self.selected_piece = piece_id

                    # Save starting position for drag
                    self.drag_data["item"] = item
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y

                    # Highlight selected piece in listbox
                    for i, piece in enumerate(self.pieces):
                        if piece.id == piece_id:
                            self.pieces_listbox.selection_clear(0, tk.END)
                            self.pieces_listbox.selection_set(i)
                            self.pieces_listbox.see(i)
                            break

                    # Redraw to update selection
                    self._draw_layout()
                    break

        except Exception as e:
            logging.error(f"Error selecting piece: {e}")

    def _on_piece_drag(self, event):
        """Handle dragging a piece on the canvas."""
        try:
            # Calculate the movement delta
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            # Skip if there's no movement
            if dx == 0 and dy == 0:
                return

            # Update drag data
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate scale factor
            scale_x = (canvas_width - 20) / self.hide_width
            scale_y = (canvas_height - 20) / self.hide_height
            scale = min(scale_x, scale_y)

            # Adjust for scale
            dx_cm = dx / scale
            dy_cm = dy / scale

            # Update piece position
            for piece in self.pieces:
                if piece.id == self.selected_piece:
                    piece.x += dx_cm
                    piece.y += dy_cm
                    break

            # Redraw
            self._draw_layout()

        except Exception as e:
            logging.error(f"Error dragging piece: {e}")

    def _on_piece_drop(self, event):
        """Handle dropping a piece after drag."""
        # Just need to redraw to ensure pieces align with grid if enabled
        self._draw_layout()

    def _optimize_layout(self):
        """Optimize the cutting layout to minimize waste."""
        if not self.pieces:
            messagebox.showinfo("Layout", "No pieces to optimize. Add pieces first.")
            return

        try:
            # Very simple algorithm: bin packing with next-fit decreasing
            # More advanced algorithms would be better here

            # Sort pieces by height descending
            sorted_pieces = sorted(self.pieces, key=lambda p: p.height, reverse=True)

            # Reset positions
            for piece in sorted_pieces:
                piece.x = 0
                piece.y = 0

            # Current position
            curr_x = 0
            curr_y = 0
            row_height = 0

            # Place pieces
            for piece in sorted_pieces:
                # If piece would extend beyond hide width, move to next row
                if curr_x + piece.width > self.hide_width:
                    curr_x = 0
                    curr_y += row_height
                    row_height = 0

                # Set piece position
                piece.x = curr_x
                piece.y = curr_y

                # Update position for next piece
                curr_x += piece.width
                row_height = max(row_height, piece.height)

            # Check if any pieces are outside the hide
            out_of_bounds = any(
                p.x < 0 or p.y < 0 or
                p.x + p.width > self.hide_width or
                p.y + p.height > self.hide_height
                for p in self.pieces
            )

            if out_of_bounds:
                messagebox.showwarning(
                    "Layout Warning",
                    "Some pieces extend beyond the hide boundaries. Consider using a larger hide."
                )

            # Redraw
            self._draw_layout()
            self.set_status("Layout optimized")

        except Exception as e:
            logging.error(f"Error optimizing layout: {e}")
            messagebox.showerror("Error", f"Failed to optimize layout: {e}")

    def _export_layout(self):
        """Export the current layout."""
        try:
            # In a full implementation, this would save to a file
            # For now, we just display a summary

            if not self.pieces:
                messagebox.showinfo("Export", "No pieces to export.")
                return

            # Create summary text
            total_area = self.hide_width * self.hide_height
            used_area = sum(p.width * p.height for p in self.pieces)
            utilization = min(used_area / total_area * 100, 100) if total_area > 0 else 0

            summary = (
                f"Leather Cutting Layout Summary\n"
                f"==============================\n\n"
                f"Hide Dimensions: {self.hide_width} x {self.hide_height} cm\n"
                f"Total Area: {total_area:.2f} sq cm\n"
                f"Used Area: {used_area:.2f} sq cm\n"
                f"Utilization: {utilization:.1f}%\n\n"
                f"Pieces:\n"
            )

            for p in self.pieces:
                summary += f"- {p.name}: {p.width} x {p.height} cm at position ({p.x:.1f}, {p.y:.1f})\n"

            # Show in a dialog
            top = tk.Toplevel(self)
            top.title("Layout Export")
            top.geometry("500x400")

            text = tk.Text(top, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text.insert("1.0", summary)
            text.config(state="disabled")

            ttk.Button(top, text="Close", command=top.destroy).pack(pady=10)

            self.set_status("Layout exported")

        except Exception as e:
            logging.error(f"Error exporting layout: {e}")
            messagebox.showerror("Error", f"Failed to export layout: {e}")

    def _clear_all(self):
        """Clear all pieces and reset the view."""
        if not self.pieces:
            return

        confirm = messagebox.askyesno("Confirm Clear", "Are you sure you want to remove all pieces?")
        if not confirm:
            return

        self.pieces = []
        self.next_id = 1
        self.selected_piece = None
        self.pieces_listbox.delete(0, tk.END)
        self._draw_layout()
        self.set_status("All pieces cleared")

    def _add_sample_pieces(self):
        """Add some sample pieces for demonstration."""
        # Only add samples if no pieces exist
        if self.pieces:
            return

        samples = [
            {"name": "Front Panel", "width": 25.0, "height": 20.0, "color": "#A0522D"},
            {"name": "Back Panel", "width": 25.0, "height": 20.0, "color": "#8B4513"},
            {"name": "Side Gusset", "width": 8.0, "height": 20.0, "color": "#CD853F"},
            {"name": "Bottom", "width": 25.0, "height": 8.0, "color": "#D2691E"},
            {"name": "Strap", "width": 40.0, "height": 5.0, "color": "#B8860B"},
            {"name": "Pocket", "width": 15.0, "height": 10.0, "color": "#BC8F8F"}
        ]

        for sample in samples:
            piece = LeatherPiece(
                id=self.next_id,
                name=sample["name"],
                width=sample["width"],
                height=sample["height"],
                color=sample["color"]
            )
            self.pieces.append(piece)
            self.pieces_listbox.insert(tk.END, f"{piece.name} ({piece.width} x {piece.height} cm)")
            self.next_id += 1

        # Optimize initial layout for better first impression
        self._optimize_layout()

    class MockApp:
        """Mock application for standalone testing."""

        def get_service(self, service_type):
            """
            Mock service getter.

            Args:
                service_type: The service interface to get

            Returns:
                None
            """
            return None


def main():
    """Main function for standalone testing."""
    root = tk.Tk()
    root.title("Leather Cutting Layout")
    root.geometry("1000x700")

    app = LeatherCuttingView.MockApp()
    layout_view = LeatherCuttingView(root, app)
    layout_view.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
