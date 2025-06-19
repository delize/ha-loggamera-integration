#!/usr/bin/env python3
"""Comprehensive sensor discovery - test ALL endpoints against ALL devices."""

import json
import os
import sys
from collections import defaultdict

import requests

# Get API key from environment variable or use placeholder
API_KEY = os.getenv("LOGGAMERA_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://platform.loggamera.se/api/v2"

# ALL possible API endpoints to test
ALL_ENDPOINTS = [
    "PowerMeter",
    "RoomSensor",
    "WaterMeter",
    "HeatMeter",
    "HeatPump",
    "CoolingUnit",
    "ChargingStation",
    "SolarPanel",
    "WindTurbine",
    "BatteryStorage",
    "InverterSystem",
    "WeatherStation",
    "AirQualitySensor",
    "MotionSensor",
    "DoorSensor",
    "WindowSensor",
    "SmokeSensor",
    "FloodSensor",
    "ThermostatUnit",
    "VentilationUnit",
    "LightingControl",
    "SecuritySystem",
    "AccessControl",
    "ParkingSensor",
    "ElevatorSystem",
    "FireSafety",
    "GenericDevice",
    "RawData",
    "Capabilities",
    "DeviceStatus",
    "Diagnostics",
    "Maintenance",
    "Configuration",
    "Alerts",
    "Notifications",
    "Statistics",
    "Analytics",
    "Reports",
    "Logs",
]


def make_api_request(endpoint_url, data=None):
    """Make an API request with proper error handling."""
    try:
        if data is None:
            data = {}

        if "ApiKey" not in data:
            data["ApiKey"] = API_KEY

        response = requests.post(
            endpoint_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            return False, None, f"HTTP {response.status_code}"

        if not response.text.strip():
            return False, None, "Empty response"

        try:
            response_data = response.json()
        except ValueError as e:
            return False, None, f"Invalid JSON: {e}"

        if response_data is None:
            return False, None, "Null response"

        # Check for API errors
        if "Error" in response_data and response_data["Error"] is not None:
            if (
                isinstance(response_data["Error"], dict)
                and "Message" in response_data["Error"]
            ):
                error_msg = response_data["Error"]["Message"]
                if error_msg == "invalid endpoint":
                    return False, None, "Invalid endpoint"
                return False, None, f"API error: {error_msg}"
            else:
                return False, None, f"Unknown error: {response_data['Error']}"

        return True, response_data, None

    except requests.exceptions.RequestException as e:
        return False, None, f"Request failed: {e}"
    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def discover_all_sensors():
    """Discover ALL sensors by testing EVERY endpoint against EVERY device."""
    print("🔍 COMPREHENSIVE SENSOR DISCOVERY")
    print("Testing ALL endpoints against ALL devices")
    print("=" * 80)

    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Error: API key not configured")
        print("   Set LOGGAMERA_API_KEY environment variable")
        return

    all_sensors = {}
    endpoint_results = defaultdict(lambda: defaultdict(list))
    device_summary = []
    total_unique_sensors = set()

    # Get organizations
    print("🏭 Getting organizations...")
    success, org_data, error = make_api_request(f"{BASE_URL}/Organizations")

    if not success:
        print(f"❌ Failed to get organizations: {error}")
        return

    if not org_data or not org_data.get("Data"):
        print("❌ No organization data found")
        return

    organizations = org_data.get("Data", {}).get("Organizations", [])
    print(f"✅ Found {len(organizations)} organizations")

    for org in organizations:
        org_id = org.get("Id")
        org_name = org.get("Name", f"Org {org_id}")

        if not org_id:
            continue

        print(f"\n🏢 Processing {org_name} (ID: {org_id})...")

        # Get devices
        success, devices_data, error = make_api_request(
            f"{BASE_URL}/Devices", {"OrganizationId": org_id}
        )

        if not success:
            print(f"  ❌ Failed to get devices: {error}")
            continue

        if not devices_data or not devices_data.get("Data"):
            print("  ⚠️  No device data found")
            continue

        devices = devices_data.get("Data", {}).get("Devices", [])
        print(f"  📱 Found {len(devices)} devices")

        for device in devices:
            device_id = device.get("Id")
            device_name = device.get("Title", f"Device {device_id}")
            device_type = device.get("Class", "Unknown")

            if not device_id:
                continue

            print(
                f"\n    📱 {device_name} ({device_type}) - Testing {len(ALL_ENDPOINTS)} endpoints:"
            )

            device_sensors = set()
            working_endpoints = []

            # Test EVERY endpoint against this device
            for endpoint_name in ALL_ENDPOINTS:
                endpoint_url = f"{BASE_URL}/{endpoint_name}"

                success, data, error = make_api_request(
                    endpoint_url, {"DeviceId": device_id}
                )

                if success and data and data.get("Data"):
                    # Check for Values array (sensor data)
                    if data["Data"].get("Values"):
                        values = data["Data"]["Values"]
                        sensor_count = len(values)
                        working_endpoints.append(f"{endpoint_name}({sensor_count})")

                        print(f"      ✅ {endpoint_name}: {sensor_count} sensors")

                        for value in values:
                            sensor_name = value.get("Name", "unknown")
                            sensor_desc = value.get("ClearTextName", "")
                            sensor_unit = value.get("UnitPresentation", "")
                            sensor_value = value.get("Value", "N/A")

                            # Create unique sensor key
                            sensor_key = f"{sensor_name}"
                            total_unique_sensors.add(sensor_key)
                            device_sensors.add(sensor_key)

                            # Store detailed sensor info
                            if sensor_key not in all_sensors:
                                all_sensors[sensor_key] = {
                                    "name": sensor_name,
                                    "description": sensor_desc,
                                    "unit": sensor_unit,
                                    "found_on_devices": [],
                                    "found_on_endpoints": set(),
                                }

                            all_sensors[sensor_key]["found_on_devices"].append(
                                {
                                    "device_name": device_name,
                                    "device_type": device_type,
                                    "organization": org_name,
                                    "value": sensor_value,
                                }
                            )
                            all_sensors[sensor_key]["found_on_endpoints"].add(
                                endpoint_name
                            )

                            endpoint_results[endpoint_name][sensor_key].append(
                                {
                                    "device": device_name,
                                    "value": sensor_value,
                                    "unit": sensor_unit,
                                }
                            )

                    # Check for other data structures
                    elif data["Data"]:
                        # Non-Values data structure - might still contain sensor info
                        working_endpoints.append(f"{endpoint_name}(other)")
                        print(f"      ⚪ {endpoint_name}: other data structure")

                elif error and "invalid endpoint" not in error.lower():
                    print(f"      ⚠️  {endpoint_name}: {error}")

            device_summary.append(
                {
                    "name": device_name,
                    "type": device_type,
                    "organization": org_name,
                    "sensors_found": len(device_sensors),
                    "working_endpoints": working_endpoints,
                    "unique_sensors": device_sensors,
                }
            )

            print(f"      📊 Total sensors found on this device: {len(device_sensors)}")

    # Generate comprehensive report
    print(f"\n" + "=" * 100)
    print(f"🔍 COMPREHENSIVE SENSOR DISCOVERY REPORT")
    print(f"=" * 100)

    print(f"\n📈 Overall Statistics:")
    print(f"  🔍 Total unique sensors discovered: {len(total_unique_sensors)}")
    print(f"  📱 Total devices tested: {len(device_summary)}")
    print(f"  🔌 Total endpoints tested: {len(ALL_ENDPOINTS)}")

    print(f"\n📱 Device Summary:")
    for device in device_summary:
        print(f"  {device['name']} ({device['type']}):")
        print(f"    📊 Sensors: {device['sensors_found']}")
        print(f"    🔌 Working endpoints: {', '.join(device['working_endpoints'])}")

    print(f"\n🔌 Endpoint Effectiveness:")
    for endpoint_name in ALL_ENDPOINTS:
        if endpoint_name in endpoint_results:
            unique_sensors = len(endpoint_results[endpoint_name])
            print(f"  {endpoint_name}: {unique_sensors} unique sensors")
        else:
            print(f"  {endpoint_name}: 0 sensors (no working responses)")

    print(f"\n🔍 All Discovered Sensors:")
    for i, (sensor_key, sensor_info) in enumerate(sorted(all_sensors.items()), 1):
        endpoints = ", ".join(sorted(sensor_info["found_on_endpoints"]))
        device_count = len(sensor_info["found_on_devices"])
        print(f"{i:3d}. {sensor_key}")
        print(f"     📝 Description: {sensor_info['description']}")
        print(f"     📏 Unit: {sensor_info['unit']}")
        print(f"     🔌 Endpoints: {endpoints}")
        print(f"     📱 Found on {device_count} device(s)")

    # Export to JSON
    export_data = {
        "metadata": {
            "total_unique_sensors": len(total_unique_sensors),
            "total_devices": len(device_summary),
            "total_endpoints_tested": len(ALL_ENDPOINTS),
        },
        "sensors": all_sensors,
        "devices": device_summary,
        "endpoint_results": dict(endpoint_results),
    }

    # Convert sets to lists for JSON serialization
    for sensor_info in export_data["sensors"].values():
        sensor_info["found_on_endpoints"] = list(sensor_info["found_on_endpoints"])

    filename = "comprehensive_sensor_discovery.json"
    with open(filename, "w") as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"\n💾 Detailed results exported to: {filename}")
    print(f"\n🎯 TOTAL SENSORS DISCOVERED: {len(total_unique_sensors)}")

    return len(total_unique_sensors)


if __name__ == "__main__":
    try:
        sensor_count = discover_all_sensors()
        if sensor_count:
            print(f"\n🎉 SUCCESS: Discovered {sensor_count} unique sensors!")
        else:
            print(f"\n❌ FAILED: No sensors discovered")
    except KeyboardInterrupt:
        print(f"\n⚠️  Discovery interrupted by user")
    except Exception as e:
        print(f"\n❌ Discovery failed: {e}")
        sys.exit(1)
