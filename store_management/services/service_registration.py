#!/usr/bin/env python3
# Path: service_registration.py
"""
Service Registration Script

This script registers service implementations with the dependency
injection container, mapping interfaces to concrete implementations.
"""

from di.core import DependencyContainer
from services.implementations.material_service import MaterialServiceImpl
from services.implementations.project_service import ProjectServiceImpl
from services.implementations.leather_service import LeatherService
from services.interfaces import MaterialService, ProjectService
from services.interfaces.leather_service import ILeatherService

# Register service implementations
DependencyContainer.register(MaterialService, MaterialServiceImpl)
DependencyContainer.register(ProjectService, ProjectServiceImpl)
DependencyContainer.register(ILeatherService, LeatherService)