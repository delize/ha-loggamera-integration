---
name: Bug report
about: Create a report to help us improve the Loggamera integration
title: '[BUG] '
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
 - Home Assistant Version: [e.g. 2023.12.0]
 - Integration Version: [e.g. 0.1.23]
 - Device Type: [e.g. PowerMeter, RoomSensor]

**Home Assistant Logs**
```
Please paste relevant logs here with debug logging enabled:

logger:
  default: warning
  logs:
    custom_components.loggamera: debug
```

**Device Information**
- Device ID: [Your device ID]
- Organization ID: [Your organization ID]
- Device Class: [e.g. PowerMeter, RoomSensor]

**Additional context**
Add any other context about the problem here.

**Diagnostic Information**
Please run the diagnostic tools and include relevant output:
```bash
python tools/test_powermeter.py YOUR_API_KEY --device-id YOUR_DEVICE_ID --verbose
```