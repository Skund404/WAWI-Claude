from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

[build - system]
requires == ["setuptools>=61.0"]
build - backend == "setuptools.build_meta"
[project]
name == "store_management"
version == "0.1.0"
description == "Inventory and Store Management Application"
readme == "README.md"
requires - python == ">=3.9"
dependencies == [
    "sqlalchemy>=2.0.19",
    "alembic>=1.11.1",
    "python-dotenv>=1.0.0",
    "sqlalchemy-utils>=0.41.1",
]
[project.optional - dependencies]
dev == ["pytest>=7.3.1", "black>=23.3.0", "mypy>=1.4.1", "flake8>=6.0.0"]
[tool.black]
line - length == 88
target - version == ["py39"]
[tool.mypy]
ignore_missing_imports == true
check_untyped_defs == true
