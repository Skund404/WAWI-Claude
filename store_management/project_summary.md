# Project Analysis: store_management
Total Python files: 236

## anotator.py

### Classes:

#### FunctionContext

#### CodeAnnotator
Inherits from: cst.CSTTransformer

Methods:
- __init__(self)
- infer_type(self, node)
- visit_FunctionDef(self, node)
- leave_FunctionDef(self, original_node, updated_node)
- leave_Param(self, original_node, updated_node)

#### DocstringGenerator
Inherits from: cst.CSTTransformer

Methods:
- leave_FunctionDef(self, original_node, updated_node)

#### ProjectAnnotator

Methods:
- __init__(self, project_path)
- process_file(self, file_path)
- process_project(self)

### Functions:
- annotate_project(project_path)

---

## application.py

### Classes:

#### Application

Methods:
- __init__(self)
- _setup_application(self)
- _register_services(self)
- _register_views(self)
- get_service(self, service_type)
- run(self)
- quit(self)

---

## config.py

### Functions:
- get_database_path()

---

## examples.py

### Classes:

#### LeatherworkingProjectWorkflow

Methods:
- __init__(self, project_service, hardware_service, supplier_service)
- create_leather_bag_project(self)
- track_project_progress(self, project)
- simulate_workflow(self)

### Functions:
- main()

---

## import_test.py

---

## main.py

### Functions:
- setup_exception_handler(root)
- initialize_app()
- main()

---

## mover_temp.py

---

## project_analyzer.py

### Classes:

#### FunctionInfo

#### ClassInfo

#### FileInfo

#### ProjectAnalyzer

Methods:
- __init__(self, project_path)
- analyze_project(self)
- analyze_file(self, file_path)
- _extract_function_info(self, node)
- _extract_class_info(self, node)
- generate_summary(self)

### Functions:
- format_for_chat(summary)
- analyze_project(project_path)

---

## project_analyzer_lightweight.py

### Classes:

#### FunctionInfo

#### ClassInfo

#### FileInfo

#### ProjectAnalyzer

Methods:
- __init__(self, project_path)
- analyze_project(self)
- analyze_file(self, file_path)
- _extract_function_info(self, node)
- _extract_class_info(self, node)
- generate_summary(self)

### Functions:
- format_for_chat(summary)
- analyze_project(project_path)

---

## setup.py

---

## tkinter_test.py

### Functions:
- print_import_chain()
- test_tkinter()

---

## __init__.py

---

## alembic\env.py

### Functions:
- run_migrations_offline()
- run_migrations_online()

---

## config\application_config.py

### Classes:

#### ApplicationConfig

Methods:
- __new__(cls)
- __init__(self)
- _load_config(self)
- _get_config_dir(self)
- _get_config_path(self)
- _merge_config(self, config)
- _load_from_env(self)
- get(self)
- set(self, value)
- save(self)

---

## config\environment.py

### Classes:

#### EnvironmentManager

Methods:
- __new__(cls)
- get(cls, key, default)
- is_debug(cls)
- get_log_level(cls)
- set_debug(cls, enable)

---

## config\settings.py

### Functions:
- _find_project_root()
- get_database_path()
- get_log_path()
- get_backup_path()
- get_config_path()

---

## config\__init__.py

---

## controllers\dashboard_controller.py

### Classes:

#### MetricsScheduler

Methods:
- __init__(self, dashboard_service)
- _setup_jobs(self)
- _capture_daily_metrics(self)
- _capture_weekly_metrics(self)
- _capture_monthly_metrics(self)
- _cleanup_old_metrics(self)
- start(self)
- shutdown(self)

### Functions:
- get_dashboard_service()

---

## controllers\__init__.py

---

## database\config.py

### Functions:
- get_database_url(config)
- _find_project_root()
- get_database_config()

---

## database\initialize.py

### Functions:
- create_tables(engine)
- add_sample_data(session)
- initialize_database(drop_existing)

---

## database\session.py

### Functions:
- init_database(db_url)
- get_db_session()
- close_db_session()

---

## database\__init__.py

### Functions:
- initialize_database(drop_existing)
- _add_initial_data()

---

## di\config.py

### Classes:

#### ApplicationConfig

Methods:
- configure_container(cls)
- _register_services(cls, container)
- get_container(cls)
- get_service(cls, service_type)

---

## di\container.py

### Classes:

#### DependencyContainer

Methods:
- __init__(self)
- register(self, interface_type, implementation_factory, singleton)
- resolve(self, interface_type)
- get_service(self, interface_type)
- is_registered(self, interface_type)
- clear(self)
- __repr__(self)

---

## di\service.py

### Classes:

#### Service
Inherits from: abc.ABC

Methods:
- __init__(self, container)
- get_dependency(self, dependency_type)

---

## di\__init__.py

---

## examples\leatherworking_project_workflow.py

### Classes:

#### LeatherworkingProjectWorkflow

Methods:
- __init__(self, project_service, material_service, inventory_service)
- create_leather_bag_project(self)
- track_project_progress(self, project_id)
- simulate_workflow(self)

### Functions:
- main()

---

## examples\leatherworking_workflow_example.py

### Classes:

#### LeatherworkingProjectWorkflow

Methods:
- __init__(self, project_service, hardware_service, supplier_service)
- create_leather_bag_project(self)
- track_project_progress(self, project)
- simulate_workflow(self)

### Functions:
- main()

---

## examples\material_management_workflow.py

### Classes:

#### MaterialManagementWorkflow

Methods:
- __init__(self, material_service, supplier_service)
- onboard_leather_material(self, supplier_id)
- manage_material_inventory(self, material_id)
- generate_material_reports(self)
- simulate_workflow(self)

### Functions:
- main()

---

## examples\__init__.py

---

## gui\base_view.py

### Classes:

#### BaseView
Inherits from: ttk.Frame, ABC

Methods:
- __init__(self, parent, app)
- get_service(self, service_type)
- setup_ui(self)
- load_data(self)
- show_error(self, title, message)
- show_info(self, title, message)
- show_warning(self, title, message)
- confirm(self, title, message)
- refresh(self)
- cleanup(self)
- set_status(self, message)

---

## gui\main_window.py

### Classes:

#### MainWindow
Inherits from: ttk.Frame

Methods:
- __init__(self, root, app)
- _setup_window(self)
- _create_menu(self)
- _create_notebook(self)
- _create_status_bar(self)
- set_status(self, message)
- add_view(self, name, view)
- _on_new(self)
- _on_open(self)
- _on_save(self)
- _on_undo(self)
- _on_redo(self)
- _on_refresh(self)
- _on_exit(self)

---

## gui\__init__.py

---

## modules\__init__.py

---

## patches\fix_storage_view.py

### Functions:
- manually_load_storage_view()

---

## patches\storage_view_debug.py

### Functions:
- debug_load_data(self)

---

## patches\__init__.py

---

## services\advanced_analytics_service.py

### Classes:

#### AdvancedAnalyticsService

Methods:
- __init__(self, material_service, project_service)
- generate_material_efficiency_report(self)
- project_performance_analysis(self)
- material_cost_analysis(self)
- generate_visualization(self, analysis_type, output_path)
- generate_comprehensive_report(self)

### Functions:
- main()

---

## services\dashboard_service.py

### Classes:

#### DashboardService
Inherits from: Service

Methods:
- __init__(self, container)
- get_dashboard_metrics(self)
- _get_inventory_metrics(self)
- _get_project_metrics(self)
- _get_material_usage(self)
- _get_supplier_metrics(self)
- _calculate_stock_percentage(self, items)
- _calculate_completion_rate(self, projects)
- _group_projects_by_status(self, projects)
- _calculate_material_efficiency(self)
- _get_active_supplier_orders(self)
- _get_default_metrics(self)
- _get_default_inventory_metrics(self)
- _get_default_project_metrics(self)
- _get_default_material_usage(self)
- _get_default_supplier_metrics(self)

---

## services\inventory_service.py

### Classes:

#### InventoryService
Inherits from: Service, IInventoryService

Methods:
- __init__(self, container)
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
- get_low_stock_parts(self, include_out_of_stock)
- get_low_stock_leather(self, include_out_of_stock)
- _update_part_status(self, part)
- _update_leather_status(self, leather)
- _part_to_dict(self, part)
- _leather_to_dict(self, leather)

---

## services\material_management_service.py

### Classes:

#### MaterialStatus
Inherits from: Enum

#### MaterialAllocation

Methods:
- __init__(self, material_id, total_quantity)
- allocate(self, project_id, quantity, allocation_type)
- deallocate(self, project_id, quantity)

#### MaterialEfficiencyMetrics

Methods:
- update_metrics(self, used, wasted, project_id)

#### MaterialManagementService

Methods:
- __init__(self)
- register_material(self, material_id, total_quantity, material_type)
- allocate_material(self, material_id, project_id, quantity)
- deallocate_material(self, material_id, project_id, quantity)
- update_material_efficiency(self, material_id, project_id, used, wasted)
- get_material_efficiency_report(self, material_id)
- get_material_allocation_status(self, material_id)

### Functions:
- main()

---

## services\order_service.py

### Classes:

#### OrderService
Inherits from: Service, IOrderService

Methods:
- __init__(self, container)
- get_all_orders(self)
- get_order_by_id(self, order_id)
- create_order(self, order_data)
- update_order(self, order_id, order_data)
- delete_order(self, order_id)
- process_order_payment(self, order_id, payment_amount)
- get_orders_by_status(self, status)
- get_supplier_orders(self, supplier_id)
- generate_order_report(self, start_date, end_date)

---

## services\project_service.py

### Classes:

#### RecipeService

Methods:
- __init__(self)
- create_project(self, recipe_data, items)
- check_materials_availability(self, recipe_id, quantity)

---

## services\project_workflow_manager.py

### Classes:

#### ProjectType
Inherits from: Enum

#### SkillLevel
Inherits from: Enum

#### ProjectStatus
Inherits from: Enum

#### ProjectMaterial

#### ProjectTask

#### ProjectWorkflowManager

Methods:
- __init__(self, material_service)
- create_project(self, name, project_type, skill_level, description)
- update_project_details(self, project_id)
- update_project_status(self, project_id, new_status)
- add_project_material(self, project_id, material_id, expected_quantity, cost_per_unit, supplier)
- update_material_usage(self, project_id, material_id, actual_quantity, wastage)
- add_project_task(self, project_id, name, description, dependencies, estimated_duration, priority)
- update_task_status(self, project_id, task_id, status, assigned_to)
- _calculate_project_progress(self, project_id)
- generate_project_summary(self, project_id)
- get_all_projects(self, status)

### Functions:
- main()

---

## services\shopping_list_service.py

### Classes:

#### ShoppingListService

Methods:
- __init__(self)
- create_shopping_list(self, list_data, items)
- add_item_to_list(self, list_id, item_data)
- mark_item_purchased(self, item_id, purchase_data)
- get_pending_items_by_supplier(self)

---

## services\storage_service.py

### Classes:

#### StorageService
Inherits from: IStorageService

Methods:
- __init__(self, db_manager)
- get_all_storage_locations(self)
- get_storage_by_id(self, storage_id)
- _to_dict(self, storage)
- _product_to_dict(self, product)

---

## services\__init__.py

---

## src\__init__.py

---

## tests\advanced_pattern_library.py

### Classes:

#### AdvancedPatternLibrary
Inherits from: tk.Frame

Methods:
- __init__(self, parent)
- setup_ui(self)
- setup_pattern_library(self)
- setup_test_suite(self)
- run_tests(self)

---

## tests\test_project_workflow_manager.py

### Classes:

#### TestProjectWorkflowManager
Inherits from: unittest.TestCase

Methods:
- setUp(self)
- test_create_project(self)
- test_update_project_details(self)
- test_update_project_status(self)
- test_add_project_material(self)
- test_update_material_usage(self)
- test_add_project_task(self)
- test_update_task_status(self)
- test_generate_project_summary(self)

---

## tests\test_storage.py

### Functions:
- test_storage_operations()

---

## tests\__init__.py

---

## tools\check_database.py

### Functions:
- find_database_path()
- check_database_file()
- list_database_tables()
- check_table_contents(table_name)
- main()

---

## tools\check_database_data.py

### Functions:
- find_database_file()
- check_storage_table()
- add_sample_data()
- main()

---

## tools\check_project_structure.py

### Functions:
- get_project_root()
- check_directory_structure()
- check_module_imports()
- check_database_config()
- main()

---

## tools\debug_view.py

### Functions:
- check_database_connectivity()
- check_view_loading()
- main()

---

## tools\enable_all_tabs.py

### Functions:
- create_recipe_view()
- create_order_view()
- create_shopping_list_view()
- enable_tabs_in_main_window()
- main()

---

## tools\fix_application.py

### Functions:
- fix_application()

---

## tools\fix_base_view.py

### Functions:
- fix_base_view()

---

## tools\fix_database_structure.py

### Functions:
- find_database_file()
- check_storage_table_structure()
- fix_storage_table()
- add_sample_data()
- backup_database()
- main()

---

## tools\fix_imports.py

### Functions:
- scan_for_problematic_imports()
- fix_imports(file_paths, dry_run)
- create_standalone_viewer()
- main()

---

## tools\fix_main_window.py

### Functions:
- fix_main_window()

---

## tools\fix_main_window_tabs.py

### Functions:
- fix_main_window()

---

## tools\fix_standalone_viewer.py

### Functions:
- fix_viewer()

---

## tools\rename_project_files.py

### Classes:

#### ProjectRenamer

Methods:
- __init__(self, project_root)
- _find_files(self, pattern)
- rename_files(self)
- update_file_contents(self)
- run(self)

### Functions:
- main()

---

## tools\run_migration.py

### Functions:
- setup_logging()
- run_migrations(db_url, drop_existing)
- main()

---

## tools\standalone_storage_viewer.py

### Classes:

#### StorageViewer

Methods:
- __init__(self, root)
- setup_ui(self)
- load_data(self)
- show_error(self, title, message)

### Functions:
- find_database_file()
- main()

---

## tools\__init__.py

---

## utils\backup.py

### Classes:

#### DatabaseBackup

Methods:
- __init__(self, db_path)
- create_backup(self, operation)
- restore_backup(self, backup_path)
- list_backups(self)
- cleanup_old_backups(self, keep_days)

---

## utils\database_utilities.py

### Classes:

#### DatabaseUtilities

Methods:
- __init__(self, db_path)
- export_database(self, export_path)
- import_database(self, import_path)
- export_schema(self)
- optimize_database(self)
- verify_database(self)
- generate_report(self, report_type)
- _generate_inventory_report(self, cursor)
- _generate_orders_report(self, cursor)
- _generate_suppliers_report(self, cursor)

---

## utils\error_handler.py

### Classes:

#### ErrorHandler

Methods:
- log_database_action(action, details)
- validate_positive_integer(value, field_name)
- show_error(self, title, message, error)
- show_warning(self, title, message)
- handle_error(self, func)

#### ApplicationError
Inherits from: Exception

Methods:
- __init__(self, message, details)

#### DatabaseError
Inherits from: ApplicationError

#### ValidationError
Inherits from: ApplicationError

### Functions:
- check_database_connection(func)
- get_error_context()

---

## utils\error_handling.py

### Classes:

#### DatabaseError
Inherits from: Exception

Methods:
- __init__(self, message, details, error_code)
- __str__(self)

### Functions:
- handle_database_error(operation, error, context)
- log_database_action(action, details, level)

---

## utils\exporters.py

### Classes:

#### OrderExporter

Methods:
- export_to_csv(data, filepath)
- export_to_excel(data, filepath)
- export_to_json(data, filepath)

#### OrderImporter

Methods:
- import_from_csv(order_file, details_file)
- import_from_excel(filepath)
- import_from_json(filepath)

---

## utils\logger.py

### Functions:
- setup_logging(log_level, log_dir, log_filename)
- get_logger(name)
- log_error(error, context, logger_name)
- log_info(message, logger_name)
- log_debug(message, logger_name)

---

## utils\logging_config.py

### Classes:

#### LoggerConfig

Methods:
- create_logger(name, log_level, log_dir)

#### ErrorTracker

Methods:
- __init__(self, logger)
- log_error(self, error, context, additional_info)
- trace_method(self, method_name)

---

## utils\notifications.py

### Classes:

#### NotificationType
Inherits from: Enum

#### StatusNotification

Methods:
- __init__(self, parent)
- setup_styles(self)
- start_processor(self)
- _process_notifications(self)
- _show_notification(self, notification)
- _clear_notification(self, callback)
- show_info(self, message, duration)
- show_success(self, message, duration)
- show_warning(self, message, duration)
- show_error(self, message, duration)
- show_progress(self, message, callback)
- clear(self)
- cleanup(self)

---

## utils\utils.py

---

## utils\validators.py

### Classes:

#### OrderValidator

Methods:
- validate_order(data)
- validate_order_details(data)

#### DataSanitizer

Methods:
- sanitize_string(value)
- sanitize_numeric(value)
- sanitize_identifier(value)
- sanitize_order_data(data)

---

## utils\__init__.py

---

## views\__init__.py

---

## utils\order_exporter\order_exporter.py

### Classes:

#### OrderExporter

Methods:
- export_to_excel(data, filepath)
- export_to_csv(data, filepath)
- export_to_json(data, filepath)

---

## utils\order_exporter\__init__.py

---

## utils\validators\order_validator.py

### Classes:

#### OrderValidator

Methods:
- validate_order(data)
- validate_order_detail(data)

---

## utils\validators\__init__.py

---

## tests\test_database\test_base_manager.py

### Classes:

#### TestModel
Inherits from: TestBase

#### TestSpecializedManager

Methods:
- get_by_name(self, name)

#### TestBaseManager

Methods:
- test_create_single_record(self, test_manager)
- test_get_record(self, test_manager)
- test_update_record(self, test_manager)
- test_delete_record(self, test_manager)
- test_bulk_create(self, test_manager)
- test_bulk_update(self, test_manager)
- test_get_all(self, test_manager)
- test_search(self, test_manager)
- test_filter(self, test_manager)
- test_exists(self, test_manager)
- test_count(self, test_manager)
- test_specialized_manager(self, session_factory)

#### TestErrorHandling

Methods:
- test_create_invalid_data(self, test_manager)
- test_update_non_existent_record(self, test_manager)
- test_delete_non_existent_record(self, test_manager)

### Functions:
- test_engine()
- session_factory(test_engine)
- test_manager(session_factory)

---

## tests\test_database\test_manager_factory.py

### Classes:

#### FactoryTestModel
Inherits from: FactoryTestBase

#### CustomTestManager

Methods:
- custom_method(self)

#### TestManagerFactory

Methods:
- test_engine(self)
- session_factory(self, test_engine)
- test_manager_cache(self, session_factory)
- test_specialized_manager_registration(self, session_factory)
- test_force_new_manager(self, session_factory)
- test_manager_with_mixins(self, session_factory)
- test_invalid_mixin(self, session_factory)

#### TestManagerPerformance

Methods:
- large_dataset_manager(self, session_factory)
- test_large_dataset_retrieval(self, large_dataset_manager)
- test_large_dataset_filtering(self, large_dataset_manager)

---

## tests\test_database\__init__.py

---

## tests\test_repositories\test_storage_repository.py

### Classes:

#### TestStorageRepository
Inherits from: unittest.TestCase

Methods:
- setUp(self)
- tearDown(self)
- test_get_all(self)
- test_get_by_id(self)
- test_get_by_location(self)
- test_create(self)
- test_update(self)
- test_delete(self)

---

## tests\test_repositories\test_storage_service.py

### Classes:

#### TestStorageService
Inherits from: unittest.TestCase

Methods:
- setUp(self)
- tearDown(self)
- test_assign_product_to_storage(self)

---

## tests\test_repositories\__init__.py

---

## src\models\__init__.py

---

## services\implementations\hardware_service.py

### Classes:

#### HardwareService
Inherits from: IHardwareService

Methods:
- __init__(self, hardware_repository)
- create_hardware(self, hardware_data)
- _validate_hardware_data(self, hardware_data)
- _check_duplicate_hardware(self, hardware_data)
- _post_hardware_creation_tasks(self, hardware)
- get_hardware(self, hardware_id)
- update_hardware(self, hardware_id, update_data)
- _validate_hardware_update(self, update_data)
- delete_hardware(self, hardware_id)
- get_low_stock_hardware(self, include_zero_stock)
- generate_hardware_performance_report(self)
- find_compatible_hardware(self, project_component, hardware_type)
- analyze_hardware_usage(self, project_id)

---

## services\implementations\inventory_service.py

### Classes:

#### InventoryService
Inherits from: Service, IInventoryService

Methods:
- __init__(self, container)
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
- get_low_stock_parts(self, include_out_of_stock)
- get_low_stock_leather(self, include_out_of_stock)
- _part_to_dict(self, part)
- _leather_to_dict(self, leather)

---

## services\implementations\material_service.py

### Classes:

#### MaterialService
Inherits from: IMaterialService

Methods:
- __init__(self, material_repository)
- _validate_material_data(self, material_data)
- create_material(self, material_data)
- get_material(self, material_id)
- update_material(self, material_id, material_data)
- delete_material(self, material_id)
- get_low_stock_materials(self, include_zero_stock)
- track_material_usage(self, material_id, quantity_used)
- search_materials(self, search_params)
- generate_sustainability_report(self)
- calculate_material_efficiency(self, material_id, period_days)

---

## services\implementations\order_service.py

### Classes:

#### OrderService
Inherits from: IOrderService

Methods:
- __init__(self, container)
- get_all_orders(self)
- get_order_by_id(self, order_id)
- get_order_by_number(self, order_number)
- create_order(self, order_data)
- update_order(self, order_id, order_data)
- delete_order(self, order_id)
- process_order_payment(self, order_id, payment_amount)
- get_orders_by_status(self, status)
- get_orders_by_customer(self, customer_name)
- get_order_statistics(self)
- _generate_order_number(self)
- cleanup(self)

---

## services\implementations\project_service.py

### Classes:

#### ProjectService
Inherits from: IProjectService

Methods:
- __init__(self, project_repository)
- _validate_project_data(self, project_data)
- create_project(self, project_data)
- get_project(self, project_id, include_components)
- update_project(self, project_id, project_data)
- delete_project(self, project_id)
- search_projects(self, search_params)
- get_complex_projects(self, complexity_threshold)
- analyze_project_material_usage(self, project_id)
- generate_project_complexity_report(self)
- update_project_status(self, project_id, new_status)

---

## services\implementations\recipe_service.py

### Classes:

#### RecipeService
Inherits from: IRecipeService

Methods:
- __init__(self, container)
- get_all_recipes(self)
- get_recipe_by_id(self, recipe_id)
- create_project(self, recipe_data)
- update_project(self, recipe_id, recipe_data)
- delete_project(self, recipe_id)
- check_materials_availability(self, recipe_id, quantity)
- calculate_production_cost(self, recipe_id, quantity)
- get_recipes_by_category(self, category)
- search_recipes(self, search_term)
- _calculate_materials_cost(self, recipe)
- _calculate_labor_cost(self, recipe)
- cleanup(self)

---

## services\implementations\shopping_list_service.py

### Classes:

#### ShoppingListService
Inherits from: Service, IShoppingListService

Methods:
- __init__(self, container)
- get_all_shopping_lists(self)
- get_shopping_list_by_id(self, list_id)
- create_shopping_list(self, list_data)
- update_shopping_list(self, list_id, list_data)
- delete_shopping_list(self, list_id)
- add_item_to_list(self, list_id, item_data)
- _add_item_to_list(self, item_data)
- _remove_all_list_items(self, list_id)
- remove_item_from_list(self, list_id, item_id)
- mark_item_purchased(self, list_id, item_id, quantity)
- get_active_lists(self)
- get_lists_by_status(self, status)
- search_shopping_lists(self, search_term)
- get_pending_items(self)
- get_shopping_list_summary(self, list_id)
- merge_shopping_lists(self, source_ids, target_id)
- cleanup(self)

---

## services\implementations\storage_service.py

### Classes:

#### StorageService
Inherits from: Service, IStorageService

Methods:
- __init__(self, container)
- get_all_storage_locations(self)
- get_storage_by_id(self, storage_id)
- create_storage_location(self, storage_data)
- update_storage_location(self, storage_id, storage_data)
- delete_storage_location(self, storage_id)
- search_storage_locations(self, search_term)
- get_storage_status(self, storage_id)
- _to_dict(self, storage)

---

## services\implementations\supplier_service.py

### Classes:

#### SupplierService
Inherits from: Service, ISupplierService

Methods:
- __init__(self, container)
- get_all_suppliers(self)
- get_supplier_by_id(self, supplier_id)
- create_supplier(self, supplier_data)
- update_supplier(self, supplier_id, supplier_data)
- delete_supplier(self, supplier_id)
- _to_dict(self, supplier)

---

## services\implementations\__init__.py

---

## services\interfaces\base_service.py

### Classes:

#### IBaseService
Inherits from: ABC

---

## services\interfaces\hardware_service.py

### Classes:

#### IHardwareService
Inherits from: ABC

Methods:
- create_hardware(self, hardware_data)
- get_hardware(self, hardware_id)
- update_hardware(self, hardware_id, update_data)
- delete_hardware(self, hardware_id)
- get_low_stock_hardware(self, include_zero_stock)
- generate_hardware_performance_report(self)

---

## services\interfaces\inventory_service.py

### Classes:

#### IInventoryService
Inherits from: ABC

Methods:
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
- get_low_stock_parts(self, include_out_of_stock)
- get_low_stock_leather(self, include_out_of_stock)

---

## services\interfaces\material_service.py

### Classes:

#### MaterialType
Inherits from: Enum

#### IMaterialService
Inherits from: ABC

Methods:
- create_material(self, material_data)
- get_material(self, material_id)
- update_material(self, material_id, material_data)
- delete_material(self, material_id)
- get_low_stock_materials(self, include_zero_stock)
- track_material_usage(self, material_id, quantity_used)
- search_materials(self, search_params)
- generate_sustainability_report(self)
- calculate_material_efficiency(self, material_id, period_days)

---

## services\interfaces\order_service.py

### Classes:

#### IOrderService
Inherits from: ABC

Methods:
- get_all_orders(self)
- get_order_by_id(self, order_id)
- get_order_by_number(self, order_number)
- create_order(self, order_data)
- update_order(self, order_id, order_data)
- delete_order(self, order_id)
- process_order_payment(self, order_id, payment_amount)
- get_orders_by_status(self, status)
- get_orders_by_customer(self, customer_name)
- get_order_statistics(self)
- cleanup(self)

---

## services\interfaces\project_service.py

### Classes:

#### ProjectType
Inherits from: Enum

#### SkillLevel
Inherits from: Enum

#### IProjectService
Inherits from: ABC

Methods:
- create_project(self, project_data)
- get_project(self, project_id, include_components)
- update_project(self, project_id, project_data)
- delete_project(self, project_id)
- search_projects(self, search_params)
- get_complex_projects(self, complexity_threshold)
- analyze_project_material_usage(self, project_id)
- generate_project_complexity_report(self)
- update_project_status(self, project_id, new_status)

---

## services\interfaces\recipe_service.py

### Classes:

#### IRecipeService
Inherits from: ABC

Methods:
- get_all_recipes(self)
- get_recipe_by_id(self, recipe_id)
- create_project(self, recipe_data)
- update_project(self, recipe_id, recipe_data)
- delete_project(self, recipe_id)
- check_materials_availability(self, recipe_id, quantity)
- calculate_production_cost(self, recipe_id, quantity)
- get_recipes_by_category(self, category)
- search_recipes(self, search_term)
- cleanup(self)

---

## services\interfaces\shopping_list_service.py

### Classes:

#### IShoppingListService
Inherits from: ABC

Methods:
- get_all_shopping_lists(self)
- get_shopping_list_by_id(self, list_id)
- create_shopping_list(self, list_data)
- update_shopping_list(self, list_id, list_data)
- delete_shopping_list(self, list_id)
- add_item_to_list(self, list_id, item_data)
- remove_item_from_list(self, list_id, item_id)
- mark_item_purchased(self, list_id, item_id, quantity)
- get_active_lists(self)
- get_lists_by_status(self, status)
- search_shopping_lists(self, search_term)
- get_pending_items(self)
- cleanup(self)

---

## services\interfaces\storage_service.py

### Classes:

#### IStorageService
Inherits from: ABC

Methods:
- get_all_storage_locations(self)
- get_storage_by_id(self, storage_id)
- create_storage_location(self, storage_data)
- update_storage_location(self, storage_id, storage_data)
- delete_storage_location(self, storage_id)
- search_storage_locations(self, search_term)
- get_storage_status(self, storage_id)

---

## services\interfaces\supplier_service.py

### Classes:

#### ISupplierService
Inherits from: ABC

Methods:
- get_all_suppliers(self)
- get_supplier_by_id(self, supplier_id)
- create_supplier(self, supplier_data)
- update_supplier(self, supplier_id, supplier_data)
- delete_supplier(self, supplier_id)
- get_supplier_performance(self, supplier_id, start_date, end_date)
- generate_supplier_report(self)

#### SupplierService
Inherits from: ISupplierService

Methods:
- __init__(self, container)
- _validate_supplier_data(self, supplier_data)
- get_all_suppliers(self)
- get_supplier_by_id(self, supplier_id)
- create_supplier(self, supplier_data)
- update_supplier(self, supplier_id, supplier_data)
- delete_supplier(self, supplier_id)
- get_supplier_performance(self, supplier_id, start_date, end_date)
- generate_supplier_report(self)

---

## services\interfaces\__init__.py

---

## gui\dialogs\add_dialog.py

### Classes:

#### AddDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, save_callback, fields, title)
- _create_ui(self)
- _on_save(self)

---

## gui\dialogs\base_dialog.py

### Classes:

#### BaseDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, title, size, modal)
- _create_main_frame(self)
- _create_button_frame(self)
- add_ok_cancel_buttons(self, ok_text, cancel_text, ok_command)
- add_button(self, text, command, side, width, default)
- center_on_parent(self)
- ok(self, event)
- cancel(self, event)
- validate(self)

---

## gui\dialogs\filter_dialog.py

### Classes:

#### FilterDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, columns, filter_callback)
- setup_ui(self)
- add_filter(self)
- remove_filter(self, filter_frame)
- get_filter_conditions(self)
- apply_filters(self)
- validate_numeric_filter(self, value, column)
- clear_filters(self)

---

## gui\dialogs\report_dialog.py

### Classes:

#### ReportDialog
Inherits from: BaseDialog

Methods:
- __init__(self, parent)
- create_ui(self)
- create_report_display(self, parent)
- update_options(self)
- on_report_type_change(self)
- generate_report(self)
- display_inventory_report(self)
- display_orders_report(self)
- display_suppliers_report(self)
- create_treeview(self, parent, columns, data)

---

## gui\dialogs\search_dialog.py

### Classes:

#### SearchDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, columns, search_callback)
- setup_ui(self)
- search(self)

---

## gui\dialogs\__init__.py

---

## gui\leatherworking\advanced_pattern_library.py

### Classes:

#### AdvancedPatternLibrary
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- setup_pattern_library(self)
- setup_pattern_list(self)
- setup_pattern_details(self)
- setup_toolbar(self)
- setup_test_suite(self)
- load_data(self)
- update_pattern_list(self)
- on_pattern_select(self, event)
- display_pattern_details(self, pattern_id)
- add_pattern(self)
- edit_pattern(self)
- delete_pattern(self)
- clear_pattern_details(self)
- import_patterns(self)
- export_patterns(self)
- run_tests(self)

#### PatternDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, title, pattern)
- setup_ui(self)
- setup_materials_ui(self)
- add_material(self)
- remove_material(self)
- select_image(self)
- save(self)
- cancel(self)

---

## gui\leatherworking\cost_analyzer.py

### Classes:

#### ProjectCostAnalyzer
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- create_toolbar(self)
- create_project_section(self)
- create_cost_section(self)
- create_cost_breakdown(self, parent)
- create_profitability_analysis(self, parent)
- create_pricing_recommendations(self, parent)
- load_projects(self)
- calculate_materials_cost(self, project)
- calculate_component_cost(self, component)
- calculate_total_cost(self, project)
- update_cost_breakdown(self)
- on_project_select(self, event)
- cleanup(self)
- load_settings(self)
- save_settings(self)
- update_labor_rate(self)
- update_profitability(self)

---

## gui\leatherworking\cost_estimator.py

### Classes:

#### CostEstimator
Inherits from: tk.Frame

Methods:
- __init__(self, parent, controller)
- _setup_layout(self)
- _create_cost_input(self)
- _create_cost_breakdown(self)
- _create_cost_visualization(self)
- _create_cost_summary(self)
- add_cost_item(self)
- recalculate_costs(self)
- _update_cost_distribution_chart(self)
- delete_selected_cost_item(self)
- show_context_menu(self, event)
- export_cost_report(self)
- load_initial_costs(self)

### Functions:
- main()

---

## gui\leatherworking\cutting_layout.py

### Classes:

#### LeatherPiece

#### LeatherCuttingView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- create_toolbar(self)
- load_data(self)
- refresh_canvas(self)
- draw_grid(self)
- draw_piece(self, piece)
- _get_color_for_priority(self, priority)
- on_canvas_click(self, event)
- on_drag(self, event)
- on_zoom(self, event)
- adjust_zoom(self, factor)
- update_grid(self, event)
- add_piece(self)
- clear_layout(self)
- export_layout(self)

#### MockApp

Methods:
- get_service(self, service_type)

### Functions:
- main()

---

## gui\leatherworking\leather_dialog.py

### Classes:

#### LeatherDetailsDialog
Inherits from: tk.Toplevel

Methods:
- __init__(self, parent, callback, initial_data)
- _create_main_frame(self)
- _create_input_fields(self)
- _create_buttons(self)
- _load_initial_data(self)
- _validate_input(self)
- _on_save(self)

### Functions:
- main()

---

## gui\leatherworking\leather_inventory.py

### Classes:

#### LeatherInventoryView
Inherits from: tk.Frame

Methods:
- __init__(self, parent, app)
- _setup_layout(self)
- _create_inventory_list(self)
- _create_analytics_section(self)
- _create_action_buttons(self)
- _add_leather_dialog(self)
- _add_leather(self, leather_data)
- _update_leather_dialog(self)
- _update_leather(self, updated_data)
- _delete_leather(self)
- _validate_leather_data(self, leather_data)
- _update_inventory_tree(self)
- _update_analytics(self)
- _show_leather_details(self, event)
- _show_context_menu(self, event)
- _generate_leather_report(self)
- _load_initial_leather_data(self)

### Functions:
- main()

---

## gui\leatherworking\material_calculator.py

### Classes:

#### MaterialCalculator
Inherits from: tk.Frame

Methods:
- __init__(self, parent, controller)
- _setup_layout(self)
- _create_material_input(self)
- _create_material_list(self)
- _create_calculation_summary(self)
- add_material(self)
- delete_selected_material(self)
- show_context_menu(self, event)
- recalculate_summary(self)
- export_material_report(self)
- load_initial_materials(self)

### Functions:
- main()

---

## gui\leatherworking\material_tracker.py

### Classes:

#### MaterialUsageTracker
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- create_toolbar(self)
- create_material_list(self)
- create_analytics_section(self)
- create_visualization(self)
- load_data(self)
- on_material_select(self, event)
- load_material_data(self, material_id)
- update_metrics(self)
- calculate_cost_per_unit(self)
- calculate_projected_usage(self)
- update_trend_analysis(self)
- calculate_period_efficiency(self, start_days, end_days)
- update_visualization(self)
- group_data_by_periods(self)
- draw_axes(self, margin, width, height)
- draw_usage_line(self, periods, margin, x_scale, y_scale, height)
- draw_efficiency_line(self, periods, margin, x_scale, y_scale, height)
- draw_period_labels(self, periods, margin, x_scale, height)
- get_days_for_range(self)
- export_data(self)

---

## gui\leatherworking\pattern_library.py

### Classes:

#### PatternLibrary
Inherits from: tk.Frame

Methods:
- __init__(self, parent, controller)
- _setup_layout(self)
- _create_pattern_input(self)
- browse_image(self)
- _create_pattern_list(self)
- _create_pattern_details(self)
- add_pattern(self)
- _update_pattern_tree(self)
- show_pattern_details(self, event)
- show_context_menu(self, event)
- edit_pattern(self)
- delete_pattern(self)
- load_initial_patterns(self)

### Functions:
- main()

---

## gui\leatherworking\project_dashboard.py

### Classes:

#### ProjectDashboard
Inherits from: tk.Frame

Methods:
- __init__(self, parent, controller)
- _setup_layout(self)
- _create_overview_section(self)
- _create_project_list(self)
- _create_quick_actions(self)
- load_data(self, projects)
- new_project(self)
- import_project(self)
- generate_report(self)

### Functions:
- main()

---

## gui\leatherworking\project_view.py

### Classes:

#### LeatherworkingProjectView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- create_toolbar(self)
- create_project_list(self)
- create_project_details(self)
- create_material_tracking(self)
- load_data(self)
- on_project_select(self, event)
- update_project_details(self, project)
- update_materials_list(self, project)
- show_new_project_dialog(self)
- show_add_material_dialog(self)
- remove_selected_material(self)
- delete_selected_project(self)
- export_project_report(self)
- filter_projects(self)
- show_error(self, title, message)
- cleanup(self)

---

## gui\leatherworking\timeline_viewer.py

### Classes:

#### TimelineViewer
Inherits from: tk.Frame

Methods:
- __init__(self, parent, controller)
- _setup_layout(self)
- _create_project_input(self)
- _create_timeline_chart(self)
- _create_project_list(self)
- add_project(self)
- update_timeline_chart(self)
- delete_selected_project(self)
- show_context_menu(self, event)
- load_initial_projects(self)

### Functions:
- main()

---

## gui\leatherworking\__init__.py

---

## gui\order\incoming_goods_view.py

### Classes:

#### IncomingGoodsView
Inherits from: BaseView

Methods:
- __init__(self, parent, session)
- _setup_ui(self)
- _create_toolbar(self)
- _create_content_area(self)
- _create_treeview(parent, columns, select_callback)
- _load_initial_data(self)
- _populate_orders_tree(self, orders)
- _on_order_select(self, event)
- _load_order_details(self, order_id)
- cleanup(self)

---

## gui\order\order_dialog.py

### Classes:

#### AddOrderDialog
Inherits from: BaseDialog

Methods:
- __init__(self, parent, save_callback, fields, suppliers, existing_data, title)
- _create_main_frame(self)
- _create_order_details_fields(self, parent)
- _create_order_items_section(self, parent)
- _show_add_item_dialog(self)
- _remove_selected_item(self)
- ok(self, event)
- validate(self)

---

## gui\order\order_view.py

### Classes:

#### OrderView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- setup_ui(self)
- _get_columns(self)
- _setup_treeview(self)
- load_data(self)
- show_add_dialog(self)
- delete_selected(self, event)
- on_double_click(self, event)
- _sort_column(self, col)
- _get_dialog_fields(self)
- show_search_dialog(self)
- _search_orders(self, search_term, columns)

---

## gui\order\shopping_list_view.py

### Classes:

#### ShoppingListView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- setup_table_selection(self)
- load_shopping_lists(self)
- show_add_list_dialog(self)
- on_list_select(self, event)
- load_list_items(self, list_id)
- show_add_item_dialog(self)

---

## gui\order\supplier_view.py

### Classes:

#### SupplierView
Inherits from: ttk.Frame

Methods:
- handle_return(self, event)
- handle_escape(self, event)
- show_search_dialog(self)
- show_filter_dialog(self)
- save_table(self)
- __init__(self, parent)
- setup_toolbar(self)
- setup_table(self)
- load_data(self)
- load_table(self)
- reset_view(self)
- show_add_dialog(self)
- delete_selected(self, event)
- on_double_click(self, event)
- start_cell_edit(self, item, column)
- undo(self)
- redo(self)
- sort_column(self, column)

---

## gui\order\__init__.py

---

## gui\product\project_view.py

### Classes:

#### RecipeView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- create_ui(self)
- create_toolbar(self)
- create_main_content(self)
- create_treeview(self, parent, columns, select_callback)
- create_status_bar(self)
- load_data(self)
- on_index_select(self, event)
- load_recipe_details(self, recipe_id)
- show_add_recipe_dialog(self)
- show_add_item_dialog(self)
- show_search_dialog(self)
- show_filter_dialog(self)
- delete_selected(self, tree)
- undo(self, event)
- redo(self, event)
- sort_column(self, tree, col)

---

## gui\product\storage_view.py

### Classes:

#### StorageView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent)
- setup_toolbar(self)
- setup_table(self)
- load_data(self)
- show_add_dialog(self)
- show_search_dialog(self)
- show_filter_dialog(self)
- delete_selected(self, event)
- on_double_click(self, event)
- start_cell_edit(self, item, column)
- undo(self, event)
- redo(self, event)
- reset_view(self)

---

## gui\product\__init__.py

---

## gui\recipe\project_view.py

### Classes:

#### RecipeView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- _find_database_file(self)
- setup_ui(self)
- create_toolbar(self)
- create_treeview(self)
- load_data(self)
- show_add_dialog(self)
- on_double_click(self, event)
- delete_selected(self, event)
- show_search_dialog(self)

---

## gui\recipe\__init__.py

---

## gui\reports\report_manager.py

---

## gui\reports\__init__.py

---

## gui\shopping_list\shopping_list_view.py

### Classes:

#### ShoppingListView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- _find_database_file(self)
- setup_ui(self)
- create_toolbar(self)
- create_treeview(self)
- load_data(self)
- show_add_dialog(self)
- on_double_click(self, event)
- delete_selected(self, event)
- show_search_dialog(self)

---

## gui\shopping_list\__init__.py

---

## gui\storage\fix_storage_view.py

### Functions:
- find_database_file()
- patch_storage_view(override)
- main()

---

## gui\storage\sorting_system_view.py

### Classes:

#### SortingSystemView
Inherits from: ttk.Frame

Methods:
- __init__(self, parent, session_factory)
- setup_toolbar(self)
- setup_table(self)
- load_data(self)
- get_warning_tag(self, amount, warning_threshold)
- show_add_dialog(self)
- save_new_item(self, data)
- generate_unique_id(self, name)
- on_double_click(self, event)
- start_cell_edit(self, item, column)
- delete_selected(self, event)
- undo(self)
- redo(self)

---

## gui\storage\storage_view.py

### Classes:

#### StorageView
Inherits from: BaseView

Methods:
- __init__(self, parent, app)
- _find_database_file(self)
- setup_ui(self)
- create_toolbar(self)
- create_treeview(self)
- load_data(self)
- show_add_dialog(self)
- on_double_click(self, event)
- delete_selected(self, event)
- show_search_dialog(self)

---

## gui\storage\__init__.py

---

## database\interfaces\base_repository.py

### Classes:

#### BaseRepository

Methods:
- __init__(self, session, model_class)
- get(self, id)
- get_all(self)
- create(self)
- update(self, id)
- delete(self, id)
- filter_by(self)
- exists(self)

---

## database\interfaces\__init__.py

---

## database\models\base.py

### Classes:

#### BaseModel
Inherits from: Base

Methods:
- __repr__(self)
- to_dict(self)

---

## database\models\base_transaction.py

### Classes:

#### BaseTransaction
Inherits from: BaseModel

Methods:
- __init__(self, transaction_type, notes)
- __repr__(self)
- to_dict(self)

---

## database\models\enums.py

### Classes:

#### OrderStatus
Inherits from: Enum

#### MaterialType
Inherits from: Enum

#### LeatherType
Inherits from: Enum

#### MaterialQualityGrade
Inherits from: Enum

#### InventoryStatus
Inherits from: Enum

#### ProjectType
Inherits from: Enum

#### SkillLevel
Inherits from: Enum

#### ProjectStatus
Inherits from: Enum

#### SupplierStatus
Inherits from: Enum

#### StorageLocationType
Inherits from: Enum

#### MeasurementUnit
Inherits from: Enum

#### Priority
Inherits from: Enum

#### TransactionType
Inherits from: Enum

#### QualityCheckStatus
Inherits from: Enum

#### PaymentStatus
Inherits from: Enum

---

## database\models\hardware.py

### Classes:

#### HardwareType
Inherits from: Enum

#### HardwareMaterial
Inherits from: Enum

#### Hardware
Inherits from: BaseModel

Methods:
- __repr__(self)
- is_low_stock(self)
- update_stock(self, quantity_change)
- to_dict(self)

---

## database\models\leather.py

### Classes:

#### Leather
Inherits from: BaseModel

Methods:
- __init__(self, name, leather_type, quality_grade, area, minimum_area)
- __repr__(self)
- to_dict(self)
- needs_reorder(self)

---

## database\models\material.py

### Classes:

#### MaterialType
Inherits from: Enum

#### LeatherType
Inherits from: Enum

#### MaterialQualityGrade
Inherits from: Enum

#### Material
Inherits from: BaseModel

Methods:
- __repr__(self)
- calculate_sustainability_impact(self)
- is_low_stock(self)
- update_stock(self, quantity_change)
- _trigger_reorder(self)

---

## database\models\metrics.py

### Classes:

#### MetricType
Inherits from: enum.Enum

#### TimeFrame
Inherits from: enum.Enum

#### MetricSnapshot
Inherits from: BaseModel

Methods:
- __repr__(self)

#### MaterialUsageLog
Inherits from: BaseModel

Methods:
- calculate_efficiency(self)

#### MetricsRepository

Methods:
- __init__(self, session)
- create_metric_snapshot(self, snapshot_data)
- get_latest_metrics(self, metric_type)
- get_metrics_history(self, metric_type, time_frame, start_date, end_date)
- log_material_usage(self, usage_data)
- get_material_usage_history(self, material_id, start_date, end_date)
- get_material_efficiency_stats(self, material_id, days)
- cleanup_old_metrics(self, days_to_keep)

#### DashboardService
Inherits from: IBaseService

Methods:
- __init__(self, container)
- get_dashboard_metrics(self)
- capture_metrics(self, time_frame)
- _get_inventory_metrics(self)
- _get_project_metrics(self)
- _get_material_usage(self)
- _get_supplier_metrics(self)
- _calculate_stock_percentage(self, items)
- _calculate_completion_rate(self, projects)
- _get_default_inventory_metrics(self)
- _get_default_project_metrics(self)
- _get_default_material_metrics(self)
- _get_default_supplier_metrics(self)

---

## database\models\order.py

### Classes:

#### Order
Inherits from: BaseModel

Methods:
- __init__(self)
- update_total(self)
- add_item(self, item)
- remove_item(self, item)
- to_dict(self)

#### OrderItem
Inherits from: BaseModel

Methods:
- __init__(self)
- update_total_price(self)
- to_dict(self)

---

## database\models\part.py

### Classes:

#### Part
Inherits from: BaseModel

---

## database\models\product.py

### Classes:

#### Product
Inherits from: BaseModel

Methods:
- __repr__(self)
- total_value(self)
- get_primary_recipe(self)
- calculate_production_cost(self)

---

## database\models\project.py

### Classes:

#### ProjectType
Inherits from: Enum

#### SkillLevel
Inherits from: Enum

#### ProductionStatus
Inherits from: Enum

#### Project
Inherits from: BaseModel

Methods:
- __repr__(self)
- calculate_complexity(self)
- update_quality_metrics(self, quality_rating, customer_satisfaction)

---

## database\models\project_component.py

### Classes:

#### ComponentType
Inherits from: Enum

#### ProjectComponent
Inherits from: BaseModel

Methods:
- __repr__(self)
- calculate_material_efficiency(self, actual_material_used, planned_material)

---

## database\models\recipe.py

### Classes:

#### Project
Inherits from: BaseModel

Methods:
- __repr__(self)
- calculate_total_cost(self)
- check_ingredient_availability(self)

#### ProjectComponent
Inherits from: BaseModel

Methods:
- __repr__(self)
- calculate_item_cost(self)
- is_available(self)

---

## database\models\shopping_list.py

### Classes:

#### ShoppingList
Inherits from: BaseModel

#### ShoppingListItem
Inherits from: BaseModel

---

## database\models\storage.py

### Classes:

#### Storage
Inherits from: Base

Methods:
- __init__(self, name, location, capacity, current_occupancy, type, description, status)
- __repr__(self)
- occupancy_percentage(self)

---

## database\models\supplier.py

### Classes:

#### Supplier
Inherits from: BaseModel

Methods:
- __init__(self, name, notes, rating)
- __repr__(self)
- to_dict(self)

---

## database\models\transaction.py

### Classes:

#### BaseTransaction
Inherits from: BaseModel

Methods:
- __init__(self, transaction_type, notes)
- __repr__(self)
- to_dict(self)

#### InventoryTransaction
Inherits from: BaseTransaction

Methods:
- __init__(self, part_id, quantity_change, transaction_type, notes)
- to_dict(self)

#### LeatherTransaction
Inherits from: BaseTransaction

Methods:
- __init__(self, leather_id, area_change, transaction_type, notes, wastage)
- to_dict(self)
- net_area_change(self)

---

## database\models\__init__.py

---

## database\repositories\hardware_repository.py

### Classes:

#### HardwareRepository

Methods:
- __init__(self, session)
- create_hardware(self, hardware_data)
- get_hardware_by_id(self, hardware_id)
- search_hardware(self, hardware_type, material, finish, min_stock, max_stock, min_load_capacity, max_load_capacity)
- update_hardware(self, hardware_id, update_data)
- delete_hardware(self, hardware_id)
- get_low_stock_hardware(self, include_zero_stock)
- get_hardware_by_supplier(self, supplier_id)
- generate_hardware_performance_report(self)

---

## database\repositories\leather_repository.py

### Classes:

#### LeatherRepository

Methods:
- __init__(self, session)
- get_low_stock(self)
- get_by_supplier(self, supplier_id)
- get_with_transactions(self, leather_id)

---

## database\repositories\material_repository.py

### Classes:

#### MaterialRepository

Methods:
- __init__(self, session)
- create_material(self, material_data)
- get_material_by_id(self, material_id)
- search_materials(self, material_type, leather_type, quality_grade, min_stock, max_stock)
- update_material(self, material_id, update_data)
- delete_material(self, material_id)
- get_low_stock_materials(self, include_zero_stock)
- get_materials_by_supplier(self, supplier_id)
- generate_sustainability_report(self)

---

## database\repositories\metrics_repository.py

### Classes:

#### MetricsRepository

Methods:
- __init__(self, session)
- create_metric_snapshot(self, snapshot_data)
- get_latest_metrics(self, metric_type)
- get_metrics_history(self, metric_type, time_frame, start_date, end_date)
- log_material_usage(self, usage_data)
- get_material_usage_history(self, material_id, start_date, end_date)
- get_material_efficiency_stats(self, material_id, days)
- cleanup_old_metrics(self, days_to_keep)

---

## database\repositories\order_repository.py

### Classes:

#### OrderRepository
Inherits from: BaseRepository

Methods:
- __init__(self, session)
- get_with_items(self, order_id)
- get_by_status(self, status)
- get_by_supplier(self, supplier_id)
- get_by_date_range(self, start_date, end_date)
- search(self, search_term, fields, limit)
- create(self, order)
- update(self, order_id, order)
- delete(self, order_id)

---

## database\repositories\part_repository.py

### Classes:

#### PartRepository

Methods:
- __init__(self, session)
- get_low_stock(self)
- get_by_supplier(self, supplier_id)
- get_with_transactions(self, part_id)

---

## database\repositories\product_repository.py

### Classes:

#### ProductRepository

Methods:
- __init__(self, session)
- get_by_storage(self, storage_id)
- search_by_name(self, name)

---

## database\repositories\project_repository.py

### Classes:

#### ProjectRepository
Inherits from: BaseRepository

Methods:
- __init__(self, session)
- get_project_with_details(self, project_id)
- search_projects(self, search_params, limit)
- get_project_material_usage(self, project_id)
- generate_project_complexity_report(self)
- create(self, project)
- update(self, project_id, project)

---

## database\repositories\recipe_repository.py

### Classes:

#### RecipeRepository

Methods:
- __init__(self, session)
- get_with_items(self, recipe_id)
- get_by_product(self, product_id)
- get_recipe_item(self, item_id)
- add_recipe_item(self, recipe_id, item_data)

---

## database\repositories\shopping_list_repository.py

### Classes:

#### ShoppingListRepository

Methods:
- __init__(self, session)
- get_with_items(self, list_id)
- get_pending_items(self)
- get_items_by_supplier(self, supplier_id)

---

## database\repositories\storage_repository.py

### Classes:

#### StorageRepository

Methods:
- get_by_location(self, location)
- get_available_storage(self)
- get_storage_with_details(self, storage_id)
- search_storage(self, search_term)

### Functions:
- get_storage_repository(session)

---

## database\repositories\supplier_repository.py

### Classes:

#### SupplierRepository
Inherits from: BaseRepository

Methods:
- __init__(self, session)
- search(self, search_term, fields, limit)
- get_supplier_orders(self, supplier_id, start_date, end_date)
- get_top_suppliers(self, limit, performance_metric)
- create(self, data)
- update(self, supplier_id, data)
- delete(self, supplier_id)

---

## database\repositories\__init__.py

---

## database\scripts\run_migration.py

### Functions:
- initialize_database()

---

## database\scripts\__init__.py

---

## database\sqlalchemy\base.py

### Classes:

#### CustomBase

Methods:
- __repr__(self)
- to_dict(self)

---

## database\sqlalchemy\base_manager.py

### Classes:

#### BaseManager

Methods:
- __init__(self, model_class, session_factory)
- _get_session(self)
- create(self, data)
- get(self, id)
- get_all(self, order_by, limit)
- update(self, id, data)
- delete(self, id)

### Functions:
- create_base_manager(model_class, session_factory)

---

## database\sqlalchemy\config.py

### Functions:
- get_database_url()
- _find_project_root()

---

## database\sqlalchemy\manager.py

### Classes:

#### DatabaseError
Inherits from: Exception

#### BaseManager

Methods:
- __init__(self, session_factory)
- session_scope(self)

#### DatabaseManagerSQLAlchemy

Methods:
- __init__(self, database_url)
- session(self)
- session_scope(self)
- get_model_columns(self, model)
- add_record(self, model, data)
- update_record(self, model, record_id, data)
- delete_record(self, model, record_id)
- get_record(self, model, record_id)
- get_all_records(self, model)
- search_records(self, model, search_term)
- bulk_update(self, model, updates)
- execute_query(self, query, params)

---

## database\sqlalchemy\manager_factory.py

### Classes:

#### ManagerFactory

Methods:
- register_specialized_manager(cls, model_class, manager_class)
- get_manager(cls, model_class, session_factory, mixins, force_new)
- clear_manager_cache(cls)

### Functions:
- register_specialized_manager(model_class, manager_class)

---

## database\sqlalchemy\migration.py

### Classes:

#### DatabaseInitializer

Methods:
- __init__(self, db_url, backup_dir)
- create_backup(self)
- drop_all_tables(self)
- initialize_database(self)

### Functions:
- run_database_initialization(db_url, backup_dir, force)

---

## database\sqlalchemy\models_file.py

---

## database\sqlalchemy\model_utils.py

### Functions:
- get_model_classes()

---

## database\sqlalchemy\session.py

### Functions:
- init_database()
- get_db_session()
- close_db_session()

---

## database\sqlalchemy\__init__.py

---

## database\sqlalchemy\core\base_manager.py

### Classes:

#### BaseManager

Methods:
- __init__(self, model_class, session_factory)
- session_scope(self)
- create(self, data)
- get(self, id)
- get_all(self, order_by, limit)
- update(self, id, data)
- delete(self, id)
- exists(self)
- count(self)
- filter_by(self)
- search(self, term, fields)
- bulk_create(self, items)
- bulk_update(self, items)

---

## database\sqlalchemy\core\manager_factory.py

### Functions:
- register_specialized_manager(model_class, manager_class)
- get_manager(model_class, session_factory, force_new)
- _create_manager(model_class, session_factory)
- clear_manager_cache()

---

## database\sqlalchemy\core\register_managers.py

### Functions:
- register_all_specialized_managers()

---

## database\sqlalchemy\core\__init__.py

---

## database\sqlalchemy\managers\incoming_goods_manager.py

### Classes:

#### IncomingGoodsManager

Methods:
- __init__(self)
- create_order(self, data)
- get_all_orders(self)
- get_order_by_id(self, order_id)
- get_order_by_number(self, order_number)
- update_order(self, order_id, data)
- delete_order(self, order_id)
- add_order_detail(self, order_id, data)
- get_order_details(self, order_id)
- update_order_detail(self, detail_id, data)
- delete_order_detail(self, detail_id)
- get_suppliers(self)
- update_inventory(self, unique_id, amount, is_shelf)

---

## database\sqlalchemy\managers\inventory_manager.py

### Classes:

#### InventoryManager

Methods:
- __init__(self, session_factory)
- add_part(self, data)
- add_leather(self, data)
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
- update_leather_stock(self, leather_id, area_change, transaction_type, notes)
- get_part_with_transactions(self, part_id)
- get_leather_with_transactions(self, leather_id)
- get_low_stock_parts(self, include_out_of_stock)
- get_low_stock_leather(self, include_out_of_stock)
- get_inventory_transactions(self, part_id, leather_id, start_date, end_date)
- get_inventory_value(self)
- search_inventory(self, search_term)
- adjust_min_stock_levels(self, part_id, new_min_level)
- adjust_min_leather_area(self, leather_id, new_min_area)
- get_inventory_summary(self)
- bulk_update_parts(self, updates)
- bulk_update_leather(self, updates)
- get_transaction_history(self, start_date, end_date, transaction_type)
- get_part_stock_history(self, part_id, days)
- get_leather_stock_history(self, leather_id, days)
- get_reorder_suggestions(self)

---

## database\sqlalchemy\managers\leather_inventory_manager.py

### Classes:

#### LeatherInventoryManager

Methods:
- __init__(self, session_factory)
- add_leather(self, data)
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
- get_leather_with_transactions(self, leather_id, include_wastage)
- get_low_stock_leather(self, include_out_of_stock, supplier_id)
- calculate_leather_efficiency(self, leather_id, date_range)
- adjust_minimum_area(self, leather_id, new_minimum)

---

## database\sqlalchemy\managers\order_manager.py

### Classes:

#### OrderManager

Methods:
- __init__(self, session_factory)
- create_order(self, order_data, items)
- get_order_with_items(self, order_id)
- update_order_status(self, order_id, status)
- add_order_items(self, order_id, items)
- remove_order_item(self, order_id, item_id)
- search_orders(self, search_term)
- get_orders_by_date_range(self, start_date, end_date)
- get_supplier_orders(self, supplier_id)
- calculate_order_total(self, order_id)

---

## database\sqlalchemy\managers\production_order_manager.py

### Classes:

#### ProductionOrderManager

Methods:
- __init__(self, session_factory)
- create_production_order(self, recipe_id, quantity, start_date, notes)
- start_production(self, order_id, operator_notes)
- _reserve_materials(self, session, order)
- complete_item(self, order_id, serial_number, quality_check_passed, notes)
- get_production_status(self, order_id)
- get_active_orders(self)
- get_production_metrics(self, start_date, end_date)

---

## database\sqlalchemy\managers\recipe_manager.py

### Classes:

#### RecipeManager

Methods:
- __init__(self, session_factory)
- create_project(self, recipe_data, items)
- get_recipe_with_items(self, recipe_id)
- update_recipe_items(self, recipe_id, items)
- add_recipe_item(self, recipe_id, item_data)
- remove_recipe_item(self, recipe_id, item_id)
- update_recipe_item_quantity(self, recipe_id, item_id, quantity)
- check_materials_availability(self, recipe_id, quantity)
- get_recipes_by_type(self, recipe_type)
- get_recipes_by_collection(self, collection)
- search_recipes(self, search_term)
- duplicate_recipe(self, recipe_id, new_name)
- calculate_recipe_cost(self, recipe_id)

---

## database\sqlalchemy\managers\report_manager.py

### Classes:

#### ReportManager
Inherits from: BaseManager

Methods:
- __init__(self, session)
- generate_report(self, report_type, filters)
- generate_inventory_report(self, filters)
- generate_products_report(self, filters)
- generate_low_stock_report(self, filters)
- generate_recipe_usage_report(self, filters)
- export_to_csv(self, df, filename)
- export_to_excel(self, df, filename)
- export_to_pdf(self, df, filename)

#### ReportDialog
Inherits from: BaseDialog

Methods:
- __init__(self, parent, title)
- setup_ui(self)
- on_report_type_change(self, event)
- _add_filter(self, name, label, widget_type)
- get_filters(self)
- generate_report(self)

---

## database\sqlalchemy\managers\shopping_list_manager.py

### Classes:

#### ShoppingListManager

Methods:
- __init__(self, session_factory)
- create_shopping_list(self, data, items)
- get_shopping_list_with_items(self, list_id)
- add_shopping_list_item(self, list_id, item_data)
- update_shopping_list_status(self, list_id, status)
- mark_item_purchased(self, list_id, item_id, purchase_data)
- get_pending_items(self)
- get_items_by_supplier(self, supplier_id)
- get_shopping_list_summary(self, list_id)
- search_shopping_lists(self, search_term)
- filter_shopping_lists(self, status, priority, date_range)
- bulk_update_items(self, updates, list_id)
- merge_shopping_lists(self, source_ids, target_id)
- get_overdue_items(self)

---

## database\sqlalchemy\managers\storage_manager.py

### Classes:

#### StorageManager

Methods:
- __init__(self, session_factory)
- get_all_storage_locations(self)
- add_storage_location(self, data)
- update_storage_location(self, location_id, data)
- delete_storage_location(self, location_id)
- get_storage_with_items(self, storage_id)
- get_available_storage(self)
- search_storage(self, term)
- get_storage_status(self, storage_id)
- get_storage_utilization(self)
- bulk_update_storage(self, updates)

---

## database\sqlalchemy\managers\supplier_manager.py

### Classes:

#### SupplierManager

Methods:
- __init__(self, session_factory)
- create_supplier(self, data)
- update_supplier(self, supplier_id, data)
- get_supplier_with_orders(self, supplier_id)
- get_supplier_products(self, supplier_id)
- get_supplier_performance(self, supplier_id)
- update_supplier_rating(self, supplier_id, rating, notes)
- get_supplier_order_history(self, supplier_id, start_date, end_date)
- get_top_suppliers(self, limit)
- get_supplier_categories(self, supplier_id)
- search_suppliers(self, search_term)
- get_supplier_statistics(self)

---

## database\sqlalchemy\managers\__init__.py

---

## database\sqlalchemy\migrations\manager.py

### Classes:

#### MigrationManager

Methods:
- __init__(self, database_url, migrations_path)
- _create_alembic_config(self)
- check_current_version(self)
- get_pending_migrations(self)
- create_backup(self)
- run_migrations(self, target)
- revert_migration(self, revision)
- verify_migration(self)

---

## database\sqlalchemy\migrations\migration_manager.py

### Classes:

#### MigrationCLI

Methods:
- create_migration(message)
- upgrade(revision)
- downgrade(revision)

#### MigrationTracker

Methods:
- get_current_version()

### Functions:
- get_base_metadata()
- run_migrations_offline(config, target_metadata)
- run_migrations_online(config, target_metadata)
- main(config_file)

---

## database\sqlalchemy\migrations\__init__.py

---

## database\sqlalchemy\mixins\base_mixins.py

### Classes:

#### BaseMixin

Methods:
- __init__(self, model_class, session_factory)

#### SearchMixin

Methods:
- search(self, search_term, fields)
- advanced_search(self, criteria)

#### FilterMixin

Methods:
- filter_by_multiple(self, filters)
- filter_with_or(self, filters)
- filter_complex(self, conditions, join_type)

#### PaginationMixin

Methods:
- get_paginated(self, page, page_size, order_by, filters)

#### TransactionMixin

Methods:
- run_in_transaction(self, operation)
- execute_with_result(self, operation)

---

## database\sqlalchemy\mixins\filter_mixin.py

### Classes:

#### FilterMixin

Methods:
- filter_by_multiple(self, filters)
- filter_with_or(self, filters)
- filter_complex(self, conditions, join_type)

---

## database\sqlalchemy\mixins\paginated_query_mixin.py

### Classes:

#### PaginatedQueryMixin

Methods:
- get_paginated(self, page, page_size, order_by, filters)

---

## database\sqlalchemy\mixins\search_mixin.py

### Classes:

#### SearchMixin

Methods:
- search(self, search_term, fields)
- advanced_search(self, criteria)

---

## database\sqlalchemy\mixins\test_mixin.py

### Classes:

#### TestModel
Inherits from: TestBase

#### TestModelManager
Inherits from: SearchMixin, FilterMixin, PaginationMixin, TransactionMixin

Methods:
- __init__(self, model_class, session_factory)

#### TestSearchMixin

Methods:
- test_basic_search(self, test_manager, sample_data)
- test_advanced_search(self, test_manager, sample_data)

#### TestFilterMixin

Methods:
- test_filter_by_multiple(self, test_manager, sample_data)
- test_filter_with_or(self, test_manager, sample_data)
- test_filter_complex(self, test_manager, sample_data)

#### TestPaginationMixin

Methods:
- test_pagination_basic(self, test_manager, session_factory)
- test_pagination_with_filters(self, test_manager, sample_data)

#### TestTransactionMixin

Methods:
- test_run_in_transaction_success(self, test_manager)
- test_run_in_transaction_rollback(self, test_manager)
- test_execute_with_result(self, test_manager)

### Functions:
- test_engine()
- session_factory(test_engine)
- test_manager(session_factory)
- sample_data(test_manager)

---

## database\sqlalchemy\mixins\test_mixin_perormance.py

### Classes:

#### PerformanceTestModel
Inherits from: TestBase

#### PerformanceTestManager
Inherits from: SearchMixin, FilterMixin, PaginationMixin

Methods:
- __init__(self, model_class, session_factory)

#### TestMixinPerformance

Methods:
- test_search_performance(self, performance_manager, large_dataset)
- test_advanced_search_performance(self, performance_manager, large_dataset)
- test_filter_performance(self, performance_manager, large_dataset)
- test_pagination_performance(self, performance_manager, large_dataset)
- test_complex_filter_performance(self, performance_manager, large_dataset)
- test_native_sqlalchemy_performance_comparison(self, performance_manager, large_dataset)

### Functions:
- test_engine()
- session_factory(test_engine)
- performance_manager(session_factory)
- large_dataset(performance_manager)

---

## database\sqlalchemy\mixins\transaction_mixin.py

### Classes:

#### TransactionMixin

Methods:
- run_in_transaction(self)
- execute_with_result(self, operation)

---

## database\sqlalchemy\mixins\__init__.py

---

## database\sqlalchemy\migrations\versions\202402201_add_relationships.py

### Functions:
- upgrade()
- downgrade()

---

## database\sqlalchemy\migrations\versions\20240222_add_metrics_tables.py

### Functions:
- upgrade()
- downgrade()

---

## database\sqlalchemy\migrations\versions\20240222_leatherworking_model_transformation.py

### Functions:
- upgrade()
- downgrade()

---

## database\sqlalchemy\migrations\versions\463698485_comprehensive_model_relationships.py

### Functions:
- upgrade()
- downgrade()

---

## database\sqlalchemy\migrations\versions\__init__.py

---

## database\sqlalchemy\core\specialized\leather_manager.py

### Classes:

#### LeatherManager
Inherits from: BaseManager

Methods:
- get_leather_with_transactions(self, leather_id)
- update_leather_area(self, leather_id, area_change, transaction_type, notes, wastage)
- get_low_stock_leather(self, include_out_of_stock, supplier_id)
- get_by_supplier(self, supplier_id)

---

## database\sqlalchemy\core\specialized\order_manager.py

### Classes:

#### OrderManager
Inherits from: BaseManager

Methods:
- __init__(self, session_factory)
- create_order(self, order_data)
- get_order_by_id(self, order_id)
- get_all_orders(self)

---

## database\sqlalchemy\core\specialized\part_manager.py

### Classes:

#### PartManager
Inherits from: BaseManager

Methods:
- get_part_with_transactions(self, part_id)
- update_part_stock(self, part_id, quantity_change, transaction_type, notes)
- get_low_stock_parts(self, include_out_of_stock)
- get_by_supplier(self, supplier_id)

---

## database\sqlalchemy\core\specialized\product_manager.py

### Classes:

#### ProductManager

Methods:
- get_product_with_recipe(self, product_id)
- get_by_storage(self, storage_id)
- assign_to_storage(self, product_id, storage_id)
- search_by_name(self, name)

---

## database\sqlalchemy\core\specialized\recipe_manager.py

### Classes:

#### RecipeManager

Methods:
- get_recipe_with_items(self, recipe_id)
- create_project(self, recipe_data, items)
- update_recipe_items(self, recipe_id, items)
- add_recipe_item(self, recipe_id, item_data)
- check_materials_availability(self, recipe_id, quantity)

---

## database\sqlalchemy\core\specialized\shopping_list_manager.py

### Classes:

#### ShoppingListManager
Inherits from: BaseManager

Methods:
- __init__(self, session_factory)
- get_shopping_list_with_items(self, list_id)
- create_shopping_list(self, data, items)
- mark_item_purchased(self, item_id, purchase_data)
- get_pending_items(self)
- get_items_by_supplier(self, supplier_id)
- get_shopping_list_summary(self, list_id)

---

## database\sqlalchemy\core\specialized\storage_manager.py

### Classes:

#### StorageManager
Inherits from: BaseManager

Methods:
- __init__(self, session_factory)

---

## database\sqlalchemy\core\specialized\supplier_manager.py

### Classes:

#### SupplierManager

Methods:
- get_supplier_with_orders(self, supplier_id)
- get_supplier_products(self, supplier_id)
- get_supplier_order_history(self, supplier_id, start_date, end_date)
- update_supplier_rating(self, supplier_id, rating, notes)
- search_suppliers(self, term)

---

## database\sqlalchemy\core\specialized\__init__.py

---
