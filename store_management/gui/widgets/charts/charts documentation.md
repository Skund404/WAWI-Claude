Okay, here's the requested documentation in the defined style.

**I. `gui.widgets.charts.bar_chart`**

*   **Module Name:** `gui.widgets.charts.bar_chart`
*   **Description:** Provides a simple bar chart component for data visualization, displays data in vertical bars.

*   **Key Features:**
    *   **Data visualization** Displays data to bar
    *   **Customizable properties:** Title, width, height and labels
    *   **ShowValues and animate** Shows the values on the bar and animation rendering
*   **Classes:**

    *   `BarChart(ttk.Frame)`:

        *   `__init__(self, parent,data: List[Dict[str, Any]],x_key: str = "label",y_key: str = "value",title: str = "Bar Chart",width: int = 600,height: int = 400,x_label: str = "",y_label: str = "",color: str = COLORS["primary"],bar_width: int = 40,spacing: int = 20,show_values: bool = True,show_grid: bool = True,animate: bool = True,**kwargs)`: Initializes the barchart components

            *`parent`: The parent widget
            *`data`: List of dictionaries with chart data
            *`x_key`: Key in data dictionaries for x-axis labels
            *`y_key`: Key in data dictionaries for y-axis values
            *`title`: Chart title
            *`width`: Chart width
            *`height`: Chart height
            *`x_label`: X-axis label
            *`y_label`: Y-axis label
            *`color`: Bar color
            *`bar_width`: Width of bars
            *`spacing`: Space between bars
            *`show_values`: Whether to show values above bars
            *`show_grid`: Whether to show grid lines
            *`animate`: Whether to animate the chart on initial display

        *   `render(self)`: Renders the chart with the current data
        *    `update_data(self, data: List[Dict[str, Any]])`: Updates the new data and refreshes the chart

            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.charts.bar_chart import BarChart

            # Example Chart Data
            chart_data = [
                {"label": "Leather", "value": 120},
                {"label": "Textiles", "value": 80},
                {"label": "Hardware", "value": 50},
                {"label": "Supplies", "value": 70},
            ]

            class BarChartData:
               def __init__(self, master):
                    # Set master root window
                   self.master = master
                   # label to explain the chart
                   ttk.Label(master, text="Bar Frame", background="white").pack()

                   barData = BarChart(master, chart_data)
                   barData.pack()
            class MainApp(tk.Tk):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.geometry("800x600")

                    bar_data = BarChartData(self)
                    bar_data.pack(expand=True, fill="both", padx=20, pady=20)
            if __name__ == "__main__":
                root = MainApp()
                root.mainloop()
            ```

**II. `gui.widgets.charts.heatmap`**

*   **Module Name:** `gui.widgets.charts.heatmap`
*   **Description:** Customizable heatmap chart for visualizing tabular data.

*   **Key Features:**
    *   **Colours customization** You can customize colours based on their magnitudes
    *   **ToolTip support** Allows the showToolTip for magnitudes values and cell
*   **Classes:**

    *   `HeatmapChart(ttk.Frame)`:
        *   `__init__(self, parent,data: Optional[List[Dict[str, Any]]] = None,title: str = "Heatmap Chart",x_label: str = "X Axis",y_label: str = "Y Axis",x_key: str = "x",y_key: str = "y",value_key: str = "value",width: int = 500,height: int = 400,cell_width: int = 40,cell_height: int = 30,color_min: str = COLORS["light_blue"],color_max: str = COLORS["dark_blue"],**kwargs)`: Initalizes a new HeatMapFrame

            *`parent`: The parent widget
            *`data`: List of data points
            *`title`: Chart title
            *`x_label`: X-axis label
            *`y_label`: Y-axis label
            *`x_key`: Data key for x values
            *`y_key`: Data key for y values
            *`value_key`: Data key for cell values
            *`width`: Chart width
            *`height`: Chart height
            *`cell_width`: Width of heatmap cells
            *`cell_height`: Height of heatmap cells
            *`color_min`: Color for minimum values
            *`color_max`: Color for maximum values
        *   `render(self)`: Renders the chart with the current data
        *   `update_data(self, data: List[Dict[str, Any]])`: Updates the new data and renders
            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.charts.heatmap import HeatmapChart
            # Sample Data
            heatmap_data = [
                {"x": "Mon", "y": "Morning", "value": 10},
                {"x": "Mon", "y": "Afternoon", "value": 15},
                {"x": "Tue", "y": "Morning", "value": 12},
                {"x": "Tue", "y": "Afternoon", "value": 8},
                {"x": "Wed", "y": "Morning", "value": 20},
                {"x": "Wed", "y": "Afternoon", "value": 25},
            ]
            class ViewChart:
                def __init__(self, master):
                    # Sets master root to master
                    self.master = master
                    # label Frame
                    ttk.Label(master, text="Heat Map Frame").pack()
                    # Adds New Frame
                    newFrame = HeatmapChart(master, heatmap_data)
                    newFrame.pack()
            class MainApp(tk.Tk):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.geometry("800x600")

                    chart_view = ViewChart(self)
                    chart_view.pack(expand=True, fill="both", padx=20, pady=20)
            if __name__ == "__main__":
                root = MainApp()
                root.mainloop()
            ```

**III. `gui.widgets.charts.line_chart`**

*   **Module Name:** `gui.widgets.charts.line_chart`
*   **Description:** Provides a line chart component for visualizing trend data over time

*   **Key Features:**
    *   **Visualization TrendData** Visualizes the given trendData
    *   **Markers** Added the marker or remove the marker for points
    *   **Customization for Chart** It comes with the wide variety of colours and customizable
*   **Classes:**

    *   `LineChart(ttk.Frame)`:
        * `__init__( self,parent,data: List[Dict[str, Any]],x_key: str = "period",y_key: str = "value",title: str = "Line Chart",width: int = 600,height: int = 400,x_label: str = "",y_label: str = "",line_color: str = COLORS["primary"],line_width: int = 2,marker_size: int = 5,show_markers: bool = True,show_area: bool = False,area_color: Optional[str] = None,show_values: bool = False,show_grid: bool = True,animate: bool = True,**kwargs)`: Initializes the new class

            *`parent`: The parent widget
            *`data`: List of dictionaries with chart data
            *`x_key`: Key in data dictionaries for x-axis labels
            *`y_key`: Key in data dictionaries for y-axis values
            *`title`: Chart title
            *`width`: Chart width
            *`height`: Chart height
            *`x_label`: X-axis label
            *`y_label`: Y-axis label
            *`line_color`: Line color
            *`line_width`: Line width
            *`marker_size`: Size of data point markers
            *`show_markers`: Whether to show data point markers
            *`show_area`: Whether to fill the area under the line
            *`area_color`: Color for the area under the line (or None to use transparent line_color)
            *`show_values`: Whether to show values at data points
            *`show_grid`: Whether to show grid lines
            *`animate`: Whether to animate the chart on initial display
        *   `render(self)`: Renders the current Data
        *   `update_data(self, data: List[Dict[str, Any]])`: Update the data and refresh Chart

            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.charts.line_chart import LineChart
            # Sample data
            line_data = [
                {"period": "Jan", "value": 50},
                {"period": "Feb", "value": 60},
                {"period": "Mar", "value": 80},
                {"period": "Apr", "value": 70},
                {"period": "May", "value": 90},
            ]
            class ViewChart:
                def __init__(self, master):
                    # Sets master root to master
                    self.master = master
                    # label Frame
                    ttk.Label(master, text="Line Chart Frame").pack()
                    # Adds New Frame
                    newFrame = LineChart(master, line_data)
                    newFrame.pack()

            class MainApp(tk.Tk):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.geometry("800x600")

                    chart_view = ViewChart(self)
                    chart_view.pack(expand=True, fill="both", padx=20, pady=20)

            # call to MainApp
            if __name__ == "__main__":
                root = MainApp()
                root.mainloop()

            ```

**IV. `gui.widgets.charts.pie_chart`**

*   **Module Name:** `gui.widgets.charts.pie_chart`
*   **Description:** Pie chart widget for displaying category distributions.

*   **Key Features:**
    *   **Customizable Segments :** Enables the segments on a chart to display chart with animation

*   **Classes:**
    *  `PieChart(ttk.Frame)`
        *`PieChart(ttk.Frame)`:`__init__(self, parent,data: List[Dict[str, Any]],label_key: str = "label",value_key: str = "value",title: str = "Pie Chart",width: int = 400,height: int = 400,colors: Optional[List[str]] = None,show_labels: bool = True,show_percentages: bool = True,show_legend: bool = True,donut: bool = False,animate: bool = True,**kwargs)`:

            *`parent`: The parent widget
            *`data`: List of dictionaries with chart data
            *`label_key`: Key in data dictionaries for segment labels
            *`value_key`: Key in data dictionaries for segment values
            *`title`: Chart title
            *`width`: Chart width
            *`height`: Chart height
            *`colors`: List of colors for segments (defaults to theme colors)
            *`show_labels`: Whether to show labels on chart segments
            *`show_percentages`: Whether to show percentages on chart segments
            *`show_legend`: Whether to show a legend
            *`donut`: Whether to create a donut chart
            *`animate`: Whether to animate the chart on initial display
        *   `render(self)`: Renders and creates the pie chart with data given

        *   `update_data(self, data: List[Dict[str, Any]])`: Update the new data with chart

            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.charts.pie_chart import PieChart
            chart_data = [
              {"label": "Leather", "value": 40},
              {"label": "Textiles", "value": 30},
              {"label": "Hardware", "value": 20},
              {"label": "Supplies", "value": 10},
            ]
            class ViewChart:
                def __init__(self, master):
                    # Sets master root to master
                    self.master = master
                    # label Frame
                    ttk.Label(master, text="Pie Chart Frame").pack()
                    # Adds New Frame
                    newFrame = PieChart(master, chart_data)
                    newFrame.pack()
            class MainApp(tk.Tk):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.geometry("800x600")
                    chart_view = ViewChart(self)
                    chart_view.pack(expand=True, fill="both", padx=20, pady=20)
            if __name__ == "__main__":
                root = MainApp()
                root.mainloop()

            ```

These chart widgets are now comprehensively documented, including example usage, following the established style.