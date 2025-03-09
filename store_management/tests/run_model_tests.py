#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/run_model_tests.py

"""
Standalone runner for leatherworking database model tests.
This bypasses pytest's automatic conftest loading.
"""

import sys
import unittest

# Import the test classes directly from the test file
from test_models import (
    TestDBSetup,
    TestCustomerModel,
    TestSupplierModel,
    TestMaterialModels,
    TestComponentModel,
    TestPatternModel,
    TestFullERDiagram
)

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