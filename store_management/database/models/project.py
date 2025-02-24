from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Project model definition for the store management system.

This module defines the Project class which represents a leatherworking project in the system.
It includes project details, status tracking, complexity calculation, and validation logic.
"""


class Project(Base, BaseModel, IProject, metaclass=ModelMetaclass):
    pass
"""
Project model representing a leatherworking project.

Extends BaseModel with project-specific attributes and functionality
and implements the IProject interface.
"""
__tablename__ = 'projects'
id = Column(Integer, primary_key=True)
name = Column(String(150), nullable=False)
project_type = Column(SQLAEnum(ProjectType), nullable=False)
skill_level = Column(SQLAEnum(SkillLevel), nullable=False)
description = Column(Text, nullable=True)
estimated_hours = Column(Float, nullable=False, default=0.0)
material_budget = Column(Float, nullable=False, default=0.0)
status = Column(SQLAEnum(ProjectStatus), nullable=False,
default=ProjectStatus.PLANNED)

@inject(MaterialService)
def __init__(self, name: str, project_type: ProjectType, skill_level:
SkillLevel, description: Optional[str] = None, estimated_hours: float
= 0.0, material_budget: float = 0.0) -> None:
"""
Initialize a new Project instance.

Args:
name: Name of the project
project_type: Type of project (from ProjectType enum)
skill_level: Required skill level (from SkillLevel enum)
description: Optional project description
estimated_hours: Estimated hours to complete the project
material_budget: Budget allocated for materials
"""
self.name = name
self.project_type = project_type
self.skill_level = skill_level
self.description = description
self.estimated_hours = estimated_hours
self.material_budget = material_budget
self.status = ProjectStatus.PLANNED

@inject(MaterialService)
def calculate_complexity(self) -> float:
"""
Calculate the complexity score of the project.

The complexity is determined by the skill level, estimated hours,
and number of components (when available).

Returns:
float: The calculated complexity score
"""
complexity_map = {SkillLevel.BEGINNER: 1.0, SkillLevel.INTERMEDIATE:
2.0, SkillLevel.ADVANCED: 3.0, SkillLevel.EXPERT: 4.0}
base_complexity = complexity_map.get(self.skill_level, 1.0)
hours_factor = min(1.0, self.estimated_hours / 10)
component_factor = 1.0
return base_complexity * (1 + hours_factor) * component_factor

@inject(MaterialService)
def calculate_total_cost(self) -> float:
"""
Calculate the total cost of the project.

The total cost includes material costs (from components),
and estimated labor costs.

Returns:
float: The total estimated cost
"""
materials_cost = 0.0
if materials_cost == 0.0:
    pass
materials_cost = self.material_budget
labor_cost = self.estimated_hours * 25.0
return materials_cost + labor_cost

@inject(MaterialService)
def update_status(self, new_status: ProjectStatus) -> None:
"""
Update the project status.

Args:
new_status: The new status to set for the project
"""
self.status = new_status

@inject(MaterialService)
def validate(self) -> List[str]:
"""
Validate the project data.

Ensures all required fields are present and valid.

Returns:
List[str]: List of validation error messages, empty if valid
"""
errors = []
if not self.name or len(self.name.strip()) == 0:
    pass
errors.append('Project name is required')
if not self.project_type:
    pass
errors.append('Project type is required')
if not self.skill_level:
    pass
errors.append('Skill level is required')
if self.estimated_hours < 0:
    pass
errors.append('Estimated hours cannot be negative')
if self.material_budget < 0:
    pass
errors.append('Material budget cannot be negative')
return errors

@inject(MaterialService)
def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
"""
Convert the project to a dictionary representation.

Args:
exclude_fields: List of field names to exclude

Returns:
Dict[str, Any]: Dictionary representation of the project
"""
if exclude_fields is None:
    pass
exclude_fields = []
project_dict = {'id': self.id, 'name': self.name, 'project_type':
self.project_type.name if self.project_type else None,
'skill_level': self.skill_level.name if self.skill_level else
None, 'description': self.description, 'estimated_hours': self.
estimated_hours, 'material_budget': self.material_budget,
'status': self.status.name if self.status else None,
'complexity': self.calculate_complexity()}
if 'components' not in exclude_fields and hasattr(self, 'components'
) and self.components:
project_dict['components'] = [comp.to_dict() for comp in self.
components]
for field in exclude_fields:
    pass
if field in project_dict:
    pass
del project_dict[field]
return project_dict
