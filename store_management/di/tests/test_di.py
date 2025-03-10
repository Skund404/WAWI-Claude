# test_di.py
from di import initialize, verify_container, resolve


def test_di_system():
    # Initialize the DI container
    container = initialize()

    # Verify the container
    is_valid = verify_container()
    print(f"Container verification: {'Passed' if is_valid else 'Failed'}")

    # Try resolving a service
    try:
        material_service = resolve('IMaterialService')
        print(f"Successfully resolved IMaterialService: {type(material_service).__name__}")
    except Exception as e:
        print(f"Failed to resolve IMaterialService: {str(e)}")


if __name__ == "__main__":
    test_di_system()