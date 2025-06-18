#!/usr/bin/env python3
"""Check actual sensor mapping coverage using real sensor.py mappings."""

import os
import sys

import requests

# Add the integration path so we can import the real SENSOR_MAP
sys.path.insert(0, "/mnt/c/Users/andrew/Documents/github/ha-loggamera-integration")

try:
    from custom_components.loggamera.sensor import SENSOR_MAP

    print(f"✅ Loaded SENSOR_MAP with {len(SENSOR_MAP)} mappings")
except ImportError:
    print("❌ Could not import SENSOR_MAP from sensor.py")
    sys.exit(1)

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"


def check_coverage():
    """Check actual coverage using real sensor mappings."""
    print("🔧 Checking Actual Sensor Coverage")
    print("=" * 50)

    total_sensors_found = 0
    mapped_sensors = 0
    missing_sensors = []

    # Get organizations
    org_response = requests.post(
        f"{BASE_URL}/Organizations",
        json={"ApiKey": API_KEY},
        headers={"Content-Type": "application/json"},
    )

    if org_response.status_code != 200:
        print(f"❌ Failed to get organizations")
        return False

    organizations = org_response.json().get("Data", {}).get("Organizations", [])

    # Test each organization's devices
    for org in organizations:
        org_id = org["Id"]
        org_name = org["Name"]

        devices_response = requests.post(
            f"{BASE_URL}/Devices",
            json={"ApiKey": API_KEY, "OrganizationId": org_id},
            headers={"Content-Type": "application/json"},
        )

        if devices_response.status_code != 200:
            continue

        devices = devices_response.json().get("Data", {}).get("Devices", [])

        for device in devices:
            device_id = device["Id"]
            device_name = device["Title"]
            device_type = device["Class"]

            print(f"\n📱 {device_name} ({device_type}):")

            # Test different endpoints
            endpoints = [
                ("PowerMeter", f"{BASE_URL}/PowerMeter"),
                ("RoomSensor", f"{BASE_URL}/RoomSensor"),
                ("WaterMeter", f"{BASE_URL}/WaterMeter"),
                ("RawData", f"{BASE_URL}/RawData"),
                ("GenericDevice", f"{BASE_URL}/GenericDevice"),
            ]

            for endpoint_name, endpoint_url in endpoints:
                response = requests.post(
                    endpoint_url,
                    json={"ApiKey": API_KEY, "DeviceId": device_id},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("Data") and data["Data"].get("Values"):
                        values = data["Data"]["Values"]

                        if values:
                            print(f"  🔌 {endpoint_name}: {len(values)} sensors")

                            for value in values:
                                sensor_name = value.get("Name", "unknown")
                                sensor_value = value.get("Value", "N/A")
                                sensor_unit = value.get("UnitPresentation", "")

                                total_sensors_found += 1

                                # Check if mapped
                                if sensor_name in SENSOR_MAP:
                                    mapped_sensors += 1
                                    mapping = SENSOR_MAP[sensor_name]
                                    print(
                                        f"    ✅ {sensor_name}: {sensor_value} {sensor_unit} → {mapping.get('name', 'Unknown')}"
                                    )
                                else:
                                    missing_sensors.append(
                                        {
                                            "name": sensor_name,
                                            "device": device_name,
                                            "endpoint": endpoint_name,
                                            "value": sensor_value,
                                            "unit": sensor_unit,
                                            "description": value.get(
                                                "ClearTextName", ""
                                            ),
                                        }
                                    )
                                    print(
                                        f"    ❌ {sensor_name}: {sensor_value} {sensor_unit} - MISSING"
                                    )

    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 ACTUAL COVERAGE REPORT")
    print(f"=" * 60)
    print(f"📋 Total sensors found: {total_sensors_found}")
    print(f"✅ Mapped sensors: {mapped_sensors}")
    print(f"❌ Missing sensors: {len(missing_sensors)}")

    if total_sensors_found > 0:
        coverage = (mapped_sensors / total_sensors_found) * 100
        print(f"📈 Coverage: {coverage:.1f}%")

    if missing_sensors:
        print(f"\n❌ Missing Sensor Mappings:")
        for sensor in missing_sensors[:10]:  # Show first 10
            print(
                f"  - {sensor['name']}: {sensor['description']} ({sensor['endpoint']})"
            )

        if len(missing_sensors) > 10:
            print(f"  ... and {len(missing_sensors) - 10} more")

    return len(missing_sensors) == 0


if __name__ == "__main__":
    success = check_coverage()
    sys.exit(0 if success else 1)
