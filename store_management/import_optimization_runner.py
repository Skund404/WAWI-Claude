# import_optimization_runner.py
import os
import sys
from utils.import_optimizer import ImportOptimizer


def run_import_optimization(project_root):
    """
    Run comprehensive import optimization for the project.

    Args:
        project_root (str): Root directory of the project
    """
    print("Starting Import Optimization Analysis")
    print("=====================================")

    try:
        # Ensure the project root is in the Python path
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Run import optimization
        results = ImportOptimizer.optimize_imports(project_root)

        # Display detailed results
        print("\nImport Optimization Results:")
        print("-------------------------")

        # Modules with potential circular dependencies
        if results.get('circular_dependencies'):
            print("\nPotential Circular Dependencies:")
            for module, dependencies in results['circular_dependencies'].items():
                print(f"- {module}:")
                for dep in dependencies:
                    print(f"  * {dep}")

        # Optimization suggestions
        if results.get('optimization_suggestions'):
            print("\nOptimization Suggestions:")
            for module, suggestions in results['optimization_suggestions'].items():
                print(f"- {module}:")
                for suggestion in suggestions:
                    print(f"  * {suggestion}")

        # Unused imports
        if results.get('unused_imports'):
            print("\nUnused Imports:")
            for module, imports in results['unused_imports'].items():
                print(f"- {module}:")
                for unused_import in imports:
                    print(f"  * {unused_import}")

        # Summary
        print("\nSummary:")
        print(f"Total modules analyzed: {results.get('total_modules', 0)}")
        print(f"Modules with potential circular dependencies: {len(results.get('circular_dependencies', []))}")
        print(f"Modules with optimization suggestions: {len(results.get('optimization_suggestions', []))}")
        print(f"Modules with unused imports: {len(results.get('unused_imports', []))}")

    except Exception as e:
        print(f"Error during import optimization: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Determine project root (assuming this script is in the project root)
    project_root = os.path.abspath(os.path.dirname(__file__))
    run_import_optimization(project_root)