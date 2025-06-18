# Loggamera Integration Troubleshooting

This document provides solutions for common issues that might occur when using the Loggamera integration with Home Assistant.

## Table of Contents

- [SSL/TLS Certificate Issues](#ssltls-certificate-issues)
- [Connection Issues](#connection-issues)
- [Access Denied Errors](#access-denied-errors)
- [Missing Devices/Entities](#missing-devicesentities)
- [Data Update Issues](#data-update-issues)
- [Docker-specific Issues](#docker-specific-issues)

## SSL/TLS Certificate Issues

SSL/TLS certificate issues are common, especially in Docker environments where certificate authorities might not be properly installed.

### Certificate Issue Symptoms

- Error messages containing "CERTIFICATE_VERIFY_FAILED"
- Error messages about SSL/TLS verification
- Integration shows error "Cannot connect" during setup

### Certificate Issue Solutions

#### 1. Run the Diagnostic Script

The integration provides a diagnostic script that can help identify and fix certificate issues:

```bash
docker exec -it homeassistant bash -c "curl -s https://raw.githubusercontent.com/delize/ha-loggamera-integration/main/tools/diagnose_tls.sh | bash"
```

#### 2. Update CA Certificates

In Docker, you may need to update the CA certificates:

```bash
docker exec -it homeassistant bash -c "apt-get update && apt-get install -y ca-certificates"
```

#### 3. Update Certifi

Make sure the Python certifi package is up-to-date:

```bash
docker exec -it homeassistant bash -c "pip install --upgrade certifi"
```

#### 4. Custom CA Bundle

Create a custom CA certificate bundle:

```bash
docker exec -it homeassistant bash -c "mkdir -p /etc/ssl/certs/custom && cp /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/custom/cacert.pem"
```

Then, you'll need to modify the integration's API client to use this custom bundle.

## Connection Issues

If you're having trouble connecting to the Loggamera API:

### Connection Issue Symptoms

- "Cannot connect" errors during integration setup
- Timeout errors in logs

### Connection Issue Solutions

1. **Check Internet Connection**: Ensure your Home Assistant instance has proper internet access.

2. **Check Firewall Settings**: Make sure outbound connections to `platform.loggamera.se` on port 443 are allowed.

3. **DNS Resolution**: Verify that DNS resolution is working correctly.

```bash
docker exec -it homeassistant bash -c "ping platform.loggamera.se"
docker exec -it homeassistant bash -c "nslookup platform.loggamera.se"
```

## Access Denied Errors

If you're seeing "access denied" errors in the logs:

### Access Denied Symptoms

- Log entries with "API error: {'Message': 'access denied'}"
- Integration connects but doesn't show any devices

### Access Denied Solutions

1. **API Key**: Verify your API key is correct and has proper permissions.

2. **Organization ID**: Your API key might be tied to a specific organization. Try specifying the organization ID in the integration configuration.

3. **Check API Key Permissions**: Make sure your API key has access to the devices and data you're trying to access.

4. **API Key Revocation**: If your API key was revoked or expired, you'll need to get a new one.

5. **Reset the Integration**: Try removing and re-adding the integration with a correct API key.

## Missing Devices/Entities

If you've successfully connected but don't see your devices:

### Missing Devices Symptoms

- Integration shows as connected, but no devices/entities appear
- Some devices appear, but others are missing

### Missing Devices Solutions

1. **Wait for Discovery**: Sometimes it can take a few minutes for all devices to be discovered.

2. **Check Device Visibility**: Ensure your devices are visible in the Loggamera platform.

3. **Organization ID**: You might be using the wrong organization. Check if you have access to multiple organizations and specify the correct one.

4. **Restart Home Assistant**: Sometimes a full restart is needed for all entities to appear.

## Data Update Issues

If entities exist but don't update properly:

### Data Update Solutions

1. **Adjust Scan Interval**: Go to the integration options and adjust the scan interval. Default is 60 seconds.

2. **Check API Quotas**: Ensure you haven't exceeded API rate limits.

3. **Device Status**: Verify the devices are active and reporting data to Loggamera.

## Docker-specific Issues

Docker environments can have specific issues related to networking, certificates, and permissions:

### Docker-specific Solutions

1. **Certificate Path**: Docker containers might store certificates in different locations. Use the diagnostic script to identify the correct paths.

2. **Network Mode**: If using host network mode, ensure proper DNS resolution.

3. **Container Rebuilds**: After major Home Assistant updates, you might need to reinstall certificates.

```bash
docker exec -it homeassistant bash -c "apt-get update && apt-get install -y ca-certificates curl"
```

## Diagnostic Tools and Support Scripts

The integration includes **25+ comprehensive diagnostic tools** to help troubleshoot issues and provide support information. **Before opening a GitHub issue, please run the appropriate tools to gather diagnostic information.**

### Core Diagnostic Tools

#### 1. **Main Diagnostic Tool** (Primary)
```bash
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose
```
**What it does:**
- Tests API connectivity and SSL/TLS certificates
- Validates API key and organization access
- Discovers all devices and capabilities across all endpoints
- Tests all available API endpoints systematically
- Provides detailed error analysis and recommendations
- Generates comprehensive diagnostic summary

**When to use:** **Always run this first** for any connectivity, device discovery, or general issues.

#### 2. **Organization Mapper** (Complete Infrastructure Mapping)
```bash
python tools/organization_mapper.py YOUR_API_KEY --format json --verbose
python tools/organization_mapper.py YOUR_API_KEY --format markdown --output mapping.md
```
**What it does:**
- Maps ALL devices across ALL accessible organizations
- Discovers ALL sensors for each device type
- Tests endpoint coverage for each device
- Generates detailed reports in JSON, CSV, or Markdown format
- Provides comprehensive sensor statistics and mapping coverage
- Shows organization hierarchy and device relationships

**When to use:** When you need complete visibility into your Loggamera infrastructure, missing devices/sensors, or want to verify sensor mappings.

#### 3. **Connection Testing Tool** (Basic Connectivity)
```bash
python tools/test_connection.py YOUR_API_KEY [ORGANIZATION_ID]
```
**What it does:**
- Tests basic API connectivity with detailed SSL/TLS diagnostics
- Validates API key authentication
- Checks organization and device access permissions
- Provides system information for debugging (Python, OpenSSL, certificates)
- Tests DNS resolution and network connectivity

**When to use:** For basic connectivity troubleshooting, SSL certificate issues, or authentication problems.

### API Testing and Exploration Tools

#### 4. **API Explorer Tool** (Endpoint Testing)
```bash
python tools/loggamera_api_explorer.py YOUR_API_KEY ENDPOINT --device-id DEVICE_ID --verbose
```
**Examples:**
```bash
# Test Organizations endpoint
python tools/loggamera_api_explorer.py YOUR_API_KEY Organizations

# Test specific device endpoints
python tools/loggamera_api_explorer.py YOUR_API_KEY PowerMeter --device-id 12345
python tools/loggamera_api_explorer.py YOUR_API_KEY RawData --device-id 67890
```
**When to use:** When you need to test specific API endpoints, debug specific device issues, or explore API responses.

#### 5. **API Test Tool** (Basic API Validation)
```bash
python tools/api_test.py YOUR_API_KEY
```
**What it does:**
- Performs basic API functionality tests
- Validates core endpoint responses
- Quick API health check

**When to use:** Quick API validation or basic functionality testing.

### Sensor Mapping and Coverage Tools

#### 6. **Sensor Mapping Validation** (Comprehensive Coverage Analysis)
```bash
python tools/validate_sensor_mappings.py
```
**What it does:**
- Tests ALL sensor mappings across ALL organizations and devices
- Identifies unmapped sensors with detailed analysis
- Suggests mappings for new/unknown sensors with device class recommendations
- Validates endpoint coverage by device type
- Provides mapping coverage statistics and recommendations

**When to use:** When sensors are missing, showing as "Unknown", or you need to validate sensor coverage.

#### 7. **Coverage Testing Tools**
```bash
python tools/check_actual_coverage.py          # Real coverage using integration mappings
python tools/test_coverage_improvement.py      # Coverage improvement analysis
python tools/final_coverage_test.py           # Final coverage validation
```
**What they do:**
- Test actual sensor mapping coverage using real integration data
- Analyze coverage improvements and missing mappings
- Validate final sensor coverage completeness

**When to use:** When validating sensor mapping completeness or testing integration coverage.

### Device-Specific Testing Tools

#### 8. **PowerMeter Analysis Tools**
```bash
python tools/analyze_power_meter.py YOUR_API_KEY DEVICE_ID
python tools/basic_powermeter_output.py YOUR_API_KEY DEVICE_ID
python tools/test_powermeter.py YOUR_API_KEY
```
**What they do:**
- Analyze PowerMeter devices in detail
- Extract all available PowerMeter data points
- Test PowerMeter-specific functionality

**When to use:** For PowerMeter-specific issues, energy monitoring problems, or detailed power analysis.

#### 9. **PowerMeter Update Monitoring**
```bash
python tools/monitor_powermeter_updates.py --api-key YOUR_API_KEY --device-id DEVICE_ID --interval 60 --duration 24
python tools/analyze_update_frequency.py powermeter_logs/logfile.log
```
**What they do:**
- Monitor PowerMeter data updates over time (hours/days)
- Analyze update patterns and frequencies
- Generate update frequency statistics and recommendations
- Help determine optimal polling intervals

**When to use:** When experiencing data update issues, need to optimize polling intervals, or analyzing PowerMeter update patterns.

#### 10. **HeatMeter Testing Tools**
```bash
python tools/test_heatmeter_api.py
python tools/test_heatmeter_support.py
```
**What they do:**
- Test HeatMeter API functionality without Home Assistant
- Validate HeatMeter support and organization hierarchy
- Test HeatMeter sensor detection and mapping

**When to use:** For HeatMeter-specific issues, heating system monitoring problems, or RawData endpoint testing.

### Integration-Specific Testing Tools

#### 11. **Device Counter Testing** (Organization Sensors)
```bash
python tools/test_device_counter.py
python tools/test_device_counter_simple.py
```
**What they do:**
- Test device counter sensor functionality comprehensively
- Validate organization sensor availability and values
- Test edge cases and error handling for organization sensors
- Simulate Home Assistant integration scenarios

**When to use:** When organization sensors show as "Unavailable", have incorrect values, or display issues in Home Assistant.

#### 12. **Integration Log Testing**
```bash
python tools/test_integration_logs.py
python tools/validate_fix.py
```
**What they do:**
- Simulate Home Assistant integration scenarios
- Validate fixes for specific integration issues
- Test sensor availability and value correctness

**When to use:** When debugging Home Assistant integration issues or validating bug fixes.

#### 13. **User and Organization Testing**
```bash
python tools/test_user_count.py
```
**What it does:**
- Tests user count functionality in Organizations API
- Validates organization hierarchy and user data
- Tests organization sensor data accuracy

**When to use:** For organization management issues or user count sensor problems.

### Home Assistant Configuration Tools

#### 14. **HA Sensor Configuration Helper**
```bash
python tools/ha_sensor_config_helper.py YOUR_API_KEY DEVICE_ID
```
**What it does:**
- Generates YAML configuration snippets for Home Assistant dashboards
- Creates energy dashboard configuration
- Provides sensor entity configuration examples
- Helps with manual Home Assistant sensor setup

**When to use:** When setting up custom dashboards, energy monitoring, or need Home Assistant configuration examples.

### Network and SSL Tools

#### 15. **TLS/SSL Diagnostic Script**
```bash
bash tools/diagnose_tls.sh
```
**What it does:**
- Comprehensive SSL/TLS certificate diagnostics
- Tests certificate chains and validation
- Provides certificate fix recommendations
- Downloads and installs missing certificates

**When to use:** For SSL certificate issues, CERTIFICATE_VERIFY_FAILED errors, or Docker certificate problems.

#### 16. **Insecure API Client** (Testing Only)
```bash
python tools/api_client_insecure.py YOUR_API_KEY
```
**What it does:**
- Tests API connectivity without SSL verification (for debugging only)
- Helps isolate SSL-related issues from API problems
- **Use only for debugging SSL issues**

**When to use:** Only when SSL issues prevent normal API testing and you need to isolate the problem.

### Development and Maintenance Tools

#### 17. **Version Manager**
```bash
python tools/version_manager.py
```
**What it does:**
- Manages integration version information
- Validates version consistency across files

**When to use:** For development version management.

## Tool Usage for Support Requests

### For Connection Issues:
```bash
python tools/test_connection.py YOUR_API_KEY
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose
bash tools/diagnose_tls.sh
```

### For Missing Devices/Sensors:
```bash
python tools/organization_mapper.py YOUR_API_KEY --format json
python tools/validate_sensor_mappings.py
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose
```

### For Data Update Issues:
```bash
python tools/monitor_powermeter_updates.py --api-key YOUR_API_KEY --device-id DEVICE_ID --duration 2
python tools/analyze_power_meter.py YOUR_API_KEY DEVICE_ID
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose
```

### For "Unavailable" Sensors:
```bash
python tools/test_device_counter.py
python tools/test_integration_logs.py
python tools/validate_fix.py
```

### For Specific Device Issues:
- **PowerMeter**: `analyze_power_meter.py`, `monitor_powermeter_updates.py`
- **HeatMeter**: `test_heatmeter_api.py`, `test_heatmeter_support.py`
- **Organization**: `test_user_count.py`, `test_device_counter.py`

### For Sensor Mapping Issues:
```bash
python tools/validate_sensor_mappings.py
python tools/check_actual_coverage.py
python tools/organization_mapper.py YOUR_API_KEY --format markdown
```

## Creating Support Requests

When opening a GitHub issue, **please include the following information:**

### Required Information

1. **Integration Version**: Found in HACS or `manifest.json`
2. **Home Assistant Version**: Found in Settings > System > Repairs
3. **Installation Method**: HACS, Manual, etc.

### Diagnostic Output

**Always include output from these tools:**

1. **Main Diagnostic Tool** (Required):
```bash
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose > diagnostic_output.txt 2>&1
```

2. **Organization Mapping** (For device/sensor issues):
```bash
python tools/organization_mapper.py YOUR_API_KEY --format json > organization_mapping.json 2>&1
```

3. **Home Assistant Logs** with debug enabled:
```yaml
logger:
  default: warning
  logs:
    custom_components.loggamera: debug
```

### Issue Templates

#### For Connection Issues:
- Run `test_connection.py` and `loggamera_diagnostic.py`
- Include SSL certificate information
- Specify network environment (Docker, VM, etc.)

#### For Missing Devices/Sensors:
- Run `organization_mapper.py` to show complete device inventory
- Run `validate_sensor_mappings.py` to check sensor coverage
- Include organization structure information

#### For Data Update Issues:
- Run diagnostic tool with specific device IDs
- Include scan interval configuration
- Show specific sensor values that aren't updating

#### For "Unavailable" Sensors:
- Run `test_device_counter.py` for organization sensors
- Include sensor entity registry information
- Show specific sensors that are unavailable

### Tool Installation

All tools are located in the `tools/` directory of the integration. To use them:

1. Navigate to your custom components directory:
```bash
cd /config/custom_components/loggamera/tools
```

2. Install any missing dependencies:
```bash
pip install requests certifi
```

3. Make tools executable:
```bash
chmod +x *.py
```

4. Run the appropriate diagnostic tool before opening issues.

### API Key Security

⚠️ **Important**: When sharing diagnostic output:
- Replace your API key with `YOUR_API_KEY_HERE`
- Replace organization IDs with `YOUR_ORG_ID_HERE`
- Replace device IDs with generic numbers (e.g., `12345`)
- Remove any specific device names or identifiers

Example command to sanitize output:
```bash
python tools/loggamera_diagnostic.py YOUR_API_KEY --verbose | sed 's/YOUR_ACTUAL_API_KEY/YOUR_API_KEY_HERE/g' > sanitized_output.txt
```

## Advanced Troubleshooting

### Custom API Testing

Create custom test scripts using the integration's API client:

```python
from custom_components.loggamera.api import LoggameraAPI

api = LoggameraAPI("YOUR_API_KEY")
organizations = api.get_organizations()
devices = api.get_devices(org_id=YOUR_ORG_ID)
```

### Manual Sensor Testing

Test specific sensors manually:

```python
from custom_components.loggamera.sensor import LoggameraSensor
# Create and test individual sensors
```

### Endpoint Coverage Testing

Test which endpoints work with your devices:

```bash
python tools/organization_mapper.py YOUR_API_KEY --format markdown --verbose
```

This will show exactly which endpoints respond for each device type in your organization.

## Still Having Issues?

If you're still experiencing problems after running the diagnostic tools:

1. Check the [GitHub Issues](https://github.com/delize/ha-loggamera-integration/issues) for similar problems

2. **Create a new issue** with:
   - Complete diagnostic tool output
   - Organization mapping (with sensitive data removed)
   - Detailed problem description
   - Steps to reproduce the issue

3. **Review the [API Errata](API_ERRATA.md)** for known API limitations and workarounds

The diagnostic tools provide comprehensive information that helps developers quickly identify and resolve issues. Please use them before requesting support!
