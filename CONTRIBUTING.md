# Contributing to Loggamera Home Assistant Integration

Thank you for your interest in contributing to the Loggamera integration!

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/delize/home-assistant-loggamera-integration.git
   cd home-assistant-loggamera-integration
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Set up pre-commit hooks** (recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Quality

We use automated pre-commit hooks that run on every commit:

- **Black** for code formatting (100 character line length)
- **isort** for import sorting (compatible with Black)
- **flake8** for linting (excludes tests/ and tools/ directories)
- **yamllint** for YAML file validation
- **General checks** for trailing whitespace, file endings, and merge conflicts

The hooks will automatically run when you commit. To run manually:
```bash
pre-commit run --all-files
```

### Configuration Files
- **setup.cfg**: Configures flake8 with proper exclusions (tests/, tools/) and line length (100 chars)
- **.pre-commit-config.yaml**: Defines all pre-commit hooks and their settings
- **pyproject.toml**: Contains black, isort, and mypy configuration

### Manual Code Quality Checks
If you need to run tools manually:
```bash
black custom_components/
isort custom_components/
flake8 custom_components/  # Uses setup.cfg for configuration
```

## Testing

### Manual Testing
1. Copy the `custom_components/loggamera` directory to your Home Assistant instance
2. Restart Home Assistant
3. Test the integration with your Loggamera devices

### API Testing
Use the diagnostic tools to test API connectivity:
```bash
python tools/test_powermeter.py YOUR_API_KEY --device-id YOUR_DEVICE_ID --verbose
python tools/loggamera_api_explorer.py YOUR_API_KEY PowerMeter --device-id YOUR_DEVICE_ID
```

## Submitting Changes

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly**
5. **Pre-commit hooks will run automatically** (or run manually with `pre-commit run --all-files`)
6. **Commit with descriptive messages**
7. **Push to your fork**
8. **Create a Pull Request**

### Automated Workflows
- **Version Bumping**: Add labels (`major`, `minor`, `patch`, `bug`, `feature`, `documentation`) to PRs to trigger automatic version bumps
- **Auto-merge**: Version bump PRs are automatically merged after passing CI checks
- **Release Creation**: Use the Smart Release workflow to create GitHub releases with automatic changelog generation

## Guidelines

### Code Style
- Follow existing code patterns
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions focused and small

### Security
- **Never commit API keys or credentials**
- Use placeholder values like `YOUR_API_KEY` in examples
- Review code for sensitive information before committing

### Compatibility
- Ensure compatibility with Home Assistant 2023.1.0+
- Test with different Loggamera device types when possible
- Follow Home Assistant integration best practices

### Documentation
- Update README.md for user-facing changes
- Add code comments for complex logic
- Update manifest.json version for releases

## Device Support

When adding support for new device types:
1. Test with actual hardware when possible
2. Update sensor mappings in `sensor.py`
3. Add appropriate device classes and units
4. Update documentation with new device capabilities

## Getting Help

- Check existing issues and discussions
- Use the diagnostic tools to gather information
- Include relevant logs and device information in issues
- Be specific about your Home Assistant and integration versions

Thank you for contributing! 🎉
