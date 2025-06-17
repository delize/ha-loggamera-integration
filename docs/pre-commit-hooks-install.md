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
- **Black**: Code formatting (100 char line length)
- **isort**: Import sorting (compatible with Black)
- **flake8**: Linting (excludes tests/ and tools/ directories, configured via setup.cfg)
- **yamllint**: YAML syntax and style validation (100 char line length)
- **General**: Trailing whitespace, file endings, YAML/JSON validation, merge conflict detection
- **Pylint**: Home Assistant specific checks (only for custom_components/)

## Configuration Files
- **setup.cfg**: Contains flake8 configuration with proper excludes and line length settings
- **.pre-commit-config.yaml**: Defines all pre-commit hooks and their settings

## Manual formatting:
```bash
# Format all Python files
black --line-length=100 custom_components/

# Sort imports
isort --profile=black --line-length=100 custom_components/

# Check linting (uses setup.cfg for configuration)
flake8 custom_components/

# Check YAML files
yamllint .github/workflows/ custom_components/
```

## Troubleshooting
If hooks fail to install or run:
1. Ensure you have the latest versions: `pip install --upgrade pre-commit`
2. Clear cache: `pre-commit clean`
3. Reinstall hooks: `pre-commit install --overwrite`
