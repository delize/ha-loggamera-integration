# Loggamera Integration for Home Assistant

This integration allows you to monitor and control your Loggamera devices in Home Assistant. It provides sensors for various device types, including PowerMeter, RoomSensor, and more.

## Features

- Supports PowerMeter devices for energy monitoring
- Shows power and energy consumption
- Supports alarm states as binary sensors
- Can execute scenarios via switches
- Automatic fallback mechanisms for different types of API access

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Add this repository URL as a custom repository in HACS.
3. Install the integration through HACS.
4. Restart Home Assistant.

### Manual Installation

1. Download the latest release.
2. Copy the `loggamera` directory from the `custom_components` directory to your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Configuration** > **Integrations** and click the "+" button.
2. Search for "Loggamera" and select it.
3. Enter your API key and follow the setup instructions.

## Update Frequency and Polling

### PowerMeter Devices

The Loggamera PowerMeter endpoint typically updates data approximately every 30 minutes. Setting a more frequent polling interval will not result in more frequent data updates.

The integration defaults to polling the API every 20 minutes (1200 seconds) which is optimized for:

- Ensuring timely updates (within ~10 minutes of new data being available)
- Reducing unnecessary API calls
- Avoiding excessive logging of "no changes" messages

You can adjust the polling interval in the integration's options, but be aware that:

- Setting it too low (< 10 minutes) will result in many unnecessary API calls
- Setting it too high (> 30 minutes) may cause you to miss some updates

### Update Patterns

If you notice that your data isn't updating as expected, you can use the diagnostic tools included in this repository to monitor the actual update patterns of your specific PowerMeter device.

## Diagnostic Tools

Several diagnostic tools are included to help troubleshoot and optimize your Loggamera integration:

### PowerMeter Update Monitor

This tool monitors your PowerMeter device to track when updates occur and recommends an optimal polling interval:

```bash
python tools/monitor_powermeter_updates.py --api-key 05DEE511FE25F65555556JKHH87562 --device-id 9729 --interval 300 --duration 24
```

This will monitor updates for 24 hours with a 5-minute polling interval and provide statistics and recommendations.

### Basic PowerMeter Output

For a quick check of current PowerMeter data:

```bash
python tools/basic_powermeter_output.py --api-key 05DEE511FE25F65555556JKHH87562 --device-id 9729
```

To continuously poll for updates:

```bash
python tools/basic_powermeter_output.py --api-key 05DEE511FE25F65555556JKHH87562 --device-id 9729 --poll 300
```

### Home Assistant Sensor Configuration Helper

Generates YAML configuration snippets for your sensors:

```bash
python tools/ha_sensor_config_helper.py 05DEE511FE25F65555556JKHH87562 9729
```

## Troubleshooting

### Stale Data

If you see warnings about stale data in your logs, this typically means that the PowerMeter device hasn't sent new data to the Loggamera backend for an extended period (>2 hours). This could indicate:

1. Network connectivity issues with your PowerMeter device
2. Issues with the Loggamera cloud service
3. Configuration problems with your PowerMeter device

The integration will mark sensors as unavailable if data hasn't been updated for over 2 hours.

### API Connection Issues

If you're experiencing API connection issues:

1. Verify your API key is correct
2. Check your internet connection
3. Confirm the Loggamera service is operational
4. Ensure your Home Assistant instance can reach the Loggamera API (platform.loggamera.se)

## Device Support

The integration currently supports the following device types:

- PowerMeter
- RoomSensor
- WaterMeter
- CoolingUnit
- HeatPump

For other device types, the integration attempts to use the RawData or GenericDevice endpoints as fallbacks.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This integration is licensed under the MIT License.

## Disclaimer

This integration is not affiliated with, endorsed by, or connected to Loggamera.
