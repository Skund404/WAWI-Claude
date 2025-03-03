# database/models/model_metaclass.py
"""
Optional metaclass and base model configuration for additional model behaviors.
"""

from abc import ABCMeta
from typing import Any, Dict, Type, Optional

from sqlalchemy.orm import DeclarativeBase


class BaseModelInterface(ABCMeta):
    """
    An optional interface-like metaclass for models that provides
    additional type checking and behavior capabilities.
    """

    def __subclasshook__(cls, C: Type) -> Optional[bool]:
        """
        Custom subclass hook to determine if a class meets interface requirements.

        Args:
            C (Type): The class to check for interface compliance.

        Returns:
            Optional[bool]: Indication of interface compliance
        """
        # Add any specific method checks here if needed
        return NotImplemented

    def __init__(cls, name: str, bases: tuple, attrs: Dict[str, Any]):
        """
        Custom initialization to add additional validation or behavior.

        Args:
            name (str): Name of the class being created
            bases (tuple): Base classes
            attrs (Dict[str, Any]): Class attributes
        """
        # Optional: Add any global model initialization logic
        super().__init__(name, bases, attrs)



