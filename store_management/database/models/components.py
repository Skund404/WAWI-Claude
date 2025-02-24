

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class Component(BaseModel, Base, TimestampMixin, ValidationMixin, CostingMixin
    ):
    """
    Base class for components used in various contexts like projects and patterns.
    """
    __tablename__ = 'components'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    material_type = Column(String(100))
    quantity = Column(Float, nullable=False, default=0)
    unit_cost = Column(Float, nullable=False, default=0)
    component_type = Column(String(100))
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    pattern_id = Column(Integer, ForeignKey('patterns.id'), nullable=True)

        @inject(MaterialService)
        def __repr__(self):
        return (
            f"<Component(id={self.id}, name='{self.name}', type='{self.component_type}')>"
            )

        @inject(MaterialService)
        def calculate_total_cost(self):
        """
        Calculate the total cost of the component.

        Returns:
            float: Total cost of the component
        """
        return self.quantity * self.unit_cost

        @inject(MaterialService)
        def validate_component(self):
        """
        Validate the component's data.

        Raises:
            ValueError: If validation fails
        """
        self.validate_required_fields({'name': self.name, 'quantity': self.
            quantity, 'unit_cost': self.unit_cost})
        self.validate_numeric_range(self.quantity, 0, float('inf'))
        self.validate_numeric_range(self.unit_cost, 0, float('inf'))

        @inject(MaterialService)
        def to_dict(self, exclude_fields=None):
        """
        Convert the component to a dictionary representation.

        Args:
            exclude_fields (list, optional): Fields to exclude from the dictionary

        Returns:
            dict: Dictionary representation of the component
        """
        if exclude_fields is None:
            exclude_fields = []
        data = {'id': self.id, 'name': self.name, 'description': self.
            description, 'material_type': self.material_type, 'quantity':
            self.quantity, 'unit_cost': self.unit_cost, 'component_type':
            self.component_type, 'total_cost': self.calculate_total_cost()}
        for field in exclude_fields:
            data.pop(field, None)
        return data


class ProjectComponent(Component):
    """
    Specialized component for projects with additional tracking capabilities.
    """
    __tablename__ = 'project_components'
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    actual_material_used = Column(Float, default=0)
    planned_material = Column(Float, default=0)

        @inject(MaterialService)
        def calculate_material_efficiency(self, actual_material_used=None,
        planned_material=None):
        """
        Calculate material efficiency for the component.

        Args:
            actual_material_used (float, optional): Amount of material actually used
            planned_material (float, optional): Amount of material originally planned

        Returns:
            float: Material efficiency percentage
        """
        actual = actual_material_used or self.actual_material_used
        planned = planned_material or self.planned_material
        if planned == 0:
            return 0.0
        return (planned - (actual - planned)) / planned * 100

        @inject(MaterialService)
        def to_dict(self, exclude_fields=None):
        """
        Override to_dict to include project component specific fields.

        Args:
            exclude_fields (list, optional): Fields to exclude from the dictionary

        Returns:
            dict: Dictionary representation of the project component
        """
        data = super().to_dict(exclude_fields)
        data.update({'actual_material_used': self.actual_material_used,
            'planned_material': self.planned_material,
            'material_efficiency': self.calculate_material_efficiency()})
        return data


class PatternComponent(Component):
    """
    Specialized component for patterns with additional details.
    """
    __tablename__ = 'pattern_components'
    id = Column(Integer, ForeignKey('components.id'), primary_key=True)
    minimum_quantity = Column(Float, default=0)
    substitutable = Column(Integer, default=0)
    stitch_type = Column(String(100))
    edge_finish_type = Column(String(100))

        @inject(MaterialService)
        def can_substitute(self, alternate_material_type):
        """
        Check if the component can be substituted with another material type.

        Args:
            alternate_material_type (str): Material type to check for substitution

        Returns:
            bool: Whether substitution is possible
        """
        return bool(self.substitutable
            ) and self.material_type != alternate_material_type

        @inject(MaterialService)
        def to_dict(self, exclude_fields=None):
        """
        Override to_dict to include pattern component specific fields.

        Args:
            exclude_fields (list, optional): Fields to exclude from the dictionary

        Returns:
            dict: Dictionary representation of the pattern component
        """
        data = super().to_dict(exclude_fields)
        data.update({'minimum_quantity': self.minimum_quantity,
            'substitutable': bool(self.substitutable), 'stitch_type': self.
            stitch_type, 'edge_finish_type': self.edge_finish_type})
        return data
