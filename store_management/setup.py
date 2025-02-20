# setup.py
from setuptools import setup, find_packages

setup(
    name='store_management',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'SQLAlchemy',  # Or whatever database connector you need
        'alembic',
        'SQLAlchemy-Utils' # if you are using sqlalchemy utils
        # Add other dependencies here
    ],
)