# File: setup.py
from setuptools import setup, find_namespace_packages

setup(
    name="store-management",
    version="0.1.0",
    description="Store Management Application",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_namespace_packages(include=['store_management*']),
    install_requires=[
        "sqlalchemy>=2.0.19",
        "alembic>=1.11.1",
        "python-dotenv>=1.0.0",
        "sqlalchemy-utils>=0.41.1",
    ],
    entry_points={
        "console_scripts": [
            "store-management=store_management.main:main",
        ],
    },
    python_requires=">=3.9",
)