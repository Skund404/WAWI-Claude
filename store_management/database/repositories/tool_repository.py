# database/repositories/tool_repository.py
from database.models.tool import Tool
from database.repositories.base_repository import BaseRepository
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging

class ToolRepository(BaseRepository):
    def __init__(self, session: Session):
        """
        Initialize the Tool Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Tool)
        self.logger = logging.getLogger(self.__class__.__name__)

    def find_by_category(self, category) -> List[Tool]:
        """
        Find tools by their category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tools matching the category
        """
        try:
            return self.session.query(Tool).filter(Tool.type == category).all()
        except Exception as e:
            self.logger.error(f"Error finding tools by category: {e}")
            raise

    def create_tool(self, tool_data: Dict[str, Any]) -> Tool:
        """
        Create a new tool.

        Args:
            tool_data (Dict[str, Any]): Data for creating a new tool

        Returns:
            Created Tool instance
        """
        try:
            tool = Tool(**tool_data)
            self.session.add(tool)
            self.session.commit()
            return tool
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating tool: {e}")
            raise
