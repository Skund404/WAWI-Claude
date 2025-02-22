"""
File: database/sqlalchemy/models/__init__.py
Import models from main models package to prevent duplication.
"""
# Use the models from database.models instead of redefining them here
from database.models import *