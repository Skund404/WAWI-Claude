# run_import_optimization.py
import os
import sys


def run_import_optimization():
    """
    Run import optimization for the project.
    """
    # Determine project root
    project_root = os.path.abspath(os.path.dirname(__file__))

    # Add project root to Python path
    sys.path.insert(0, project_root)

    try:
        from utils.import_optimizer import ImportOptimizer

        print("Starting Import Optimization Analysis")
        print("=====================================")

        # Run import optimization
        results = ImportOptimizer.optimize_imports(project_root)

        # Detailed reporting
        print("\n=== IMPORT OPTIMIZATION REPORT ===")

        # Circular Dependencies
        if results.get('circular_dependencies'):
            print("\n--- Potential Circular Dependencies ---")
            for module, dependencies in results['circular_dependencies'].items():
                print(f"Module: {module}")
                for dep in dependencies:
                    print(f"  - {dep}")

        # Optimization Suggestions
        if results.get('optimization_suggestions'):
            print("\n--- Import Optimization Suggestions ---")
            for module, suggestions in results['optimization_suggestions'].items():
                print(f"Module: {module}")
                for suggestion in suggestions:
                    print(f"  - {suggestion}")

        # Unused Imports
        if results.get('unused_imports'):
            print("\n--- Unused Imports ---")
            for module, imports in results['unused_imports'].items():
                print(f"Module: {module}")
                for unused_import in imports:
                    print(f"  - {unused_import}")

        # Summary
        print("\n=== SUMMARY ===")
        print(f"Total Modules Analyzed: {results.get('total_modules', 0)}")
        print(f"Modules with Circular Dependencies: {len(results.get('circular_dependencies', []))}")
        print(f"Modules with Optimization Suggestions: {len(results.get('optimization_suggestions', []))}")
        print(f"Modules with Unused Imports: {len(results.get('unused_imports', []))}")

    except ImportError as e:
        print(f"Error importing ImportOptimizer: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during import optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_import_optimization()