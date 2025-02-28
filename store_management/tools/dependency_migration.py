import os
import re
import json

# Define the target files and their paths
TARGET_FILES = [
    "application.py",
    "gui/main_window.py",
    "gui/inventory/inventory_view.py",
    "gui/order/order_view.py",
    "gui/leatherworking/pattern_library.py",
    "gui/product/project_view.py",
    "gui/storage/storage_view.py",
    "gui/shopping_list/shopping_list_view.py",
    "gui/order/supplier_view.py",
    "gui/leatherworking/material_calculator.py",
    "gui/leatherworking/cutting_layout.py",
    "gui/leatherworking/cost_analyzer.py",
    "gui/leatherworking/project_dashboard.py",
    "gui/leatherworking/advanced_pattern_library.py",
    "gui/leatherworking/leather_inventory.py",
    "gui/inventory/hardware_inventory.py",
    "gui/inventory/product_inventory.py",
]

# Define patterns to search for dependency retrieval
DEPENDENCY_PATTERNS = [
    r"self\.container\.get\((.*?)\)",  # Matches self.container.get(IMaterialService)
    r"container\.get\((.*?)\)",       # Matches container.get(IMaterialService)
    r"self\.get_service\((.*?)\)",    # Matches self.get_service(IMaterialService)
]

# Log file to store the extracted information
LOG_FILE = "dependency_extraction_log.json"

def extract_dependencies(file_path):
    """
    Extract dependencies from a file based on predefined patterns.
    """
    dependencies = []
    try:
        with open(file_path, "r") as file:
            content = file.read()

            # Search for direct calls to container.get or self.get_service
            for pattern in DEPENDENCY_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean up matches to extract service names
                    service_name = match.strip("\"'").split(",")[0]  # Handle cases like get(IMaterialService, ...)
                    dependencies.append(service_name)

            # Special case: Extract dependencies from the `views` list in MainWindow
            if "views = [" in content:
                view_pattern = r"'service':\s*(\w+)"  # Matches 'service': IMaterialService
                view_matches = re.findall(view_pattern, content)
                dependencies.extend(view_matches)

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return dependencies

def main():
    # Get the root directory of the project
    project_root = os.getcwd()

    # Dictionary to store extracted information
    extracted_info = {}

    for target_file in TARGET_FILES:
        file_path = os.path.join(project_root, target_file)
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            dependencies = extract_dependencies(file_path)
            extracted_info[target_file] = {
                "file_path": file_path,
                "dependencies": list(set(dependencies)),  # Remove duplicates
            }
        else:
            print(f"File not found: {file_path}")
            extracted_info[target_file] = {
                "file_path": file_path,
                "error": "File not found",
            }

    # Write the extracted information to a log file
    with open(LOG_FILE, "w") as log_file:
        json.dump(extracted_info, log_file, indent=4)

    print(f"Dependency extraction complete. Results saved to {LOG_FILE}")

if __name__ == "__main__":
    main()
