# Loggamera Integration for Home Assistant

This is a custom component for Home Assistant that integrates with Loggamera, a tool that monitors electricity, water, and other utilities in your home.

## Features

- Monitor power consumption
- Monitor water usage
- Monitor room temperature and humidity
- Execute scenarios
- Set device properties
- Get alerts for device alarms

## Installation

### Manual Installation

1. Download the `loggamera` folder from this repository.
2. Copy the folder to your Home Assistant configuration directory under `custom_components/`.
3. Restart Home Assistant.

### Installation via HACS (Home Assistant Community Store)

1. Add this repository to HACS as a custom repository.
2. Search for "Loggamera" in HACS and install it.
3. Restart Home Assistant.

## Configuration

1. Go to Home Assistant Settings > Devices & Services.
2. Click the "+ Add Integration" button.
3. Search for "Loggamera" and select it.
4. Enter your API key.

## Services

The integration provides the following services:

### `loggamera.execute_scenario`

Execute a scenario in Loggamera.

**Parameters:**

- `scenario_id` (required): The ID of the scenario to execute.
- `duration_minutes` (optional): Duration in minutes for the scenario.
- `entry_id` (optional): Entry ID of the Loggamera integration (needed only if you have multiple instances).

## Device Types Supported

The integration supports multiple device types:

- **PowerMeter**: Monitors electricity usage and power consumption
- **WaterMeter**: Tracks water consumption
- **RoomSensor**: Provides temperature and humidity readings
- **GenericDevice**: Supports various sensors and capabilities
- **CoolingUnit**: Monitors cooling system status
- **HeatPump**: Provides heat pump status and controls

## Data Refresh

By default, data is refreshed every 60 seconds. You can change this interval in the integration options.

## Troubleshooting

### Common Issues

- **Cannot connect to Loggamera API**: Check your API key and internet connection.
- **No devices found**: Make sure your devices are properly set up in the Loggamera platform.
- **Missing entity values**: Some devices might not report all values. Check the device in the Loggamera platform.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
