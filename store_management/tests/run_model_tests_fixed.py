#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/run_model_tests_fixed.py

"""
Standalone runner for leatherworking database model tests.
This bypasses pytest's automatic conftest loading.
"""

import sys
import os
import unittest

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the test classes directly from the fixed test file
try:
    from test_models_fixed import (
        TestDBSetup,
        TestCustomerModel,
        TestSupplierModel,
        TestMaterialModels,
        TestComponentModel,
        TestPatternModel,
        TestFullERDiagram
    )
except ImportError as e:
    print(f"Error importing test modules: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    print(f"Files in directory: {os.listdir(current_dir)}")
    sys.exit(1)

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()

    # Add test classes to the suite
    test_suite.addTest(unittest.makeSuite(TestDBSetup))
    test_suite.addTest(unittest.makeSuite(TestCustomerModel))
    test_suite.addTest(unittest.makeSuite(TestSupplierModel))
    test_suite.addTest(unittest.makeSuite(TestMaterialModels))
    test_suite.addTest(unittest.makeSuite(TestComponentModel))
    test_suite.addTest(unittest.makeSuite(TestPatternModel))
    test_suite.addTest(unittest.makeSuite(TestFullERDiagram))

    # Create test runner
    test_runner = unittest.TextTestRunner(verbosity=2)

    # Run the tests
    result = test_runner.run(test_suite)

    # Set exit code based on test result
    sys.exit(not result.wasSuccessful())