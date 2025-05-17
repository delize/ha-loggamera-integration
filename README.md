# Loggamera Integration for Home Assistant

This custom integration allows you to connect your Loggamera devices to Home Assistant. Monitor your electricity, water, and other utilities directly from your Home Assistant dashboard.

## Features

- Monitor power consumption and usage
- Track water consumption
- View room temperature and humidity
- Support for various Loggamera device types
- Execute scenarios defined in Loggamera

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations → Click the three dots in the top right corner → Custom repositories
3. Add the repository URL: `https://github.com/yourusername/ha-loggamera-integration`
4. Click "Add"
5. Find and install "Loggamera" in HACS
6. Restart Home Assistant

### Manual Installation

1. Download this repository as a ZIP file
2. Extract the contents
3. Copy the `custom_components/loggamera` folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Loggamera"
3. Enter your Loggamera API key
4. Click "Submit"

## Usage

After setup, the integration will automatically add sensors for your Loggamera devices based on their capabilities:

- Power meters will show current power usage and energy consumption
- Water meters will show water consumption
- Room sensors will show temperature and humidity
- And more, depending on your connected devices

## Troubleshooting

If you encounter issues:

1. Check your API key is correct
2. Ensure your Loggamera devices are online and reporting data
3. Check the Home Assistant logs for any error messages
4. Restart Home Assistant after making configuration changes

## Support

If you need help or want to report a bug, please [create an issue](https://github.com/yourusername/ha-loggamera-integration/issues) on GitHub.
