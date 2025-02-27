# services/implementations/project_service.py
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from utils.circular_import_resolver import CircularImportResolver
from services.interfaces.project_service import IProjectService, ProjectType, SkillLevel


class ProjectService(IProjectService):
    """Implementation of the Project Service for managing leatherworking projects."""

    def __init__(self):
        """Initialize the project service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("ProjectService initialized")

        # In-memory storage for demonstration purposes
        self._projects = {}
        self._project_components = {}

    def create_project(self, name: str, project_type: ProjectType,
                       description: Optional[str] = None,
                       skill_level: SkillLevel = SkillLevel.BEGINNER,
                       deadline: Optional[datetime] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project.

        Args:
            name: Project name
            project_type: Type of project
            description: Optional project description
            skill_level: Skill level required
            deadline: Optional project deadline
            metadata: Additional project metadata

        Returns:
            Dict[str, Any]: Created project data
        """
        project_id = f"PRJ{len(self._projects) + 1:04d}"
        now = datetime.now()

        project = {
            "id": project_id,
            "name": name,
            "project_type": project_type,
            "description": description,
            "skill_level": skill_level,
            "deadline": deadline,
            "created_at": now,
            "updated_at": now,
            "status": "PLANNING",
            "progress": 0,
            "metadata": metadata or {},
        }

        self._projects[project_id] = project
        self._project_components[project_id] = []

        self.logger.info(f"Created project: {name} (ID: {project_id})")
        return project

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID.

        Args:
            project_id: ID of the project to retrieve

        Returns:
            Optional[Dict[str, Any]]: Project data or None if not found
        """
        project = self._projects.get(project_id)
        if not project:
            self.logger.warning(f"Project not found: {project_id}")
            return None

        # Add components
        project_copy = project.copy()
        project_copy["components"] = self._project_components.get(project_id, [])

        return project_copy

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a project.

        Args:
            project_id: ID of the project to update
            updates: Dictionary of fields to update

        Returns:
            Optional[Dict[str, Any]]: Updated project data or None if not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot update non-existent project: {project_id}")
            return None

        project = self._projects[project_id]

        # Update only valid fields
        valid_fields = [
            "name", "description", "skill_level", "project_type",
            "deadline", "status", "progress", "metadata"
        ]

        for field, value in updates.items():
            if field in valid_fields:
                project[field] = value

        # Always update the 'updated_at' timestamp
        project["updated_at"] = datetime.now()

        self.logger.info(f"Updated project: {project_id}")

        # Add components to the returned project
        project_copy = project.copy()
        project_copy["components"] = self._project_components.get(project_id, [])

        return project_copy

    def update_project_status(self, project_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        """Update the status of a project.

        Args:
            project_id: ID of the project
            new_status: New status to set

        Returns:
            Optional[Dict[str, Any]]: Updated project data or None if not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot update status of non-existent project: {project_id}")
            return None

        project = self._projects[project_id]
        old_status = project["status"]
        project["status"] = new_status
        project["updated_at"] = datetime.now()

        self.logger.info(f"Updated project {project_id} status from {old_status} to {new_status}")

        # Add components to the returned project
        project_copy = project.copy()
        project_copy["components"] = self._project_components.get(project_id, [])

        return project_copy

    def delete_project(self, project_id: str) -> bool:
        """Delete a project.

        Args:
            project_id: ID of the project to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot delete non-existent project: {project_id}")
            return False

        del self._projects[project_id]
        if project_id in self._project_components:
            del self._project_components[project_id]

        self.logger.info(f"Deleted project: {project_id}")
        return True

    def list_projects(self, project_type: Optional[ProjectType] = None,
                      skill_level: Optional[SkillLevel] = None) -> List[Dict[str, Any]]:
        """List all projects, optionally filtered by type or skill level.

        Args:
            project_type: Optional filter by project type
            skill_level: Optional filter by skill level

        Returns:
            List[Dict[str, Any]]: List of projects
        """
        result = []

        for project_id, project in self._projects.items():
            if project_type and project["project_type"] != project_type:
                continue

            if skill_level and project["skill_level"] != skill_level:
                continue

            project_copy = project.copy()
            project_copy["components"] = self._project_components.get(project_id, [])
            result.append(project_copy)

        return result

    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects by name or description.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching projects
        """
        query = query.lower()
        results = []

        for project_id, project in self._projects.items():
            if (query in project["name"].lower() or
                    (project["description"] and query in project["description"].lower())):
                project_copy = project.copy()
                project_copy["components"] = self._project_components.get(project_id, [])
                results.append(project_copy)

        return results

    def add_component_to_project(self, project_id: str,
                                 component_name: str,
                                 material_id: Optional[str] = None,
                                 material_type: Optional[str] = None,
                                 quantity: float = 1.0,
                                 dimensions: Optional[Dict[str, float]] = None,
                                 notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Add a component to a project.

        Args:
            project_id: ID of the project
            component_name: Name of the component
            material_id: Optional ID of the material
            material_type: Optional type of material
            quantity: Quantity needed
            dimensions: Optional component dimensions
            notes: Optional notes about the component

        Returns:
            Optional[Dict[str, Any]]: Updated project or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot add component to non-existent project: {project_id}")
            return None

        # Generate a component ID
        components = self._project_components.get(project_id, [])
        component_id = f"PC{len(components) + 1:03d}"

        # Create the component
        component = {
            "id": component_id,
            "name": component_name,
            "material_id": material_id,
            "material_type": material_type,
            "quantity": quantity,
            "dimensions": dimensions or {},
            "notes": notes,
            "created_at": datetime.now()
        }

        # Add to components list
        components.append(component)
        self._project_components[project_id] = components

        # Update project timestamp
        self._projects[project_id]["updated_at"] = datetime.now()

        self.logger.info(f"Added component {component_name} to project {project_id}")

        # Return the updated project
        updated_project = self._projects[project_id].copy()
        updated_project["components"] = components

        return updated_project

    def remove_component_from_project(self, project_id: str, component_id: str) -> Optional[Dict[str, Any]]:
        """Remove a component from a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component to remove

        Returns:
            Optional[Dict[str, Any]]: Updated project or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot remove component from non-existent project: {project_id}")
            return None

        components = self._project_components.get(project_id, [])

        # Find and remove the component
        for i, component in enumerate(components):
            if component["id"] == component_id:
                components.pop(i)
                self._project_components[project_id] = components
                self._projects[project_id]["updated_at"] = datetime.now()

                self.logger.info(f"Removed component {component_id} from project {project_id}")

                # Return the updated project
                updated_project = self._projects[project_id].copy()
                updated_project["components"] = components
                return updated_project

        self.logger.warning(f"Component {component_id} not found in project {project_id}")

        # Return the project without changes
        project = self._projects[project_id].copy()
        project["components"] = components
        return project

    def update_project_progress(self, project_id: str, progress: int) -> Optional[Dict[str, Any]]:
        """Update the progress of a project.

        Args:
            project_id: ID of the project
            progress: Progress percentage (0-100)

        Returns:
            Optional[Dict[str, Any]]: Updated project or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot update progress of non-existent project: {project_id}")
            return None

        # Ensure progress is between 0 and 100
        validated_progress = max(0, min(100, progress))

        project = self._projects[project_id]
        project["progress"] = validated_progress
        project["updated_at"] = datetime.now()

        # Update status based on progress if needed
        if validated_progress == 0:
            project["status"] = "PLANNING"
        elif validated_progress < 50:
            project["status"] = "IN_PROGRESS"
        elif validated_progress < 100:
            project["status"] = "FINISHING"
        else:
            project["status"] = "COMPLETED"

        self.logger.info(f"Updated project {project_id} progress to {validated_progress}%")

        # Return the updated project with components
        updated_project = project.copy()
        updated_project["components"] = self._project_components.get(project_id, [])

        return updated_project

    def get_projects_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get projects by status.

        Args:
            status: Project status to filter by

        Returns:
            List[Dict[str, Any]]: List of projects with the specified status
        """
        results = []

        for project_id, project in self._projects.items():
            if project["status"] == status:
                project_copy = project.copy()
                project_copy["components"] = self._project_components.get(project_id, [])
                results.append(project_copy)

        return results

    def get_complex_projects(self, min_components: int = 5) -> List[Dict[str, Any]]:
        """Get complex projects based on number of components.

        Args:
            min_components: Minimum number of components for a project to be considered complex

        Returns:
            List[Dict[str, Any]]: List of complex projects
        """
        results = []

        for project_id, project in self._projects.items():
            components = self._project_components.get(project_id, [])
            if len(components) >= min_components:
                project_copy = project.copy()
                project_copy["components"] = components
                results.append(project_copy)

        return results

    def get_projects_by_deadline(self, before_date: Optional[datetime] = None,
                                 after_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get projects by deadline.

        Args:
            before_date: Return projects with deadline before this date
            after_date: Return projects with deadline after this date

        Returns:
            List[Dict[str, Any]]: List of projects matching the deadline criteria
        """
        results = []

        for project_id, project in self._projects.items():
            deadline = project.get("deadline")
            if not deadline:
                continue

            matches = True

            if before_date and deadline > before_date:
                matches = False

            if after_date and deadline < after_date:
                matches = False

            if matches:
                project_copy = project.copy()
                project_copy["components"] = self._project_components.get(project_id, [])
                results.append(project_copy)

        return results

    def calculate_project_material_requirements(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Calculate material requirements for a project.

        Args:
            project_id: ID of the project

        Returns:
            Optional[Dict[str, Any]]: Material requirements or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot calculate materials for non-existent project: {project_id}")
            return None

        components = self._project_components.get(project_id, [])

        # Group materials by type and ID
        material_requirements = {}

        for component in components:
            material_type = component.get("material_type")
            material_id = component.get("material_id")

            if not material_type:
                continue

            key = f"{material_type}:{material_id}" if material_id else material_type

            if key not in material_requirements:
                material_requirements[key] = {
                    "material_type": material_type,
                    "material_id": material_id,
                    "quantity": 0
                }

            material_requirements[key]["quantity"] += component["quantity"]

        return {
            "project_id": project_id,
            "project_name": self._projects[project_id]["name"],
            "materials": list(material_requirements.values())
        }

    def analyze_project_material_usage(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Analyze material usage and efficiency for a project.

        Args:
            project_id: ID of the project

        Returns:
            Optional[Dict[str, Any]]: Material usage analysis or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot analyze materials for non-existent project: {project_id}")
            return None

        # Get basic requirements
        requirements = self.calculate_project_material_requirements(project_id)
        if not requirements:
            return None

        # Calculate additional metrics
        materials = requirements["materials"]
        total_quantity = sum(material["quantity"] for material in materials)

        # Calculate material diversity
        material_diversity = len(materials)

        # Generate analysis
        analysis = {
            "project_id": project_id,
            "project_name": self._projects[project_id]["name"],
            "total_material_quantity": total_quantity,
            "material_diversity": material_diversity,
            "material_breakdown": materials,
            "material_types": len(set(material["material_type"] for material in materials)),
            "estimated_waste_factor": 0.15,  # Assumed waste factor
            "estimated_total_with_waste": total_quantity * 1.15
        }

        self.logger.info(f"Analyzed material usage for project {project_id}")
        return analysis

    def generate_project_complexity_report(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Generate a complexity report for a project.

        Args:
            project_id: ID of the project

        Returns:
            Optional[Dict[str, Any]]: Project complexity report or None if project not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot generate complexity report for non-existent project: {project_id}")
            return None

        project = self._projects[project_id]
        components = self._project_components.get(project_id, [])

        # Basic complexity factors
        num_components = len(components)
        skill_level = project.get("skill_level")
        skill_level_value = 1  # Default value

        # Convert SkillLevel enum to numeric value
        if hasattr(skill_level, "value"):
            skill_level_value = skill_level.value
        elif isinstance(skill_level, int):
            skill_level_value = skill_level
        elif skill_level in [SkillLevel.BEGINNER, "BEGINNER"]:
            skill_level_value = 1
        elif skill_level in [SkillLevel.INTERMEDIATE, "INTERMEDIATE"]:
            skill_level_value = 2
        elif skill_level in [SkillLevel.ADVANCED, "ADVANCED"]:
            skill_level_value = 3
        elif skill_level in [SkillLevel.EXPERT, "EXPERT"]:
            skill_level_value = 4

        # Material diversity complexity
        material_types = set()
        for component in components:
            if component.get("material_type"):
                material_types.add(component.get("material_type"))

        material_diversity = len(material_types)

        # Calculate complexity score
        complexity_score = (
                (num_components * 0.5) +
                (skill_level_value * 2) +
                (material_diversity * 1.5)
        )

        # Complexity rating
        if complexity_score < 5:
            complexity_rating = "Simple"
        elif complexity_score < 10:
            complexity_rating = "Moderate"
        elif complexity_score < 15:
            complexity_rating = "Complex"
        else:
            complexity_rating = "Very Complex"

        # Estimated time calculation based on complexity
        base_hours = num_components * 0.5
        skill_factor = 1.0
        if skill_level_value == 1:
            skill_factor = 1.5  # Beginners take longer
        elif skill_level_value == 2:
            skill_factor = 1.2
        elif skill_level_value == 3:
            skill_factor = 1.0
        elif skill_level_value == 4:
            skill_factor = 0.8  # Experts work faster

        estimated_hours = base_hours * skill_factor

        # Generate report
        report = {
            "project_id": project_id,
            "project_name": project["name"],
            "complexity_score": complexity_score,
            "complexity_rating": complexity_rating,
            "number_of_components": num_components,
            "skill_level": skill_level_value if isinstance(skill_level_value, int) else str(skill_level),
            "material_diversity": material_diversity,
            "estimated_time": estimated_hours,
            "factors": {
                "component_count": num_components * 0.5,
                "skill_level": skill_level_value * 2,
                "material_diversity": material_diversity * 1.5
            }
        }

        self.logger.info(f"Generated complexity report for project {project_id}")
        return report

    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Duplicate a project.

        Args:
            project_id: ID of the project to duplicate
            new_name: Optional name for the duplicate

        Returns:
            Optional[Dict[str, Any]]: Duplicate project or None if original not found
        """
        if project_id not in self._projects:
            self.logger.warning(f"Cannot duplicate non-existent project: {project_id}")
            return None

        original = self._projects[project_id]
        components = self._project_components.get(project_id, [])

        # Create new project with same details but new ID and name
        duplicate_id = f"PRJ{len(self._projects) + 1:04d}"
        now = datetime.now()

        duplicate = {
            "id": duplicate_id,
            "name": new_name or f"Copy of {original['name']}",
            "project_type": original["project_type"],
            "description": original["description"],
            "skill_level": original["skill_level"],
            "deadline": None,  # Reset deadline
            "created_at": now,
            "updated_at": now,
            "status": "PLANNING",  # Reset status
            "progress": 0,  # Reset progress
            "metadata": original.get("metadata", {}).copy()
        }

        # Copy components
        duplicate_components = []
        for comp in components:
            duplicate_components.append({
                "id": f"PC{len(duplicate_components) + 1:03d}",
                "name": comp["name"],
                "material_id": comp.get("material_id"),
                "material_type": comp.get("material_type"),
                "quantity": comp["quantity"],
                "dimensions": comp.get("dimensions", {}).copy(),
                "notes": comp.get("notes"),
                "created_at": now
            })

        # Save the duplicate
        self._projects[duplicate_id] = duplicate
        self._project_components[duplicate_id] = duplicate_components

        self.logger.info(f"Duplicated project {project_id} to {duplicate_id}")

        # Return the full project with components
        result = duplicate.copy()
        result["components"] = duplicate_components
        return result