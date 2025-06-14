# Pre-commit Hooks Installation

## Quick Setup

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Install the hooks:
```bash
pre-commit install
```

3. Run on all files (optional):
```bash
pre-commit run --all-files
```

## What the hooks do:
- **Black**: Code formatting (88 char line length)
- **isort**: Import sorting (compatible with Black)
- **flake8**: Linting with relaxed rules
- **General**: Trailing whitespace, file endings, YAML/JSON validation
- **Pylint**: Home Assistant specific checks

## Manual formatting:
```bash
# Format all Python files
black --line-length=88 custom_components/

# Sort imports
isort --profile=black --line-length=88 custom_components/

# Check linting
flake8 custom_components/ --max-line-length=88
```
