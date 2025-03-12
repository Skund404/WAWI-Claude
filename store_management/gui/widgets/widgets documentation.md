Okay, here's the documentation for the remaining GUI widgets (`enhanced_treeview`, `breadcrumb_navigation`, `search_frame`, `enum_combobox`, and `status_badge`), presented in a consistent style.

**I. `gui.widgets.enhanced_treeview`**

*   **Module Name:** `gui.widgets.enhanced_treeview`
*   **Description:** Enhances the standard `ttk.Treeview` widget with sorting, filtering, improved interaction, and status-based styling. It provides a more feature-rich and customizable list display for GUI applications.

*   **Key Features:**

    *   **Column Sorting:** Enables sorting by clicking on column headers.
    *   **Row Highlighting:**  Provides alternating row colors for improved readability.
    *   **Selection Tracking:** Triggers a callback when an item is selected.
    *   **Double-Click Handling:**  Triggers a callback when an item is double-clicked.
    *   **Status-Based Styling:** Applies different styles to rows based on status values in a designated column.
    *   **Scrollbars:** Includes vertical and horizontal scrollbars when the content exceeds the widget size.

*   **Classes:**

    *   `EnhancedTreeview(ttk.Treeview)`: Extends the standard `ttk.Treeview`.

        *   `__init__(self, parent, columns: List[str], on_sort: Optional[Callable[[str, str], None]] = None, on_select: Optional[Callable[[], None]] = None, on_double_click: Optional[Callable[[], None]] = None, status_column: Optional[str] = None, **kwargs)`: Initializes the enhanced treeview.

            *   `parent`: The parent widget.
            *   `columns`: A list of column identifiers (strings).
            *   `on_sort`: An optional callback function called when a column is sorted. It receives the column identifier and sort direction ("asc" or "desc").
            *   `on_select`: An optional callback function called when an item is selected.
            *   `on_double_click`: An optional callback function called when an item is double-clicked.
            *   `status_column`: An optional column identifier that indicates which column contains status values for styling.
            *   `**kwargs`: Additional keyword arguments passed to the `ttk.Treeview` constructor.

        *   `insert_item(self, item_id, values)`: Inserts an item into the treeview with proper styling (alternating row colors and status-based tags).

            *   `item_id`: The unique identifier for the item.
            *   `values`: A list of values for the item's columns.

        *   `clear(self)`: Clears all items from the treeview.
        *   `set_column_widths(self, widths)`: Sets the width of columns.
            ```python
            from gui.widgets.enhanced_treeview import EnhancedTreeview
            # Define column headers
            columns = ("id", "name", "category")

            class MyView:
              # Create new tree with column
              enhanced_tree = EnhancedTreeview(self.master, columns, on_select =self.handleSelectEvent)
                def handleSelectEvent(self):
                   # Do code
            # Set column header widths
            tree.set_column_widths({"id": 50, "name": 150, "category": 100})
            ```

        * `get_selected_item_values(self) -> List`: Returns a list of column name value of the select columns
        * `get_selected_id(self) -> List`: Returns the id column name of the select column

            ```python
                # Example
                selected_val = enhanced_tree.get_selected_item_values()
                # Prints name and category column from select rows
                print(select_val["name"])
                print(select_val["category"])
            ```
        *   `Example usage:`
            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.enhanced_treeview import EnhancedTreeview
            # Define the main window
            root = tk.Tk()
            root.geometry("600x400")

            # Example sorting callback
            def on_sort(column, direction):
                print(f"Sorting by {column} ({direction})")

            # Define column headers
            columns = ("id", "name", "category", "status")

            # Create enhanced treeview
            tree = EnhancedTreeview(
                root,
                columns,
                on_sort=on_sort,
                status_column="status"
            )

            # Insert sample data
            tree.insert_item(1, ["1", "Leather", "Raw Material", "Active"])
            tree.insert_item(2, ["2", "Lining Fabric", "Textile", "Inactive"])
            tree.insert_item(3, ["3", "Buckle", "Hardware", "Active"])

            # Set column header widths
            tree.set_column_widths({"id": 50, "name": 150, "category": 100, "status": 80})

            root.mainloop()

            ```

**II. `gui.widgets.breadcrumb_navigation`**

*   **Module Name:** `gui.widgets.breadcrumb_navigation`
*   **Description:** Provides a hierarchical navigation path display. Allows navigation back to parent views in the hierarchy.

*   **Key Features:**
    *   **Clear hierarchy of the view** Hierarchal view of the view and data in the screen
    *   **Clickable Links:** Navigation back in the history
    *   **Callbacks:** Callable to set callback when a bradcrump is clicked
    *   **Styling** Sets the style of labels, texts and frames

*   **Classes:**
    *   `BreadcrumbNavigation(ttk.Frame)`:
        *   `__init__(self, parent, callback=None)`:
            *`parent`: The parent widget
            *`callback`: Function to call when a breadcrumb is clicked
        *   `set_callback(self, callback)`: Sets the callable function
        *   `update_breadcrumbs(self, breadcrumbs)`: Update the crumbnavigation and pass down the new breadcrumbs
            * `breadcrumbs`: List of breadcrumb dictionaries with 'title', 'view', and optional 'data'
        *   `clear_breadcrumbs(self)`: Clear the crumbnavigation
        *   `add_breadcrumb(self, title, view, data=None)`: Add the new breadcrumb to the frame
        *   `pop_breadcrumb(self)`: Pops the breadcrumb from the list
        *    `set_home_breadcrumb(self, title="Dashboard", view="dashboard")`: Set the main Dashboard Navigation

        ```python
        import tkinter as tk
        from tkinter import ttk
        from gui.widgets.breadcrumb_navigation import BreadcrumbNavigation

        class MyView(ttk.Frame):
          def __init__(self, parent):
              super().__init__(parent)
              self.label = tk.Label(parent, text="Crumb Navigation Frame")
              self.label.pack()

              self.breadcrumb = BreadcrumbNavigation(self)
              self.breadcrumb.pack()

              self.crumbList = [
                {"title": "Dashboard", "view": "dashboard"},
                {"title": "MaterialView", "view": "materialview"},
                {"title": "TextilesView", "view": "textileview"},
              ]
              # Set the crumbnavigation
              self.breadcrumb.update_breadcrumbs(self.crumbList)
        class MainApp(tk.Tk):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.geometry("800x600")

                my_view = MyView(self)
                my_view.pack(expand=True, fill="both", padx=20, pady=20)
        # Example call
        if __name__ == "__main__":
            root = MainApp()
            root.mainloop()
        ```

**III. `gui.widgets.search_frame`**

*   **Module Name:** `gui.widgets.search_frame`
*   **Description:** Reusable search interface with customizable fields.

*   **Key Features:**

    *   **Create search from scratch** Generates new Search form based on data
    *   **Search form and Reset** New search bar to implement action for get action from the user
    *   **Validate Number** Number Validation for the data
*   **Classes:**

    *   `SearchFrame(ttk.LabelFrame)`: Provides search
        * `get_search_criteria(self)`: Get the Search Criteria
        * `add_search_fields(self, fields)`: Add new Search fields to the search form
        *   `__init__( self, parent,search_fields: List[Dict[str, Any]],on_search: Callable[[Dict[str, Any]], None],title: str = "Search")`: Initizalies and create the new frame for search action
            *   `parent`: The parent widget
            *   `search_fields`: List of search field configurations
            *   `on_search`: Callback when search is performed (receives search criteria)
            *   `title`: Title for the frame

                ```python
                from gui.widgets.search_frame import SearchFrame

                class MyListView:
                    def __init__(self, parent):
                        self.search_fields = [
                            {"name": "name", "label": "Name", "type": "text"},
                            {"name": "category", "label": "Category", "type": "select", "options": ["Leather", "Textile", "Hardware"]},
                            {"name": "price", "label": "Price", "type": "number"}
                        ]

                        self.search_frame = SearchFrame(
                            parent,
                            self.search_fields,
                            on_search=self.on_search
                        )
                        self.search_frame.pack()

                    def on_search(self, criteria):
                        print("Search criteria:", criteria)
                ```
            *  `on_search()`: Handle search button click, and returns  all the non-empty column

                ```python
                    searchCriteria = []
                    class MyView(tk.Tk):
                         def __init__(self, *args, **kwargs):
                            self.search_fields = [
                              {"name": "code", "label": "Code", "type": "text"},
                              {"name": "category", "label": "category", "type": "text"}
                           ]
                            searchForm = SearchFrame(search_fields, on_search = getCriteria)

                    def getCriteria(criteria):
                        # Prints all searchCriteria from the form
                        print(searchForm.get_search_criteria())

                ```
            * `on_reset(self)`: Function to return the data to default column
            *   `validate_number(self, value)`: Function for number validation
            *   `set_field_value(self, field_name, value)`: Setting new Value to the column name
            *   `create_field_widget(self, parent, field)`: Base the widget to the type and the data from the column

        *  `SearchField`:
            Provides class for the columns

                ```python
                    class SearchFrame:
                       def __init__(self):
                            my_form = SearchFrame(root, search_fields = [SearchField(name="searchForm", label= "Help Form")])
                ```

**IV. `gui.widgets.enum_combobox`**

*   **Module Name:** `gui.widgets.enum_combobox`
*   **Description:** Specialized combobox for displaying and working with Python `Enum` types.

*   **Key Features:**

    *   **Enum Integration:** Directly displays values from an `Enum` class.
    *   **User-Friendly Display:** Formats `Enum` values for better readability in the UI.
    *   **Two-Way Binding:**  Automatically converts between display values and `Enum` instances.
    *   **Automatic String Conversion:** Converts back to string or to Enum
*   **Classes:**

    *   `EnumCombobox(ttk.Combobox)`:

        *   `__init__(self, parent, enum_class: Type[Enum], textvariable: Optional[tk.StringVar] = None, display_formatter: Optional[callable] = None, **kwargs)`: Initializes the enum combobox.

            *   `parent`: The parent widget.
            *   `enum_class`: The `Enum` class to use.
            *   `textvariable`: An optional `StringVar` to track the selected value.
            *   `display_formatter`: An optional function to format `Enum` values for display.

        *   `get_enum() -> Optional[Enum]`: Returns the selected `Enum` value, or `None` if nothing is selected.

        *   `set_enum(enum_value: Union[Enum, str, Any])`: Sets the selected `Enum` value.
            ```python
            import tkinter as tk
            from tkinter import ttk
            from enum import Enum
            from gui.widgets.enum_combobox import EnumCombobox

            class Status(Enum):
                ACTIVE = "active"
                INACTIVE = "inactive"
                PENDING = "pending"

            class MyView(ttk.Frame):
              def __init__(self, parent):
                 # Set the super master to root window
                 super().__init__(parent)
                 self.label = tk.Label(self, text="Enum Frame")
                 self.label.pack()
                 selectedStatus = tk.StringVar(value="Pending")

                 self.enumCombobox = EnumCombobox(self, Status, textvariable=selectedStatus)
                 self.enumCombobox.pack()
        class MainApp(tk.Tk):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.geometry("800x600")

                my_view = MyView(self)
                my_view.pack(expand=True, fill="both", padx=20, pady=20)
        if __name__ == "__main__":
            root = MainApp()
            root.mainloop()
            ```

**V. `gui.widgets.status_badge`**

*   **Module Name:** `gui.widgets.status_badge`
*   **Description:** Provides visual indicators for status values.
    *   **Show the Status for value** Creates the value for text data

*   **Key Features:**

    *   **Theme integration** Connect the new frame with theme data
    *   **Easy To implement** Base implementation to build status into UI

*   **Classes:**

    *   `StatusBadge(tk.Frame)`:  (All methods are static.)
        *   `__init__(self, parent,text: str = "", status_value: Optional[str] = None,width: int = 12,**kwargs)`: Creates the new `StatusBadge` widget

            *`parent`: The parent widget
            *`text`: The text to display
            *`status_value`: The status value for styling (if different from text)
            *`width`: The badge width
            *`**kwargs`: Additional arguments for tk.Frame
        *   `_try_round_corners()`: Tries to implement the round corner to the widget
        *    `set_text(text: str, status_value: Optional[str] = None)`: Updates the text for widget

            ```python
            import tkinter as tk
            from tkinter import ttk
            from gui.widgets.status_badge import StatusBadge
            class MyView(tk.Frame):
              def __init__(self, parent):
                 # Set the super master to root window
                 super().__init__(parent)
                 self.label = tk.Label(self, text="Frame")
                 self.label.pack()
                 # Create the new view
                 statusFrame = StatusBadge(self, "Active")
                 statusFrame.pack()
                 inActiveFrame = StatusBadge(self, "InActive")
                 inActiveFrame.pack()
        class MainApp(tk.Tk):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.geometry("800x600")
                my_view = MyView(self)
                my_view.pack(expand=True, fill="both", padx=20, pady=20)

            if __name__ == "__main__":
                root = MainApp()
                root.mainloop()
            ```
