Okay, here's the documentation in a similar style, focusing on the purpose, functionality, and usage of each of the provided `gui/utils` modules.

**I. `gui.utils.service_provider`**

*   **Module Name:** `gui.utils.service_provider`
*   **Description:** Provides a centralized and standardized mechanism for accessing services within the application. It acts as a facade for the dependency injection (DI) container, adding caching, consistent error handling, and parameter adaptation for service calls. This module promotes loose coupling and simplifies service management.

*   **Key Features:**

    *   **Service Caching:**  Caches resolved service instances to improve performance.
    *   **Error Handling:** Provides consistent error handling for service operations, wrapping exceptions with `ServiceProviderError` and ensuring proper logging.
    *   **Parameter Adaptation:** Adapts parameters passed to service methods to handle mismatches between GUI components and service APIs.
    *   **Exception Translation:** Re-raises service-specific exceptions (ValidationError, NotFoundError, PermissionError) to allow UI components to handle them appropriately.
    *   **with\_service decorator:** Provides an easy way to inject a service into a method.
*   **Classes:**
    *   `ServiceProvider`:

        *   `get_service(service_type: Union[str, Type]) -> Any`: Retrieves a service instance from the DI container, using the service cache if available.
            ```python
            from gui.utils.service_provider import ServiceProvider

            try:
                material_service = ServiceProvider.get_service("IMaterialService")
                # Use the material service
            except ServiceProviderError as e:
                print(f"Error resolving service: {e}")

            ```
        *   `execute_service_operation(service_type: Union[str, Type], operation: str, *args, **kwargs) -> Any`: Executes a service operation with standard error handling.
            ```python
            from gui.utils.service_provider import ServiceProvider

            try:
                materials = ServiceProvider.execute_service_operation(
                    "IMaterialService", "get_all", offset=0, limit=10
                )
                # Process the materials
            except Exception as e:
                print(f"Error executing service operation: {e}")
            ```
        *   `clear_cache() -> None`: Clears the service cache.
            ```python
            from gui.utils.service_provider import ServiceProvider

            ServiceProvider.clear_cache()
            ```
        *   `clear_service_from_cache(service_type: Union[str, Type]) -> None`:  Removes a specific service from the cache.
            ```python
            from gui.utils.service_provider import ServiceProvider

            ServiceProvider.clear_service_from_cache("IMaterialService")
            ```
    *   `ServiceProviderError(Exception)`: Custom exception raised when a service cannot be resolved or an operation fails.

*   **Decorator:**
    *   `with_service(service_type)`: Injects the specified service into a method as a keyword argument.
        ```python
        from gui.utils.service_provider import with_service

        class MyComponent:
            @with_service("IMaterialService")
            def do_something(self, service):
                materials = service.get_all()
                # ...

        component = MyComponent()
        component.do_something()
        ```

**II. `gui.utils.service_access`**

*   **Module Name:** `gui.utils.service_access`
*   **Description:**  Provides backward compatibility for existing code that might be using older service access patterns. It acts as a bridge, delegating service resolution and operation execution to the `ServiceProvider`. This module allows you to gradually transition existing code to the new `ServiceProvider` approach without breaking existing functionality.

*   **Key Features:**

    *   **Backward Compatibility:**  Maintains compatibility with older service access methods.
    *   **Delegation to `ServiceProvider`:** Delegates all service operations to the `ServiceProvider` for consistent handling.
    *   **Error Handling:**  Provides error handling and optional UI error display.

*   **Functions:**

    *   `get_service(service_name: str) -> Any`: Resolves a service using the `ServiceProvider`.

        ```python
        from gui.utils import service_access

        try:
            material_service = service_access.get_service("IMaterialService")
            # Use the material service
        except Exception as e:
            print(f"Error resolving service: {e}")
        ```
    *   `with_service(service_type: str)`: Injects a service into a method as an argument, using the `ServiceProvider`.

        ```python
        from gui.utils import service_access

        class MyComponent:
            @service_access.with_service("IMaterialService")
            def do_something(self, service, *args, **kwargs):
                materials = service.get_all()
                # ...

        component = MyComponent()
        component.do_something()
        ```

    *   `execute_service_operation(service_type: str, operation: str, *args: Any, **kwargs: Any) -> Any`: Executes a service operation using the `ServiceProvider`.

        ```python
        from gui.utils import service_access

        try:
            materials = service_access.execute_service_operation(
                "IMaterialService", "get_all", offset=0, limit=10
            )
            # Process the materials
        except Exception as e:
            print(f"Error executing service operation: {e}")
        ```

    *   `clear_service_cache()`: Clears the service cache.  Delegates to the service provider.

        ```python
        from gui.utils import service_access

        service_access.clear_service_cache()
        ```

**III. `gui.utils.utils_service_provider_bridge`**

*   **Module Name:** `gui.utils.utils_service_provider_bridge`
*   **Description:**  Provides a custom import hook to redirect imports from `utils.service_provider` to `gui.utils.service_provider`. This is used to maintain backward compatibility for applications that might have been using `utils.service_provider` directly before the code was reorganized.

*   **Key Features:**

    *   **Import Redirection:**  Intercepts imports of `utils.service_provider` and redirects them to the current `gui.utils.service_provider`.
    *   **Automatic Installation:** Installs the import hook when the module is imported.
    *   **Namespace Handling:** Creates a `utils` package if it doesn't already exist to act as a namespace for the redirected import.

*   **Classes:**

    *   `ServiceProviderImportFinder(importlib.abc.MetaPathFinder)`:  A custom import finder that intercepts imports of `utils.service_provider`.
        *   `find_spec(self, fullname, path, target=None)`: The method called by the import system to find a module specification.

*   **Functions:**

    *   `install_import_hook()`: Installs the custom import hook into `sys.meta_path`.

        *This module does not need manual usage of its functions, as it works automatically upon import.*

**IV. `gui.utils.view_history_manager`**

*   **Module Name:** `gui.utils.view_history_manager`
*   **Description:** Manages the navigation history within the GUI application. It allows for back and forward navigation between views, similar to a web browser's history.

*   **Key Features:**
    *   **History Stack:** Maintains a stack of visited view entries.
    *   **Navigation Callbacks:** Allows you to register a callback function that is invoked when navigating to a view.
    *   **History Management:** Provides methods for adding views, navigating back and forward, and clearing the history.
    *   **View Parameter Equality:** Includes logic for comparing view parameters to avoid duplicate history entries.

*   **Classes:**
    *   `ViewHistoryManager`
        *   `__init__(self, max_history: int = 50)`: Initializes the view history manager.

            *   `max_history`: The maximum number of views to store in the history stack.
        *   `set_navigation_callback(self, callback: Callable[[str, Any], None]) -> None`: Sets the callback function to be called when navigating to a view.

            *   `callback`: A function that takes the view name and view data as arguments.
        *   `add_view(self, view_name: str, view_data: Optional[Dict[str, Any]] = None) -> None`: Adds a view to the history stack.

            *   `view_name`: The name of the view.
            *   `view_data`: A dictionary of parameters to pass to the view.
        *   `can_go_back(self) -> bool`: Returns `True` if there is a previous view in the history, `False` otherwise.
        *   `can_go_forward(self) -> bool`: Returns `True` if there is a next view in the history, `False` otherwise.
        *   `go_back(self) -> bool`: Navigates to the previous view in the history. Returns `True` if successful, `False` otherwise.
        *   `go_forward(self) -> bool`: Navigates to the next view in the history. Returns `True` if successful, `False` otherwise.
        *   `get_current_view(self) -> Optional[Dict[str, Any]]`: Returns the view entry for the current view or `None` if there is no current view.
        *   `get_previous_view(self) -> Optional[Dict[str, Any]]`: Returns the view entry for the previous view or `None` if there is no previous view.
        *   `clear_history(self) -> None`: Clears the view history.
        *    `replace_current_view(self, view_name: str, view_data: Optional[Dict[str, Any]] = None) -> None`: Replaces the current view entry.
        *   `_are_view_params_equal(self, params1: Dict[str, Any], params2: Dict[str, Any]) -> bool`: Compare view parameters.
        *   `contains_view(self, view_name: str, view_data: Optional[Dict[str, Any]] = None) -> bool`: Checks if specific view is in history.

        ```python
        from gui.utils.view_history_manager import ViewHistoryManager

        history = ViewHistoryManager()
        history.add_view("DashboardView")
        history.add_view("MaterialListView", {"category": "Leather"})
        if history.can_go_back():
            history.go_back()

        current_view = history.get_current_view()
        print(current_view["view_name"])
        ```

**V. `gui.utils.error_manager`**

*   **Module Name:** `gui.utils.error_manager`
*   **Description:** Provides centralized error handling and logging utilities for the application. It standardizes the way errors are handled and presented to the user, ensuring a consistent and informative user experience.

*   **Key Features:**
    *   **Exception Handling:** Provides a method to handle exceptions with consistent logging and user feedback.
    *   **User-Friendly Messages:** Creates user-friendly error messages with specific guidance based on the exception type.
    *   **Centralized Logging:** Logs detailed error information, including tracebacks, for debugging.
    *   **Standardized Dialogs:**  Provides methods for showing validation errors and informational messages to the user.
    *   **Confirmation Dialogs:** Offers a standardized confirmation dialog.

*   **Classes:**
    *   `ErrorManager`: (All methods are static.)
        *   `handle_exception(view, exception, context=None)`: Handles exceptions, logs the details, and displays an error message to the user.

            ```python
            from gui.utils.error_manager import ErrorManager

            class MyView:
                def my_method(self):
                    try:
                        result = 1 / 0
                    except Exception as e:
                        ErrorManager.handle_exception(self, e, "Performing division")
            ```

        *   `log_error(exception, context=None)`: Logs the error details.
            ```python
            from gui.utils.error_manager import ErrorManager

            try:
                result = 1 / 0
            except Exception as e:
                ErrorManager.log_error(e, "Attempting division")
            ```
        *   `show_validation_error(message)`: Shows a validation error message to the user.
            ```python
            from gui.utils.error_manager import ErrorManager

            ErrorManager.show_validation_error("Invalid input: Age must be a number.")
            ```

        *   `show_info(title, message)`: Shows an informational message to the user.
            ```python
            from gui.utils.error_manager import ErrorManager

            ErrorManager.show_info("Success", "Operation completed successfully.")
            ```

        *   `confirm_action(title, message)`: Shows a confirmation dialog to the user. Returns `True` if user confirms, `False` otherwise.

            ```python
            from gui.utils.error_manager import ErrorManager

            if ErrorManager.confirm_action("Confirm Delete", "Are you sure you want to delete this?"):
                # Perform deletion
                pass
            ```

**VI. `gui.utils.event_bus`**

*   **Module Name:** `gui.utils.event_bus`
*   **Description:** Provides a simple event bus implementation for communication between GUI components. It uses a publish-subscribe pattern, allowing components to subscribe to specific topics and receive notifications when those topics are published.

*   **Key Features:**
    *   **Publish-Subscribe:** Implements the publish-subscribe pattern for decoupling components.
    *   **Topic Management:** Allows registering and managing topics for events.
    *   **Global Instance:** Provides a global event bus instance for easy access from any component.
    *   **Error Handling:** Handles exceptions in event handlers to prevent cascading failures.

*   **Functions (operate on the global event bus):**
    *   `subscribe(topic: str, callback: Callable[[Any], None]) -> None`: Subscribes a callback function to a topic.

        ```python
        from gui.utils import event_bus

        def handle_material_added(material):
            print(f"Material added: {material}")

        event_bus.subscribe("material_added", handle_material_added)
        ```

    *   `unsubscribe(topic: str, callback: Callable[[Any], None]) -> None`: Unsubscribes a callback function from a topic.

        ```python
        from gui.utils import event_bus

        def handle_material_added(material):
            print(f"Material added: {material}")

        event_bus.unsubscribe("material_added", handle_material_added)
        ```

    *   `publish(topic: str, data: Any = None) -> None`: Publishes data to a topic, notifying all subscribers.

        ```python
        from gui.utils import event_bus

        new_material = {"name": "Leather", "category": "Raw"}
        event_bus.publish("material_added", new_material)
        ```

    *   `register_topic(topic: str) -> None`: Registers a new topic.
        ```python
        from gui.utils import event_bus

        event_bus.register_topic("material_deleted")
        ```

    *   `get_topics() -> List[str]`: Returns a list of all registered topics.
        ```python
        from gui.utils import event_bus
        topics = event_bus.get_topics()
        ```

    *   `clear() -> None`: Clears all subscriptions.

        ```python
        from gui.utils import event_bus

        event_bus.clear()
        ```

**VII. `gui.utils.gui_logger`**

*   **Module Name:** `gui.utils.gui_logger`
*   **Description:** Provides logging utilities specifically configured for the GUI application. It sets up logging to both a file and the console (for development), using a rotating file handler to manage log file size.

*   **Key Features:**
    *   **File and Console Logging:** Logs to both a file and the console for flexibility.
    *   **Rotating File Handler:** Uses a rotating file handler to limit log file size.
    *   **Configurable Log Level:** Allows setting the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    *   **Timestamped Log Files:** Creates log files with timestamps in the file names.

*   **Functions:**
    *   `setup_gui_logger(level="INFO", log_dir="logs")`: Configures logging for the GUI application.

        ```python
        from gui.utils.gui_logger import setup_gui_logger

        setup_gui_logger(level="DEBUG", log_dir="my_logs")

        # Now you can use the logging module:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("This is a debug message.")
        ```

        *   `level`: The log level (default: "INFO").
        *   `log_dir`: The directory to store log files (default: "logs").
    *   `get_logger(name)`: Gets a logger for a specific module.
        ```python
        from gui.utils.gui_logger import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")
        ```

**VIII. `gui.utils.navigation_service`**

*   **Module Name:** `gui.utils.navigation_service`
*   **Description:** Provides a centralized navigation system for moving between different views within the GUI application.  It simplifies the process of view navigation and manages view parameters for a consistent user experience.

*   **Key Features:**

    *   **Centralized Navigation:**  Provides a single point of control for view navigation.
    *   **Parameter Handling:** Simplifies passing parameters to different views.
    *   **History Management:** Integrates with the `ViewHistoryManager` to maintain navigation history.
    *   **Standardized Patterns:** Implements standardized patterns for common navigation tasks, such as navigating to entity details views.
    *   **Error Handling:** Includes error handling and user feedback for navigation failures.
    *   **Lazy Loading of Views:** Utilizes lazy loading to prevent circular imports and reduce initial load time.
    *  **Singleton Pattern:** Navigation Service follows singleton design pattern to ensure one instance

*   **Classes:**

    *   `NavigationService`:

        *   `get_instance() -> 'NavigationService'`: Returns the singleton instance of the navigation service.
        *   `initialize(main_window: Any, view_history_manager: Any) -> None`: Initializes the service with the main window and view history manager.
        *   `navigate_to_view(parent_window: Any, view_name: str, view_params: Optional[Dict[str, Any]] = None, add_to_history: bool = True) -> Any`: Navigates to a specific view.

            ```python
            from gui.utils.navigation_service import NavigationService
            from main_window import MainWindow  # Assuming main_window.py

            # Get the NavigationService instance
            navigation_service = NavigationService.get_instance()

            # Example usage inside some view/component
            main_window = NavigationService._find_main_window(self)
            navigation_service.navigate_to_view(main_window, "MaterialListView", {"category": "Leather"})
            ```

        *   `navigate_to_entity_details(parent_window: Any, entity_type: str, entity_id: Union[int, str], readonly: bool = False) -> Any`: Navigates to an entity details view.

            ```python
            from gui.utils.navigation_service import NavigationService
            from main_window import MainWindow  # Assuming main_window.py
            # Get the NavigationService instance
            navigation_service = NavigationService.get_instance()
            # Example usage
            navigation_service.navigate_to_entity_details(self.main_window, "material", 123, readonly=True)
            ```

        *   `navigate_back(parent_window: Any) -> bool`: Navigates back in history.

        *   `navigate_forward(parent_window: Any) -> bool`: Navigates forward in history.
        *    `can_go_back(parent_window: Any) -> bool`: Checks to see whether the navigation stack can navigate backwards
        *    `can_go_forward(parent_window: Any) -> bool`: Checks to see whether the navigation stack can navigate forwards
        * `open_dialog(parent_window: Any, dialog_class: Type[T], **kwargs) -> Optional[T]`: Opens a new dialog
            ```python
            from gui.utils.navigation_service import NavigationService
            from main_window import MainWindow
            from gui.dialogs.my_custom_dialog import MyCustomDialog

            class MyView:
                # inside MyView
                def open_my_dialog(self):
                  result = NavigationService.open_dialog(self.master, MyCustomDialog, initial_value=100)
                  if result:
                      print(f"Result from dialog: {result}")
        ```

    *Helper function to Find the Main Window*
        *   `_find_main_window(widget: Any) -> Optional[Any]`: Locates the main application window given any child widget.
**IX. `gui.utils.keyboard_shortcuts`**

*   **Module Name:** `gui.utils.keyboard_shortcuts`

*   **Description:** Provides a centralized keyboard shortcut management system for the application.

*   **Key Features:**

    *   **Centralized Management:** Provides a single point to register, unregister, and manage keyboard shortcuts.
    *   **Context-Aware Shortcuts:** Allows defining shortcuts that are active only in specific contexts (e.g., a specific view or dialog).
    *   **Sequential Shortcuts:** Supports multi-key sequential shortcuts (e.g., Ctrl+N, P for "New Project").
    *   **Help Display:** Includes functionality to display a help dialog with all registered shortcuts.
    *   **Customizable Formatting:** Allows customization of the key combination display.

*   **Classes:**

    *   `KeyboardShortcutManager`:

        *   `__init__(self, root_window)`: Initializes the shortcut manager.

            *   `root_window`: The main application window.

        *   `register_shortcut(key_combination: str, command: Callable, description: str = None, context: str = "global")`: Registers a new keyboard shortcut.
            ```python
            from gui.utils.keyboard_shortcuts import KeyboardShortcutManager

            class MyView:
                def __init__(self, master):
                    self.master = master
                    # Create label
                    self.label = tk.Label(master, text="Some label")
                    self.label.pack()
                def setup_shortcuts(self):

                   root = self.master # Get main tk window
                   self.master.shortcut_manager.register_shortcut(
                      "Ctrl+Shift+X",
                      lambda event: self.on_my_custom_action(),
                      "Description of My Custom Action",
                      "my_view_context",
                   )
                def on_my_custom_action(self):
                   print("My custom action triggered via shortcut")

            root = tk.Tk()
            root.geometry("800x600")

            view = MyView(root)

            # Get shortcut manager to the new window
            root.shortcut_manager = KeyboardShortcutManager(root)
            root.mainloop()
            ```

            *   `key_combination`: The key combination (e.g., "Ctrl+S").
            *   `command`: The function to execute when the shortcut is pressed.
            *   `description`: A description of the shortcut (optional).
            *   `context`: The context in which the shortcut is active (default: "global").
        *    `unregister_shortcut(self, key_combination: str, context: str = "global") -> bool`: unregisters the current shortcut
        *   `set_context(self, context: str)`: Sets the active shortcut context. Only shortcuts for the active context are enabled.

        *   `get_all_shortcuts() -> Dict[str, str]`: Returns a dictionary of all registered shortcuts and their descriptions.

        *    `get_context_shortcuts(self, context: str = None) -> Dict[str, str]`: Returns registered shortcuts and description of specific context
        *   `show_shortcut_help(self)`: Displays a dialog with a list of all registered shortcuts.

    *Helper functions*
    * `setup_shortcuts(root_window)`: Initiates the shortcuts
        ```python
        # import tk and ttk
        import tkinter as tk

        # importing all helper functions
        from gui.utils.keyboard_shortcuts import (
            KeyboardShortcutManager,
            register_view_shortcuts,
            set_shortcut_context,
        )
        class KeyboardShortcuts:
            def __init__(self, master):
                # Sets master to root
                self.master = master
                # Setup label widget
                self.label = tk.Label(master, text="Setting the shortcut on the label")
                self.label.pack()

            def add_shortcut_label(self):
                KeyboardShortcutManager(self.master)
                new_shortcut = KeyboardShortcutManager(root)
        root = tk.Tk()
        KeyboardShortcuts(root)
        ```
    * `register_view_shortcuts(root_window, view_name, shortcuts)`: Register the shortcut for the label
        ```python
        class KeyboardShortcuts:
            def __init__(self, master):
                self.master = master
                self.label = tk.Label(master, text="Setting the shortcut on the label")
                self.label.pack()
            def add_shortcut_label(self):
                register_view_shortcuts(root, "MyLabel", {"Ctrl+Shift+B": (KeyboardShortcuts.keyBoardHelp, "Description Of Help Action")})
        ```
    * `set_shortcut_context(root_window, context)`: Sets the active shortcut

    * `show_shortcut_help(root_window)`: The method opens a new window for the help message

        ```python
            # add the view shortcut inside the same method
           def add_shortcut_label(self):
                new_shortcuts = {
                    "Ctrl+Shift+R": (KeyboardShortcuts.keyBoardRefresh, "Description Of Refresh Action"),
                    "Ctrl+Shift+B": (KeyboardShortcuts.keyBoardHelp, "Description Of Help Action"),
                }
                register_view_shortcuts(root, "MyLabel", new_shortcuts)

        def keyBoardHelp(event=None):
            # The Method that creates the help message for the user
            show_shortcut_help(root)
         ```

With this documentation, developers can easily understand the utility of each function, class, and their inner workings. This modular documentation makes it scalable and easy to implement in the GUI application.
