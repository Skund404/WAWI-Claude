from setuptools import setup, find_packages

setup(
    name='store_management',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'sqlalchemy>=2.0.0',
        'pytest',
        'sqlalchemy-utils',
    ],
    author='Your Name',
    author_email='your.email@example.com',
    description='A store management system for leatherworking',
    long_description=open('README.md').read() if open('README.md').read() else '',
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/store_management',
    classifiers=[
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.11',
)