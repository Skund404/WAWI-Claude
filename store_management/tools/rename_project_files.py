#!/usr/bin/env python3
"""
Path: tools/rename_project_files.py

Script to systematically rename files and update references in a leatherworking project,
replacing generic 'recipe' terminology with more specific project-related terms.
"""

import os
import re
import sys
import logging
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectRenamer:
    """
    A comprehensive renaming utility for leatherworking project files and references.
    """

    def __init__(self, project_root: str):
        """
        Initialize the renaming utility with the project's root directory.

        Args:
            project_root (str): Root directory of the project
        """
        self.project_root = os.path.abspath(project_root)
        self.renames: Dict[str, str] = {
            # File renames
            'pattern_service.py': 'project_service.py',
            'recipe_repository.py': 'project_repository.py',
            'recipe_view.py': 'project_view.py',

            # Model class renames
            'Project': 'Project',
            'ProjectComponent': 'ProjectComponent',
        }

        # Search and replace patterns
        self.replacements: List[Tuple[str, str]] = [
            (r'\bRecipe\b', 'Project'),
            (r'\bRecipeItem\b', 'ProjectComponent'),
            (r'\brecipe_\b', 'project_'),
            (r'\bget_recipe\b', 'get_project'),
            (r'\bcreate_recipe\b', 'create_project'),
            (r'\bupdate_recipe\b', 'update_project'),
            (r'\bdelete_recipe\b', 'delete_project'),
        ]

    def _find_files(self, pattern: str = r'.*\.py$') -> List[str]:
        """
        Find all Python files in the project recursively.

        Args:
            pattern (str, optional): Regex pattern to match filenames. Defaults to Python files.

        Returns:
            List[str]: List of file paths matching the pattern
        """
        matches = []
        for root, _, filenames in os.walk(self.project_root):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if re.search(pattern, filepath):
                    matches.append(filepath)
        return matches

    def rename_files(self):
        """
        Rename files according to the predefined mapping.
        """
        for root, _, filenames in os.walk(self.project_root):
            for filename in filenames:
                old_path = os.path.join(root, filename)
                if filename in self.renames:
                    new_filename = self.renames[filename]
                    new_path = os.path.join(root, new_filename)
                    try:
                        os.rename(old_path, new_path)
                        logger.info(f'Renamed: {old_path} → {new_path}')
                    except Exception as e:
                        logger.error(f'Error renaming {old_path}: {e}')

    def update_file_contents(self):
        """
        Update file contents by replacing specific terms and references.
        """
        python_files = self._find_files()

        for filepath in python_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                modified = False
                for pattern, replacement in self.replacements:
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        modified = True

                if modified:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f'Updated: {filepath}')

            except Exception as e:
                logger.error(f'Error processing {filepath}: {e}')

    def run(self):
        """
        Execute the full renaming process.
        """
        logger.info('Starting project renaming process...')
        self.rename_files()
        self.update_file_contents()
        logger.info('Project renaming complete.')


def main():
    """
    Main execution point for the renaming script.
    """
    # Determine project root (assumes script is run from project root or tools directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    renamer = ProjectRenamer(project_root)
    renamer.run()


if __name__ == '__main__':
    main()