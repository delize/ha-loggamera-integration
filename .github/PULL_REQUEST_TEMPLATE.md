# Pull Request

## Description
Brief description of changes made in this PR.

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue) - **PATCH version bump**
- [ ] ✨ New feature (non-breaking change which adds functionality) - **MINOR version bump**
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected) - **MAJOR version bump**
- [ ] 📚 Documentation update - **PATCH version bump**
- [ ] ♻️ Code refactoring - **PATCH version bump**

## Version Bump
When this PR is merged, the version will be automatically bumped based on the type of change in the title:
How It Works:

  For Automatic Releases (Most Common):
  1. Create PR with appropriate title:
    - [BUG] Fix sensor reading → PATCH bump (0.1.23 → 0.1.24)
    - [FEATURE] Add water meter support → MINOR bump (0.1.23 → 0.2.0)
    - [BREAKING] Change API structure → MAJOR bump (0.1.23 → 1.0.0)
  2. Merge PR → Automatically:
    - Detects version bump type
    - Updates manifest.json
    - Creates git tag
    - Generates release with notes
    - Comments on PR with release URL

To override the automatic detection, add one of these labels to the PR:
- `patch` - Force patch version bump
- `minor` - Force minor version bump  
- `major` - Force major version bump
- `breaking` - Force major version bump

## Testing
- [ ] Local testing performed
- [ ] Integration loads successfully in Home Assistant
- [ ] All existing functionality still works
- [ ] New functionality works as expected

## Device Testing
- [ ] Tested with PowerMeter devices
- [ ] Tested with RoomSensor devices  
- [ ] Tested with WaterMeter devices
- [ ] Tested with scenario controls

## Validation
- [ ] HACS validation passes
- [ ] hassfest validation passes
- [ ] Code quality checks pass
- [ ] No API keys or sensitive data in code
- [ ] Code follows existing patterns

## Documentation
- [ ] README updated if needed
- [ ] Code comments added for complex logic
- [ ] Breaking changes documented

## Release Notes
When this PR is merged, a new release will be automatically created. The release notes will include:
- This PR title and description
- Installation instructions
- Supported devices list
- Links to documentation

## Additional Notes
Any additional information about the changes.