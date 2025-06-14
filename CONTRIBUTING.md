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

3. **Set up pre-commit hooks** (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Quality

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run these before submitting:
```bash
black custom_components/
isort custom_components/
flake8 custom_components/
mypy custom_components/
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
5. **Run code quality checks**
6. **Commit with descriptive messages**
7. **Push to your fork**
8. **Create a Pull Request**

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
