# database/repositories/project_repository.py
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, func, distinct
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.exc import SQLAlchemyError

from contextlib import contextmanager
from database.sqlalchemy.session import get_db_session


from database.repositories.base_repository import BaseRepository
from database.models.project import Project
from database.models.components import ProjectComponent  # Update this import
from database.models.enums import ProjectType, ProjectStatus, SkillLevel
from database.exceptions import DatabaseError
from utils.error_handler import (
    NotFoundError,
    ValidationError
)


class ProjectRepository(BaseRepository):
    """
    Advanced repository for project-related database operations.

    Provides comprehensive methods for querying, filtering,
    and managing project data with robust error handling.
    """

    def __init__(self, session=None):
        """
        Initialize the project repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Project)
        self.logger = logging.getLogger(__name__)
        if session is None:
            self.session = get_db_session()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        if self.session is None:
            self.session = get_db_session()

        session = self.session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

    def search_projects(self, query: str) -> List[Project]:
        """
        Search for projects by name or description.

        Args:
            query (str): Search term

        Returns:
            List[Project]: Projects matching the search query
        """
        try:
            with self.session_scope() as session:
                # Case-insensitive search across name and description
                results = (
                    session.query(Project)
                    .filter(
                        or_(
                            func.lower(Project.name).like(f"%{query.lower()}%"),
                            func.lower(Project.description).like(f"%{query.lower()}%")
                        )
                    )
                    .all()
                )

                self.logger.info(f"Search for '{query}' returned {len(results)} projects")
                return results

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to search projects with query '{query}': {str(e)}")
            raise DatabaseError(f"Database error searching projects: {str(e)}")

    def cleanup_old_projects(
            self,
            days_threshold: int = 365,
            status_filter: Optional[List[ProjectStatus]] = None,
            max_projects_to_delete: Optional[int] = None
    ) -> int:
        """
        Clean up old, inactive projects with advanced filtering options.

        Args:
            days_threshold (int): Number of days since last activity to consider for cleanup
            status_filter (Optional[List[ProjectStatus]]): Optional statuses to filter for cleanup
            max_projects_to_delete (Optional[int]): Maximum number of projects to delete

        Returns:
            int: Number of projects deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

            with self.session_scope() as session:
                # Prepare base query
                query = session.query(Project).filter(Project.updated_at < cutoff_date)

                # Add status filter if provided
                if status_filter:
                    query = query.filter(Project.status.in_(status_filter))
                else:
                    # Default inactive statuses if no filter provided
                    query = query.filter(
                        or_(
                            Project.status.in_([
                                ProjectStatus.PLANNING,
                                ProjectStatus.ON_HOLD,
                                ProjectStatus.CANCELLED
                            ]),
                            Project.is_completed == False
                        )
                    )

                # Optional: Limit number of projects to delete
                if max_projects_to_delete is not None:
                    query = query.limit(max_projects_to_delete)

                # Get projects to delete
                projects_to_delete = query.all()

                # Delete projects
                deleted_count = len(projects_to_delete)
                for project in projects_to_delete:
                    session.delete(project)

                session.commit()

                self.logger.warning(f"Cleaned up {deleted_count} inactive projects")
                return deleted_count

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to clean up old projects: {str(e)}")
            raise DatabaseError(f"Database error cleaning up projects: {str(e)}")

    def get_projects_by_status(
            self,
            status: ProjectStatus,
            page: int = 1,
            per_page: int = 20
    ) -> List[Project]:
        """
        Retrieve projects with a specific status with pagination.

        Args:
            status (ProjectStatus): Project status to filter by
            page (int): Page number for pagination
            per_page (int): Number of projects per page

        Returns:
            List[Project]: Projects with the specified status
        """
        try:
            with self.session_scope() as session:
                # Calculate offset
                offset = (page - 1) * per_page

                # Query projects by status with pagination
                projects = (
                    session.query(Project)
                    .filter(Project.status == status)
                    .order_by(Project.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                    .all()
                )

                # Get total count for logging
                total_count = session.query(Project).filter(Project.status == status).count()

                self.logger.info(
                    f"Retrieved {len(projects)} projects with status {status} "
                    f"(page {page}, total {total_count})"
                )

                return projects

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to retrieve projects with status {status}: {str(e)}")
            raise DatabaseError(f"Database error retrieving projects by status: {str(e)}")

    def get_complex_projects(
            self,
            min_components: int = 5,
            page: int = 1,
            per_page: int = 20
    ) -> List[Project]:
        """
        Retrieve projects with a high number of components.

        Args:
            min_components (int): Minimum number of components to consider a project complex
            page (int): Page number for pagination
            per_page (int): Number of projects per page

        Returns:
            List[Project]: Complex projects
        """
        try:
            with self.session_scope() as session:
                # Subquery to count components for each project
                subquery = (
                    session.query(ProjectComponent.project_id, func.count().label('component_count'))
                    .group_by(ProjectComponent.project_id)
                    .having(func.count() >= min_components)
                    .subquery()
                )

                # Query complex projects with pagination
                projects = (
                    session.query(Project)
                    .join(subquery, Project.id == subquery.c.project_id)
                    .order_by(subquery.c.component_count.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )

                # Get total count of complex projects
                total_count = (
                    session.query(func.count(distinct(subquery.c.project_id)))
                    .scalar()
                )

                self.logger.info(
                    f"Retrieved {len(projects)} complex projects "
                    f"(min {min_components} components, page {page}, total {total_count})"
                )

                return projects

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to retrieve complex projects: {str(e)}")
            raise DatabaseError(f"Database error retrieving complex projects: {str(e)}")

    def get_projects_by_deadline(
            self,
            before_date: Optional[datetime] = None,
            after_date: Optional[datetime] = None,
            page: int = 1,
            per_page: int = 20
    ) -> List[Project]:
        """
        Retrieve projects within a specific deadline range.

        Args:
            before_date (Optional[datetime]): Maximum deadline date
            after_date (Optional[datetime]): Minimum deadline date
            page (int): Page number for pagination
            per_page (int): Number of projects per page

        Returns:
            List[Project]: Projects matching the deadline criteria
        """
        try:
            with self.session_scope() as session:
                # Prepare query
                query = session.query(Project)

                # Apply deadline filters
                if before_date:
                    query = query.filter(Project.deadline <= before_date)

                if after_date:
                    query = query.filter(Project.deadline >= after_date)

                # Paginate and order results
                projects = (
                    query
                    .order_by(Project.deadline)
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )

                # Get total count
                total_count = query.count()

                self.logger.info(
                    f"Retrieved {len(projects)} projects by deadline "
                    f"(page {page}, total {total_count})"
                )

                return projects

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to retrieve projects by deadline: {str(e)}")
            raise DatabaseError(f"Database error retrieving projects by deadline: {str(e)}")

    def find_projects_by_complex_criteria(self, filters: Dict[str, Any]) -> List[Project]:
        """
        Find projects based on complex filter criteria.

        Args:
            filters (Dict[str, Any]): Dictionary of filter conditions

        Returns:
            List[Project]: Matching projects
        """
        try:
            with self.session_scope() as session:
                # Start with base query
                query = session.query(Project)

                # Apply filters based on provided criteria
                for key, value in filters.items():
                    if hasattr(Project, key):
                        query = query.filter(getattr(Project, key) == value)

                # Optional: Add support for specific enum types
                if 'project_type' in filters and isinstance(filters['project_type'], ProjectType):
                    query = query.filter(Project.project_type == filters['project_type'])

                if 'skill_level' in filters and isinstance(filters['skill_level'], SkillLevel):
                    query = query.filter(Project.skill_level == filters['skill_level'])

                if 'status' in filters and isinstance(filters['status'], ProjectStatus):
                    query = query.filter(Project.status == filters['status'])

                # Execute and return results
                results = query.all()

                self.logger.info(f"Found {len(results)} projects matching criteria: {filters}")
                return results

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to find projects with criteria {filters}: {str(e)}")
            raise DatabaseError(f"Database error finding projects: {str(e)}")