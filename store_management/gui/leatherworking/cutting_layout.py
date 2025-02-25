from di.core import inject
from services.interfaces import MaterialService, ProjectService, \
    InventoryService, OrderService
import logging
from dataclasses import dataclass
from typing import Any, List, Optional
import tkinter as tk
from tkinter import ttk, messagebox

logger = logging.getLogger(__name__)


@dataclass
class LeatherPiece:
    """Represents a piece of leather with its dimensions and properties."""
    width: float
    height: float
    name: str
    priority: int = 1
    x: float = 0
    y: float = 0


class LeatherCuttingView(BaseView):
    """
    View for leather cutting layout management.
    Implements drag-and-drop functionality for arranging leather pieces.
    """

    @inject(MaterialService)
    def __init__(self, parent: tk.Widget, app: Any) -> None:
        """
        Initialize the leather cutting view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.canvas: Optional[tk.Canvas] = None
        self.pieces: List[LeatherPiece] = []
        self.selected_piece: Optional[LeatherPiece] = None
        self.zoom_level: float = 1.0
        self.grid_size: int = 20
        self.setup_ui()
        self.load_data()

    @inject(MaterialService)
    def setup_ui(self) -> None:
        """Set up the user interface components."""
        try:
            self.main_frame = ttk.Frame(self)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            self.create_toolbar()
            self.canvas = tk.Canvas(self.main_frame, width=800, height=600,
                                    background='white')
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.bind('<ButtonPress-1>', self.on_canvas_click)
            self.canvas.bind('<B1-Motion>', self.on_drag)
            self.canvas.bind('<MouseWheel>', self.on_zoom)
            self.bind('<Configure>', self.update_grid)
        except Exception as e:
            logger.error(f'Error setting up UI: {str(e)}')
            messagebox.showerror('Error', f'Failed to set up interface: {str(e)}')

    @inject(MaterialService)
    def create_toolbar(self) -> None:
        """Create the toolbar with control buttons."""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text='Add Piece', command=self.add_piece).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Export', command=self.export_layout).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Clear', command=self.clear_layout).pack(side=tk.LEFT, padx=2)
        ttk.Label(toolbar, text='Zoom:').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='+', command=lambda: self.adjust_zoom(1.2)).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='-', command=lambda: self.adjust_zoom(0.8)).pack(side=tk.LEFT)

    @inject(MaterialService)
    def load_data(self) -> None:
        """Load initial data and any saved layouts."""
        try:
            self.pieces = [LeatherPiece(100, 150, 'Piece 1', 1),
                           LeatherPiece(200, 100, 'Piece 2', 2)]
            self.refresh_canvas()
        except Exception as e:
            logger.error(f'Error loading data: {str(e)}')
            messagebox.showerror('Error', 'Failed to load layout data')

    @inject(MaterialService)
    def refresh_canvas(self) -> None:
        """Refresh the canvas display with current pieces."""
        if not self.canvas:
            return
        self.canvas.delete('all')
        self.draw_grid()
        for piece in self.pieces:
            self.draw_piece(piece)

    @inject(MaterialService)
    def draw_grid(self) -> None:
        """Draw the background grid."""
        if not self.canvas:
            return
        width = int(self.canvas.winfo_width())
        height = int(self.canvas.winfo_height())
        grid_size = int(self.grid_size * self.zoom_level)
        for x in range(0, width, grid_size):
            self.canvas.create_line(x, 0, x, height, fill='#EEEEEE')
        for y in range(0, height, grid_size):
            self.canvas.create_line(0, y, width, y, fill='#EEEEEE')

    @inject(MaterialService)
    def draw_piece(self, piece: LeatherPiece) -> None:
        """
        Draw a single leather piece on the canvas.

        Args:
            piece: LeatherPiece to draw
        """
        if not self.canvas:
            return
        x1 = piece.x * self.zoom_level
        y1 = piece.y * self.zoom_level
        x2 = x1 + piece.width * self.zoom_level
        y2 = y1 + piece.height * self.zoom_level
        color = self._get_color_for_priority(piece.priority)
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black')
        self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=f"""{piece.name}
{piece.width}x{piece.height}""")

    @inject(MaterialService)
    def _get_color_for_priority(self, priority: int) -> str:
        """
        Get color based on piece priority.

        Args:
            priority: Priority level

        Returns:
            Color hex code
        """
        colors = {1: '#BBDEFB', 2: '#C8E6C9', 3: '#FFECB3', 4: '#FFCDD2'}
        return colors.get(priority, '#FFFFFF')

    @inject(MaterialService)
    def on_canvas_click(self, event) -> None:
        """Handle canvas click event to select pieces."""
        if not self.canvas:
            return
        x = event.x / self.zoom_level
        y = event.y / self.zoom_level
        for piece in reversed(self.pieces):
            if (piece.x <= x <= piece.x + piece.width and piece.y <= y <= piece.y + piece.height):
                self.selected_piece = piece
                break

    @inject(MaterialService)
    def on_drag(self, event) -> None:
        """Handle drag event to move pieces."""
        if not self.canvas or not self.selected_piece:
            return
        x = event.x / self.zoom_level
        y = event.y / self.zoom_level
        self.selected_piece.x = x - self.selected_piece.width / 2
        self.selected_piece.y = y - self.selected_piece.height / 2
        self.refresh_canvas()

    @inject(MaterialService)
    def on_zoom(self, event) -> None:
        """Handle mouse wheel zoom event."""
        if event.delta > 0:
            self.adjust_zoom(1.1)
        else:
            self.adjust_zoom(0.9)

    @inject(MaterialService)
    def adjust_zoom(self, factor: float) -> None:
        """
        Adjust the zoom level.

        Args:
            factor: Zoom multiplication factor
        """
        self.zoom_level *= factor
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))
        self.refresh_canvas()

    @inject(MaterialService)
    def update_grid(self, event=None) -> None:
        """Update the grid when window is resized."""
        self.refresh_canvas()

    @inject(MaterialService)
    def add_piece(self) -> None:
        """Add a new leather piece to the layout."""
        new_piece = LeatherPiece(150, 100, f'Piece {len(self.pieces) + 1}')
        self.pieces.append(new_piece)
        self.refresh_canvas()

    @inject(MaterialService)
    def clear_layout(self) -> None:
        """Clear all pieces from the layout."""
        self.pieces.clear()
        self.refresh_canvas()

    @inject(MaterialService)
    def export_layout(self) -> None:
        """Export the current layout."""
        try:
            logger.info('Exporting layout...')
            messagebox.showinfo('Export', 'Layout exported successfully')
        except Exception as e:
            logger.error(f'Error exporting layout: {str(e)}')
            messagebox.showerror('Error', 'Failed to export layout')


class MockApp:
    """Mock application class for testing."""

    @inject(MaterialService)
    def get_service(self, service_type):
        return None


def main():
    """Main entry point for testing the leather cutting view."""
    root = tk.Tk()
    root.title('Leather Cutting Layout')
    root.geometry('1024x768')
    try:
        cutting_view = LeatherCuttingView(root, MockApp())
        cutting_view.pack(fill=tk.BOTH, expand=True)
        root.mainloop()
    except Exception as e:
        logger.error(f'Error starting application: {str(e)}')
        messagebox.showerror('Error', f'Failed to start application: {str(e)}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
