# Loggamera Integration for Home Assistant
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
[![GitHub license](https://img.shields.io/github/license/delize/home-assistant-loggamera-integration.svg?style=flat-square)](https://github.com/delize/home-assistant-loggamera-integration/blob/main/LICENSE)


[![Release Date](https://img.shields.io/github/release-date/delize/home-assistant-loggamera-integration?label=Latest%20Release&color=green)](https://github.com/delize/home-assistant-loggamera-integration/releases/latest) [![Latest Stable](https://img.shields.io/github/v/release/delize/home-assistant-loggamera-integration?label=Stable&color=blue)](https://github.com/delize/home-assistant-loggamera-integration/releases/latest) [![Pre-Release Date](https://img.shields.io/github/release-date-pre/delize/home-assistant-loggamera-integration?label=Latest%20Pre-Release&color=orange)](https://github.com/delize/home-assistant-loggamera-integration/releases) [![Latest Pre-Release](https://img.shields.io/github/v/release/delize/home-assistant-loggamera-integration?include_prereleases&label=Pre-Release&color=orange)](https://github.com/delize/home-assistant-loggamera-integration/releases)


[![Validate with hassfest](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/hacs-hassfest.yaml/badge.svg?branch=main)](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/hassfest.yaml)
[![HACS Action](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/hacs-validation.yaml/badge.svg?branch=main)](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/hacs.yaml)
[![Code Quality](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/delize/home-assistant-loggamera-integration/actions/workflows/lint.yaml)
[![Latest Commit](https://badgen.net/github/last-commit/delize/home-assistant-loggamera-integration/main)](https://github.com/delize/home-assistant-loggamera-integration/commit/HEAD)


This integration allows you to monitor your Loggamera devices in Home Assistant, providing comprehensive energy monitoring and device control capabilities.

## Supported Devices

- **PowerMeter** (Electricity meters) - Monitor energy consumption and power usage
- **RoomSensor** (Temperature and humidity sensors) - Track environmental conditions
- **WaterMeter** (Water meters) - Monitor water consumption
- **CoolingUnit** - Monitor and control cooling systems
- **HeatPump** - Monitor and control heat pump systems

## Features

### Core Functionality
- **Energy Monitoring**: Monitor power consumption in real-time with full Home Assistant Energy dashboard integration
- **Environmental Sensors**: Track temperature and humidity readings from room sensors
- **Water Usage**: Monitor water consumption from water meters
- **Scenario Control**: Execute predefined scenarios through switches
- **Alarm Monitoring**: Binary sensors for device alarm states
- **Multi-Device Support**: Manage multiple Loggamera devices from a single integration

### Advanced Sensor Management
- **Clean Device Interface**: Each device type gets appropriate primary sensors (PowerMeter → 4 clean sensors, WaterMeter → standard water sensors, etc.)
- **Detailed RawData Sensors**: Additional detailed sensors available via RawData endpoint (disabled by default to prevent entity spam)
- **Smart Entity Naming**: Clear naming patterns distinguish between standard sensors (`loggamera_{device_id}_{sensor}`) and detailed sensors (`rawdata_{device_id}_{device_type}_{sensor}`)
- **Dynamic Sensor Detection**: Automatically detects and properly configures unknown sensors using intelligent analysis of API metadata
- **User Control**: Standard sensors enabled by default, detailed sensors can be manually enabled per user preference

### Developer Experience
- **Comprehensive Diagnostics**: Built-in diagnostic tools for troubleshooting
- **Robust API Handling**: Intelligent endpoint selection with graceful fallbacks
- **Future-Proof Architecture**: Handles new device types and unknown sensors automatically
- **Extensive Logging**: Detailed logging for debugging and development

## Example Screenshot

![Example Screenshot of Sensor Data](docs/assets/README/demo-screenshot.png)

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository: `https://github.com/delize/home-assistant-loggamera-integration`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Loggamera" in HACS and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/delize/home-assistant-loggamera-integration/releases)
2. Extract the contents and copy the `custom_components/loggamera` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Development

This project uses automated workflows and code quality tools:

### Automated Version Management
- **Automatic Version Bumping**: PRs with appropriate labels (`major`, `minor`, `patch`) automatically trigger version bumps
- **Smart Release Workflow**: Creates GitHub releases with automatic changelog generation
- **Auto-merge**: Version bump PRs are automatically merged after passing all checks

### Code Quality
- **Pre-commit Hooks**: Automated code formatting and linting on every commit
- **Continuous Integration**: All PRs are validated with hassfest, HACS, and custom linting
- **YAML Linting**: All workflow files are validated for proper syntax

For development setup, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Configuration

The integration is configured through the Home Assistant UI:

1. Go to Configuration > Integrations
2. Click "Add Integration"
3. Search for "Loggamera"
4. Enter your API key (found in the Loggamera portal, you may need to reach out to Loggamera)

## Available Entities

The integration creates various entity types based on your Loggamera devices:

### Standard Sensors (Enabled by Default)

#### PowerMeter Devices
- **Total Energy Consumption** (`sensor.loggamera_{device_id}_ConsumedTotalInkWh`) - Total energy consumed in kWh
- **Current Power** (`sensor.loggamera_{device_id}_PowerInkW`) - Current power usage in kW
- **Alarm Status** (`sensor.loggamera_{device_id}_alarmActive`) - Device alarm state
- **Alarm Context** (`sensor.loggamera_{device_id}_alarmInClearText`) - Alarm description

#### WaterMeter Devices
- **Total Water Consumption** (`sensor.loggamera_{device_id}_ConsumedTotalInm3`) - Total water consumed in m³
- **Water Since Midnight** (`sensor.loggamera_{device_id}_ConsumedSinceMidnightInLiters`) - Daily water usage

#### RoomSensor Devices
- **Temperature** (`sensor.loggamera_{device_id}_TemperatureInC`) - Temperature readings in °C
- **Humidity** (`sensor.loggamera_{device_id}_HumidityInRH`) - Humidity readings in %

#### HeatPump Devices
- **Heat Carrier Temperatures** - Inlet/outlet temperature sensors
- **Brine Temperatures** - Brine system temperature monitoring
- **Pump Activity** - Heat pump operational status

### Detailed RawData Sensors (Disabled by Default)

Each device also provides detailed RawData sensors for advanced monitoring:
- **PowerMeter**: ~19 additional sensors with detailed electrical metrics (`sensor.rawdata_{device_id}_powermeter_{sensor_id}`)
- **WaterMeter**: Additional flow and pressure sensors (`sensor.rawdata_{device_id}_watermeter_{sensor_id}`)
- **HeatPump**: Comprehensive temperature and performance sensors (`sensor.rawdata_{device_id}_heatpump_{sensor_id}`)

**Note**: RawData sensors are disabled by default to prevent entity spam. Users can manually enable specific sensors they need via the Home Assistant UI.

### Binary Sensors
- **Alarm Status** - Indicates if device alarms are active
- **Device connectivity** - Shows if devices are online/offline

### Switches
- **Scenario Controls** - Execute predefined scenarios on your Loggamera devices

All sensors are automatically discovered and configured based on your device capabilities. Energy sensors are compatible with the Home Assistant Energy dashboard for comprehensive energy monitoring.

## Recent Major Updates

### Version 2.x - Sensor Architecture Overhaul

#### 🎯 **Clean Device Interface**
- **Before**: PowerMeter devices created ~23 mixed sensors (confusing user experience)
- **After**: PowerMeter devices create 4 clean, standard sensors with optional detailed sensors

#### 🔄 **Improved Data Collection**
- **Better Organization**: Standard device sensors and detailed diagnostic sensors are now collected separately
- **More Reliable**: Each device type uses its most appropriate data source for consistent readings

#### 🏷️ **Smart Entity Naming**
- **Standard sensors**: `sensor.loggamera_{device_id}_{sensor_name}` (enabled by default)
- **Detailed sensors**: `sensor.rawdata_{device_id}_{device_type}_{sensor_id}` (disabled by default)

#### 🤖 **Automatic Sensor Detection**
- **Smart Recognition**: Automatically detects and configures new sensor types
- **Future-Proof**: Works with new Loggamera devices without software updates
- **Comprehensive Coverage**: Supports all common sensor types (temperature, energy, power, water, etc.)

#### 📊 **User Experience Improvements**
- **Entity Spam Prevention**: RawData sensors disabled by default
- **User Control**: Manual enablement of detailed sensors per user preference
- **Better Organization**: Clear separation between standard and detailed monitoring
- **Backward Compatible**: Existing sensor names preserved for known sensors

#### 🔧 **Reliability Improvements**
- **Robust Connection**: Better API handling with automatic fallbacks
- **Enhanced Debugging**: Detailed logging for troubleshooting
- **Error Handling**: Improved validation and graceful error recovery


## Troubleshooting

### Debugging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.loggamera: debug
```

### API Structure

The Loggamera API is structured as follows:

- **PowerMeter**: Returns energy data with values for `PowerInkW`, `ConsumedTotalInkWh`, and additional power metrics
- **RawData**: Provides detailed sensor values with numerical identifiers (544352, 544399, etc.)
- **RoomSensor**: Returns temperature and humidity data in `Values` array
- **WaterMeter**: Returns water consumption data
- **Scenarios**: Controls execution of defined scenarios

### Diagnostic Tools

The integration includes comprehensive diagnostic tools in the `tools/` directory:

#### Basic API Testing
```bash
# Test API connectivity and device discovery
python tools/test_powermeter.py YOUR_API_KEY --verbose

# Explore specific API endpoints
python tools/loggamera_api_explorer.py YOUR_API_KEY PowerMeter --device-id YOUR_DEVICE_ID
```

#### Advanced Diagnostics
```bash
# Monitor real-time power meter updates
python tools/monitor_powermeter_updates.py --api-key YOUR_API_KEY --device-id YOUR_DEVICE_ID

# Analyze update frequency patterns
python tools/analyze_update_frequency.py YOUR_API_KEY YOUR_DEVICE_ID

# Test SSL/TLS connectivity
bash tools/diagnose_tls.sh
```

#### Integration Helpers
```bash
# Generate Home Assistant sensor configurations
python tools/ha_sensor_config_helper.py YOUR_API_KEY YOUR_DEVICE_ID

# Comprehensive diagnostic report
python tools/loggamera_diagnostic.py YOUR_API_KEY
```

### Common Issues

1. **SSL/TLS Errors**: Use the TLS diagnostic tool to check certificate issues
2. **API Key Issues**: Verify your API key with the Loggamera portal
3. **Device Not Found**: Use the diagnostic tools to verify device IDs and organization access
4. **Update Frequency**: PowerMeter data typically updates every 30 minutes

## Issues and Support

If you encounter issues:

1. Enable debug logging and check Home Assistant logs
2. Use the diagnostic tools to test your API connection
3. Check the [troubleshooting documentation](docs/TROUBLESHOOTING.md)
4. Open an issue on [GitHub](https://github.com/delize/home-assistant-loggamera-integration/issues)

## License

This integration is licensed under AGPL License.
