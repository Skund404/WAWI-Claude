# Leatherworking Application Test Runner

## Overview

The test runner script (`run_tests_scripts.py`) is a versatile Python utility designed to streamline the process of running tests in the Leatherworking Application. It provides a flexible and automated way to execute test suites, manage virtual environments, and install dependencies.

## Features

- 🔍 Automatic test discovery
- 🌐 Cross-platform support (Windows, macOS, Linux)
- 📦 Virtual environment management
- 🛠 Dependency installation
- 🧪 Comprehensive test running capabilities

## Prerequisites

- Python 3.8+
- pip
- venv module

## Installation

No additional installation is required. The script is self-contained and will set up its environment automatically.

## Usage

### Basic Usage

```bash
python run_tests_scripts.py
```

This command will:
- Create a virtual environment (if not exists)
- Install required dependencies
- Run all tests in the current directory

### Advanced Usage

#### Specifying Test Directory
```bash
python run_tests_scripts.py -d path/to/test/directory
```

#### Filtering Test Files
```bash
python run_tests_scripts.py -p "test_specific_*.py"
```

#### Verbose Output
```bash
python run_tests_scripts.py -v
```

### Command-Line Options

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `--directory` | `-d` | Specify test directory | Current directory |
| `--pattern` | `-p` | Test file name pattern | `test_*.py` |
| `--venv` | | Virtual environment path | `.venv` |
| `--requirements` | | Custom requirements file | Project requirements.txt |
| `--verbose` | `-v` | Enable verbose output | False |

## Best Practices

1. Always run tests from the project root directory
2. Ensure all dependencies are listed in `requirements.txt`
3. Keep test files organized in a consistent structure
4. Use meaningful test method names

## Troubleshooting

### Common Issues

- **Virtual Environment Creation Fails**
  - Ensure you have the latest version of `venv`
  - Check Python installation
  - Verify write permissions

- **Dependency Installation Problems**
  - Check internet connection
  - Ensure pip is up to date
  - Verify requirements.txt is correctly formatted

### Logging

Test run logs and potential errors will be displayed in the console. For more detailed debugging, consider using verbose mode (`-v`).

## Configuration

### Requirements File

The script uses `requirements.txt` for dependency management. Ensure it contains all necessary testing libraries, such as:
- pytest
- sqlalchemy
- Any model-specific testing dependencies

## Contributing

### Adding New Tests

1. Place new test files in the `tests/betsy_validation/` directory
2. Follow naming convention: `test_*.py`
3. Use pytest for writing tests
4. Ensure tests are atomic and test specific functionality

## Performance Tips

- Use `-v` for detailed output during development
- Run specific test files or patterns for targeted testing
- Keep tests modular and focused

## License

[Specify your project's license]

## Contact

For issues or questions, please contact [Your Contact Information]