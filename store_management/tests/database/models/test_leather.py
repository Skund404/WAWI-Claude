# tests/database/models/test_leather.py
import pytest
from datetime import datetime

from database.models.enums import LeatherType, MaterialQualityGrade, InventoryStatus, TransactionType
from database.models.leather import Leather
from database.models.transaction import LeatherTransaction


class TestLeatherModel:
    """Test cases for the Leather model."""

    def test_create_leather(self):
        """Test creating a leather instance with valid data."""
        # Arrange
        leather_data = {
            "name": "Premium Veg Tan",
            "description": "High quality vegetable tanned leather",
            "leather_type": LeatherType.VEGETABLE_TANNED,
            "tannage": "Vegetable",
            "thickness_mm": 2.5,
            "size_sqft": 20.0,
            "grade": MaterialQualityGrade.PREMIUM,
            "color": "Natural",
            "finish": "Matte",
            "cost_per_sqft": 12.99,
            "quantity": 5,
            "location": "Shelf A-3"
        }

        # Act
        leather = Leather(**leather_data)

        # Assert
        assert leather.name == "Premium Veg Tan"
        assert leather.leather_type == LeatherType.VEGETABLE_TANNED
        assert leather.thickness_mm == 2.5
        assert leather.size_sqft == 20.0
        assert leather.grade == MaterialQualityGrade.PREMIUM
        assert leather.status == InventoryStatus.IN_STOCK  # Default value
        assert leather.quantity == 5
        assert leather.deleted is False  # Default value

    def test_validation_errors(self):
        """Test validation errors when creating a leather instance."""
        # Test missing required field
        with pytest.raises(ValueError):
            Leather(description="Test", leather_type=LeatherType.FULL_GRAIN, grade=MaterialQualityGrade.STANDARD)

        # Test invalid thickness
        with pytest.raises(ValueError):
            Leather(
                name="Test",
                leather_type=LeatherType.FULL_GRAIN,
                grade=MaterialQualityGrade.STANDARD,
                thickness_mm=-1.0
            )

        # Test invalid size
        with pytest.raises(ValueError):
            Leather(
                name="Test",
                leather_type=LeatherType.FULL_GRAIN,
                grade=MaterialQualityGrade.STANDARD,
                size_sqft=-5.0
            )

        # Test invalid quantity
        with pytest.raises(ValueError):
            Leather(
                name="Test",
                leather_type=LeatherType.FULL_GRAIN,
                grade=MaterialQualityGrade.STANDARD,
                quantity=-1
            )

    def test_update_leather(self):
        """Test updating a leather instance."""
        # Arrange
        leather = Leather(
            name="Test Leather",
            leather_type=LeatherType.FULL_GRAIN,
            grade=MaterialQualityGrade.STANDARD,
            quantity=10
        )

        # Act
        leather.update(
            name="Updated Leather",
            thickness_mm=3.0,
            color="Brown"
        )

        # Assert
        assert leather.name == "Updated Leather"
        assert leather.thickness_mm == 3.0
        assert leather.color == "Brown"
        assert leather.leather_type == LeatherType.FULL_GRAIN  # Unchanged

    def test_soft_delete_restore(self):
        """Test soft delete and restore functionality."""
        # Arrange
        leather = Leather(
            name="Test Delete",
            leather_type=LeatherType.CHROME_TANNED,
            grade=MaterialQualityGrade.ECONOMY,
            quantity=5
        )

        # Act - Soft delete
        leather.soft_delete()

        # Assert
        assert leather.deleted is True
        assert leather.status == InventoryStatus.DISCONTINUED

        # Act - Restore
        leather.restore()

        # Assert
        assert leather.deleted is False
        assert leather.status == InventoryStatus.IN_STOCK

    def test_adjust_quantity(self):
        """Test adjusting leather quantity."""
        # Arrange
        leather = Leather(
            name="Test Quantity",
            leather_type=LeatherType.FULL_GRAIN,
            grade=MaterialQualityGrade.PREMIUM,
            quantity=10
        )

        # Act - Add leather
        leather.adjust_quantity(5, TransactionType.PURCHASE, "Added more stock")

        # Assert
        assert leather.quantity == 15
        assert len(leather.transactions) == 1
        assert leather.transactions[0].quantity == 5
        assert leather.transactions[0].is_addition is True
        assert leather.transactions[0].transaction_type == TransactionType.PURCHASE

        # Act - Use leather
        leather.adjust_quantity(-3, TransactionType.USAGE, "Used in project")

        # Assert
        assert leather.quantity == 12
        assert len(leather.transactions) == 2
        assert leather.transactions[1].quantity == 3
        assert leather.transactions[1].is_addition is False
        assert leather.transactions[1].transaction_type == TransactionType.USAGE

        # Verify error on negative quantity
        with pytest.raises(ValueError):
            leather.adjust_quantity(-20, TransactionType.USAGE)

    def test_calculate_total_value(self):
        """Test calculating total value of leather."""
        # Arrange
        leather = Leather(
            name="Value Test",
            leather_type=LeatherType.FULL_GRAIN,
            grade=MaterialQualityGrade.PREMIUM,
            size_sqft=15.0,
            cost_per_sqft=10.0,
            quantity=3
        )

        # Act
        value = leather.calculate_total_value()

        # Assert
        assert value == 450.0  # 15 * 10 * 3

        # Test with missing cost data
        leather_no_cost = Leather(
            name="No Cost",
            leather_type=LeatherType.FULL_GRAIN,
            grade=MaterialQualityGrade.PREMIUM,
            quantity=5
        )
        assert leather_no_cost.calculate_total_value() == 0.0

    def test_to_dict(self):
        """Test converting leather to dictionary."""
        # Arrange
        leather = Leather(
            name="Dict Test",
            leather_type=LeatherType.NUBUCK,
            grade=MaterialQualityGrade.STANDARD,
            thickness_mm=1.8,
            size_sqft=12.5,
            color="Black",
            quantity=2
        )

        # Act
        result = leather.to_dict()

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "Dict Test"
        assert result["leather_type"] == "NUBUCK"
        assert result["grade"] == "STANDARD"
        assert result["thickness_mm"] == 1.8
        assert result["quantity"] == 2
        assert result["material_type"] == "LEATHER"