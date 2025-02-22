# File: import_test.py
import sys
import os

print("Python Path:")
for path in sys.path:
    print(path)

print("\nTrying to import store_management:")
try:
    import store_management

    print("Import successful!")
    print("Version:", store_management.__version__)
except Exception as e:
    print("Import failed:", e)

print("\nTrying to import from store_management:")
try:
    from store_management import main

    print("Main module import successful!")
except Exception as e:
    print("Main module import failed:", e)
