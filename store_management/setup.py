# File: setup.py
# Relative path: ./setup.py

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """
    Ensure the script is run with a compatible Python version.

    Raises:
        SystemExit: If Python version is incompatible.
    """
    min_version = (3, 9)
    if sys.version_info < min_version:
        print(f"Python {'.'.join(map(str, min_version))}+ is required.")
        sys.exit(1)


def install_dependencies():
    """
    Install project dependencies using pip.

    Raises:
        subprocess.CalledProcessError: If pip installation fails.
    """
    try:
        print("Installing project dependencies...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install dependencies. Please check your pip configuration.")
        sys.exit(1)


def create_virtual_environment():
    """
    Create a virtual environment for the project.

    Raises:
        subprocess.CalledProcessError: If venv creation fails.
    """
    venv_path = Path(".venv")
    if not venv_path.exists():
        try:
            print("Creating virtual environment...")
            subprocess.check_call(
                [sys.executable, "-m", "venv", str(venv_path)])
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError:
            print("Failed to create virtual environment.")
            sys.exit(1)


def main():
    """
    Main setup script to prepare the project environment.
    """
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    print("Project setup complete!")


if __name__ == "__main__":
    main()
