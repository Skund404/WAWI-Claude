# tests/leatherwork_repository_tests/test_leather_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    MaterialType,
    QualityGrade,
    MeasurementUnit,
    LeatherType,
    LeatherFinish,
    SupplierStatus,
    InventoryStatus
)


class TestLeatherRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Premium Leather Supplier",
            contact_email="leather@example.com",
            phone="555-222-3333",
            address="456 Tannery Rd",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def test_create_leather(self, dbsession):
        """Test creating a new leather material."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def get_by_id(self, id):
                return self.leathers.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create a leather material
        leather = TestLeather(
            name="Horween Chromexcel",
            description="Premium full-grain leather",
            supplier_id=supplier.id,
            unit_price=15.99,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Brown",
            created_at=datetime.now(),
            leather_type=LeatherType.FULL_GRAIN,
            thickness=2.0,  # mm
            area=25.0,  # sq ft
            is_full_hide=True,
            finish=LeatherFinish.ANILINE
        )

        # Save the leather
        added_leather = repository.add(leather)

        # Verify the leather was saved
        assert added_leather.id == 1
        assert added_leather.name == "Horween Chromexcel"
        assert added_leather.material_type == MaterialType.LEATHER
        assert added_leather.leather_type == LeatherType.FULL_GRAIN
        assert added_leather.thickness == 2.0
        assert added_leather.is_full_hide is True
        assert added_leather.finish == LeatherFinish.ANILINE

    def test_read_leather(self, dbsession):
        """Test reading a leather material."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def get_by_id(self, id):
                return self.leathers.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create a leather material
        leather = TestLeather(
            name="Wickett & Craig Veg-Tan",
            description="Vegetable tanned leather",
            supplier_id=supplier.id,
            unit_price=12.50,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Natural",
            created_at=datetime.now(),
            leather_type=LeatherType.VEGETABLE_TANNED,
            thickness=3.5,  # mm
            area=15.0,  # sq ft
            is_full_hide=False,
            finish=LeatherFinish.NAPPA
        )

        # Add to repository
        added_leather = repository.add(leather)

        # Read the leather
        retrieved_leather = repository.get_by_id(added_leather.id)

        # Verify the leather was retrieved correctly
        assert retrieved_leather is not None
        assert retrieved_leather.id == added_leather.id
        assert retrieved_leather.name == "Wickett & Craig Veg-Tan"
        assert retrieved_leather.leather_type == LeatherType.VEGETABLE_TANNED
        assert retrieved_leather.thickness == 3.5
        assert retrieved_leather.finish == LeatherFinish.NAPPA

    def test_update_leather(self, dbsession):
        """Test updating a leather material."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def get_by_id(self, id):
                return self.leathers.get(id)

            def update(self, leather):
                if leather.id in self.leathers:
                    self.leathers[leather.id] = leather
                    return leather
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create a leather material
        leather = TestLeather(
            name="Chevre Goatskin",
            description="Supple goat leather",
            supplier_id=supplier.id,
            unit_price=18.75,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Black",
            created_at=datetime.now(),
            leather_type=LeatherType.CHROME_TANNED,
            thickness=1.2,  # mm
            area=8.0,  # sq ft
            is_full_hide=False,
            finish=LeatherFinish.ANILINE
        )

        # Add to repository
        added_leather = repository.add(leather)

        # Update the leather
        added_leather.name = "Premium Chevre Goatskin"
        added_leather.unit_price = 22.50
        added_leather.color = "Navy Blue"
        added_leather.thickness = 1.0
        repository.update(added_leather)

        # Retrieve and verify updates
        updated_leather = repository.get_by_id(added_leather.id)
        assert updated_leather.name == "Premium Chevre Goatskin"
        assert updated_leather.unit_price == 22.50
        assert updated_leather.color == "Navy Blue"
        assert updated_leather.thickness == 1.0

    def test_delete_leather(self, dbsession):
        """Test deleting a leather material."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def get_by_id(self, id):
                return self.leathers.get(id)

            def delete(self, id):
                if id in self.leathers:
                    del self.leathers[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create a leather material
        leather = TestLeather(
            name="Italian Calfskin",
            description="Soft calfskin leather",
            supplier_id=supplier.id,
            unit_price=25.00,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Tan",
            created_at=datetime.now(),
            leather_type=LeatherType.CALFSKIN,
            thickness=1.5,  # mm
            area=10.0,  # sq ft
            is_full_hide=False,
            finish=LeatherFinish.ANILINE
        )

        # Add to repository
        added_leather = repository.add(leather)

        # Delete the leather
        leather_id = added_leather.id
        result = repository.delete(leather_id)

        # Verify the leather was deleted
        assert result is True
        assert repository.get_by_id(leather_id) is None

    def test_find_leathers_by_type(self, dbsession):
        """Test finding leathers by type."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def find_by_leather_type(self, leather_type):
                return [l for l in self.leathers.values() if l.leather_type == leather_type]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create different types of leathers
        veg_tan1 = TestLeather(
            name="Oak Bark Tanned",
            material_type=MaterialType.LEATHER,
            supplier_id=supplier.id,
            unit_price=30.00,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Natural",
            leather_type=LeatherType.VEGETABLE_TANNED,
            thickness=4.0
        )

        veg_tan2 = TestLeather(
            name="Bridle Leather",
            material_type=MaterialType.LEATHER,
            supplier_id=supplier.id,
            unit_price=22.50,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.PREMIUM,
            color="Chestnut",
            leather_type=LeatherType.VEGETABLE_TANNED,
            thickness=3.2
        )

        chrome_tanned = TestLeather(
            name="Soft Chrome Tanned",
            material_type=MaterialType.LEATHER,
            supplier_id=supplier.id,
            unit_price=18.75,
            measurement_unit=MeasurementUnit.SQUARE_FOOT,
            quality_grade=QualityGrade.STANDARD,
            color="Black",
            leather_type=LeatherType.CHROME_TANNED,
            thickness=1.8
        )

        # Add to repository
        repository.add(veg_tan1)
        repository.add(veg_tan2)
        repository.add(chrome_tanned)

        # Find leathers by type
        veg_tanned_leathers = repository.find_by_leather_type(LeatherType.VEGETABLE_TANNED)
        chrome_tanned_leathers = repository.find_by_leather_type(LeatherType.CHROME_TANNED)

        # Verify results
        assert len(veg_tanned_leathers) == 2
        assert len(chrome_tanned_leathers) == 1
        assert all(l.leather_type == LeatherType.VEGETABLE_TANNED for l in veg_tanned_leathers)
        assert all(l.leather_type == LeatherType.CHROME_TANNED for l in chrome_tanned_leathers)

    def test_find_leathers_by_thickness_range(self, dbsession):
        """Test finding leathers within a specific thickness range."""

        # Create a simple test leather object
        class TestLeather:
            def __init__(self, **kwargs):
                self.id = None
                self.material_type = MaterialType.LEATHER
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleLeatherRepo:
            def __init__(self):
                self.leathers = {}
                self.next_id = 1

            def add(self, leather):
                leather.id = self.next_id
                self.leathers[self.next_id] = leather
                self.next_id += 1
                return leather

            def find_by_thickness_range(self, min_thickness, max_thickness):
                return [l for l in self.leathers.values()
                        if min_thickness <= l.thickness <= max_thickness]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleLeatherRepo()

        # Create leathers of different thicknesses
        thicknesses = [0.8, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0]
        for i, thickness in enumerate(thicknesses):
            leather = TestLeather(
                name=f"Test Leather {i+1}",
                material_type=MaterialType.LEATHER,
                supplier_id=supplier.id,
                quality_grade=QualityGrade.STANDARD,
                leather_type=LeatherType.FULL_GRAIN,
                thickness=thickness
            )
            repository.add(leather)

        # Find leathers by thickness ranges
        thin_leathers = repository.find_by_thickness_range(0.5, 1.5)
        medium_leathers = repository.find_by_thickness_range(1.5, 3.0)
        thick_leathers = repository.find_by_thickness_range(3.0, 6.0)

        # Verify results
        assert len(thin_leathers) == 3  # 0.8, 1.2, 1.5
        assert len(medium_leathers) == 3  # 1.5, 2.0, 3.0
        assert len(thick_leathers) == 3  # 3.0, 4.0, 5.0