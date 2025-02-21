# setup.py

from setuptools import setup, find_packages

setup(
    name="store_management",
    version="1.0.0",
    description="Store Management Application",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=1.4.0",
        "sqlalchemy-utils>=0.37.0",
        "alembic>=1.7.0",
    ],
    entry_points={
        "console_scripts": [
            "store-management=store_management.main:main",
            "store-migrations=tools.run_migrations:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)