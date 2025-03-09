#!/usr/bin/env python
"""
Python script to run the model tests.
This script sets up the test environment and runs the tests.
"""

import os
import sys
import subprocess
import unittest


def setup_environment():
    """Create necessary directories and __init__.py files."""
    print("Setting up test environment...")

    # Create directories if they don't exist
    os.makedirs("database/models", exist_ok=True)

    # Create empty __init__.py files if they don't exist
    init_files = [
        "database/__init__.py",
        "database/models/__init__.py",
        "utils/__init__.py"
    ]

    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                # Empty file
                pass
            print(f"Created {init_file}")

    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to Python path")

    print("Environment setup complete.")


def run_tests():
    """Discover and run the tests."""
    print("Running tests...")

    # Check if test_revised_models.py exists
    if not os.path.exists("test_revised_models.py"):
        print("Error: test_revised_models.py not found!")
        return False

    try:
        # If running from command line, use the unittest module directly
        if __name__ == "__main__":
            # Import the test module
            test_module_name = "test_revised_models"
            print(f"Importing test module: {test_module_name}")
            test_module = __import__(test_module_name)

            # Create a test loader
            loader = unittest.TestLoader()

            # Create a test suite
            suite = loader.loadTestsFromModule(test_module)

            # Create a test runner
            runner = unittest.TextTestRunner(verbosity=2)

            # Run the tests
            result = runner.run(suite)

            # Return True if tests succeeded, False otherwise
            return result.wasSuccessful()
        else:
            # If imported as a module, use subprocess
            result = subprocess.run([sys.executable, "test_revised_models.py", "-v"],
                                    check=False,
                                    capture_output=False)
            return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    setup_environment()
    success = run_tests()

    # Exit with appropriate status code
    sys.exit(0 if success else 1)