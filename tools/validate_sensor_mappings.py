#!/usr/bin/env python3
"""Comprehensive sensor mapping validation for all devices."""

import json
import sys
from collections import defaultdict

import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"

# Import sensor mappings from the integration
SENSOR_MAP = {
    # PowerMeter standard values
    "ConsumedTotalInkWh": {
        "device_class": "energy",
        "unit": "kWh",
        "state_class": "total_increasing",
        "name": "Total Energy Consumption",
    },
    "PowerInkW": {
        "device_class": "power",
        "unit": "kW",
        "state_class": "measurement",
        "name": "Current Energy Consumption",
    },
    "alarmActive": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Alarm Status",
        "icon": "mdi:alert-circle",
    },
    "alarmInClearText": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Alarm Context",
        "icon": "mdi:alert-box",
    },
    # Organization sensors
    "device_count": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Total Device Count",
        "icon": "mdi:counter",
    },
    "organization_count": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Total Organization Count",
        "icon": "mdi:domain",
    },
    "parent_organization": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Parent Organization",
        "icon": "mdi:account-supervisor",
    },
    "child_organizations": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Child Organizations Count",
        "icon": "mdi:account-group",
    },
    "user_count": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "User Count",
        "icon": "mdi:account",
    },
    "member_count": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Member Count",
        "icon": "mdi:account-multiple",
    },
    # HeatMeter RawData sensors
    "544310": {
        "device_class": "energy",
        "unit": "kWh",
        "state_class": "total_increasing",
        "name": "Total Energy",
    },
    "544311": {
        "device_class": None,
        "unit": "m³",
        "state_class": "total_increasing",
        "name": "Total Volume",
    },
    "544320": {
        "device_class": None,
        "unit": "m³/h",
        "state_class": "measurement",
        "name": "Flow Rate",
    },
    "544321": {
        "device_class": "temperature",
        "unit": "°C",
        "state_class": "measurement",
        "name": "Flow Temperature",
    },
    "544322": {
        "device_class": "temperature",
        "unit": "°C",
        "state_class": "measurement",
        "name": "Return Temperature",
    },
    "544323": {
        "device_class": "temperature",
        "unit": "°C",
        "state_class": "measurement",
        "name": "Temperature Difference",
    },
    "544324": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Error Code",
        "icon": "mdi:alert-circle-outline",
    },
    # RawData PowerMeter sensors
    "544352": {
        "device_class": "energy",
        "unit": "kWh",
        "state_class": "total_increasing",
        "name": "Total Energy Consumed",
    },
    "544353": {
        "device_class": "energy",
        "unit": "kWh",
        "state_class": "total_increasing",
        "name": "Total Energy Interval",
    },
    "544399": {
        "device_class": "power",
        "unit": "W",
        "state_class": "measurement",
        "name": "Power",
    },
    # RoomSensor sensors
    "Temperature": {
        "device_class": "temperature",
        "unit": "°C",
        "state_class": "measurement",
        "name": "Temperature",
    },
    "RelativeHumidity": {
        "device_class": "humidity",
        "unit": "%",
        "state_class": "measurement",
        "name": "Relative Humidity",
    },
    # WaterMeter sensors
    "ConsumedTotalInM3": {
        "device_class": "water",
        "unit": "m³",
        "state_class": "total_increasing",
        "name": "Total Water Consumption",
    },
    "ConsumedSinceMidnightInLiters": {
        "device_class": "water",
        "unit": "L",
        "state_class": "total_increasing",
        "name": "Water Used Since Midnight",
    },
}


def validate_sensor_mappings():
    """Validate sensor mappings for all devices across all organizations."""
    print("🔧 Comprehensive Sensor Mapping Validation")
    print("=" * 60)

    missing_mappings = []
    all_sensors = defaultdict(list)
    device_summary = []
    endpoint_coverage = defaultdict(set)

    # Get organizations
    org_response = requests.post(
        f"{BASE_URL}/Organizations",
        json={"ApiKey": API_KEY},
        headers={"Content-Type": "application/json"},
    )

    if org_response.status_code != 200:
        print(f"❌ Failed to get organizations: {org_response.status_code}")
        return False

    organizations = org_response.json().get("Data", {}).get("Organizations", [])
    print(f"📡 Found {len(organizations)} organizations to validate")

    # Test each organization
    for org in organizations:
        org_id = org["Id"]
        org_name = org["Name"]

        print(f"\n🏢 Validating Organization: {org_name} (ID: {org_id})")

        # Get devices for this organization
        devices_response = requests.post(
            f"{BASE_URL}/Devices",
            json={"ApiKey": API_KEY, "OrganizationId": org_id},
            headers={"Content-Type": "application/json"},
        )

        if devices_response.status_code != 200:
            print(f"  ❌ Failed to get devices: {devices_response.status_code}")
            continue

        devices = devices_response.json().get("Data", {}).get("Devices", [])
        print(f"  📱 Found {len(devices)} devices")

        # Test each device
        for device in devices:
            device_id = device["Id"]
            device_type = device["Class"]
            device_name = device["Title"]

            print(f"\n    🔌 {device_name} (ID: {device_id}, Type: {device_type})")

            device_info = {
                "id": device_id,
                "name": device_name,
                "type": device_type,
                "org": org_name,
                "endpoints_tested": [],
                "sensors_found": 0,
                "mapped_sensors": 0,
                "unmapped_sensors": [],
            }

            # Test different endpoints for this device
            endpoints_to_test = [
                ("PowerMeter", f"{BASE_URL}/PowerMeter"),
                ("RoomSensor", f"{BASE_URL}/RoomSensor"),
                ("WaterMeter", f"{BASE_URL}/WaterMeter"),
                ("HeatPump", f"{BASE_URL}/HeatPump"),
                ("CoolingUnit", f"{BASE_URL}/CoolingUnit"),
                ("RawData", f"{BASE_URL}/RawData"),
                ("GenericDevice", f"{BASE_URL}/GenericDevice"),
                ("Capabilities", f"{BASE_URL}/Capabilities"),
            ]

            for endpoint_name, endpoint_url in endpoints_to_test:
                response = requests.post(
                    endpoint_url,
                    json={"ApiKey": API_KEY, "DeviceId": device_id},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()

                    # Check for sensor data
                    sensors_found = False
                    if data.get("Data") and data["Data"].get("Values"):
                        sensors_found = True
                        values = data["Data"]["Values"]
                        device_info["endpoints_tested"].append(
                            f"{endpoint_name}✅({len(values)})"
                        )
                        endpoint_coverage[device_type].add(endpoint_name)

                        print(f"      ✅ {endpoint_name}: {len(values)} sensors")

                        # Check each sensor for mapping
                        for value in values:
                            sensor_name = value.get("Name", "unknown")
                            sensor_value = value.get("Value", "N/A")
                            sensor_unit = value.get("UnitPresentation", "")
                            sensor_desc = value.get("ClearTextName", "")

                            device_info["sensors_found"] += 1

                            # Track all unique sensors
                            sensor_key = f"{sensor_name} ({endpoint_name})"
                            all_sensors[sensor_key].append(
                                {
                                    "device": device_name,
                                    "device_type": device_type,
                                    "value": sensor_value,
                                    "unit": sensor_unit,
                                    "description": sensor_desc,
                                }
                            )

                            # Check if we have a mapping
                            if sensor_name in SENSOR_MAP:
                                device_info["mapped_sensors"] += 1
                                mapping = SENSOR_MAP[sensor_name]
                                print(
                                    f"        ✅ {sensor_name}: {sensor_value} {sensor_unit} → {mapping['name']}"
                                )
                            else:
                                device_info["unmapped_sensors"].append(
                                    {
                                        "name": sensor_name,
                                        "value": sensor_value,
                                        "unit": sensor_unit,
                                        "description": sensor_desc,
                                        "endpoint": endpoint_name,
                                    }
                                )
                                print(
                                    f"        ❌ {sensor_name}: {sensor_value} {sensor_unit} ({sensor_desc}) - NO MAPPING"
                                )

                                missing_mappings.append(
                                    {
                                        "sensor_name": sensor_name,
                                        "device_name": device_name,
                                        "device_type": device_type,
                                        "endpoint": endpoint_name,
                                        "value": sensor_value,
                                        "unit": sensor_unit,
                                        "description": sensor_desc,
                                    }
                                )

                    elif data.get("Data"):
                        # Endpoint works but no Values array
                        device_info["endpoints_tested"].append(
                            f"{endpoint_name}⚠️(no-values)"
                        )
                        print(f"      ⚠️  {endpoint_name}: No sensor values")

                    else:
                        # Endpoint works but no Data
                        device_info["endpoints_tested"].append(
                            f"{endpoint_name}⚠️(no-data)"
                        )

                else:
                    # Endpoint failed
                    device_info["endpoints_tested"].append(f"{endpoint_name}❌")

            device_summary.append(device_info)

    # Generate comprehensive report
    print(f"\n" + "=" * 80)
    print(f"📊 SENSOR MAPPING VALIDATION REPORT")
    print(f"=" * 80)

    print(f"\n📈 Summary by Device:")
    for device in device_summary:
        coverage = (
            f"{device['mapped_sensors']}/{device['sensors_found']}"
            if device["sensors_found"] > 0
            else "0/0"
        )
        coverage_pct = (
            (device["mapped_sensors"] / device["sensors_found"] * 100)
            if device["sensors_found"] > 0
            else 0
        )

        print(f"  📱 {device['name']} ({device['type']}):")
        print(f"    📊 Mapping Coverage: {coverage} ({coverage_pct:.1f}%)")
        print(f"    🔌 Endpoints: {', '.join(device['endpoints_tested'])}")

        if device["unmapped_sensors"]:
            print(f"    ❌ Missing mappings:")
            for sensor in device["unmapped_sensors"]:
                print(
                    f"      - {sensor['name']}: {sensor['description']} ({sensor['endpoint']})"
                )

    print(f"\n🔧 Endpoint Coverage by Device Type:")
    for device_type, endpoints in endpoint_coverage.items():
        print(f"  {device_type}: {', '.join(sorted(endpoints))}")

    print(f"\n❌ Missing Sensor Mappings ({len(missing_mappings)} total):")
    if missing_mappings:
        # Group by sensor name for easier analysis
        grouped_missing = defaultdict(list)
        for missing in missing_mappings:
            grouped_missing[missing["sensor_name"]].append(missing)

        for sensor_name, instances in grouped_missing.items():
            first_instance = instances[0]
            device_count = len(instances)
            print(f"\n  🔍 {sensor_name}:")
            print(f"    📝 Description: {first_instance['description']}")
            print(f"    📏 Unit: {first_instance['unit']}")
            print(f"    🔌 Endpoint: {first_instance['endpoint']}")
            print(
                f"    📱 Found on {device_count} device(s): {', '.join([i['device_name'] for i in instances])}"
            )

            # Suggest mapping
            unit = first_instance["unit"]
            desc = first_instance["description"].lower()

            suggested_device_class = None
            if "temp" in desc or "grader" in desc or "°c" in unit.lower():
                suggested_device_class = "temperature"
            elif (
                "power" in desc
                or "effekt" in desc
                or "kw" in unit.lower()
                or "w" == unit.lower()
            ):
                suggested_device_class = "power"
            elif "energy" in desc or "kwh" in unit.lower():
                suggested_device_class = "energy"
            elif "humidity" in desc or "fukt" in desc or "%" in unit:
                suggested_device_class = "humidity"
            elif (
                "water" in desc
                or "vatten" in desc
                or "m³" in unit
                or "l" == unit.lower()
            ):
                suggested_device_class = "water"
            elif "alarm" in desc or "larm" in desc:
                suggested_device_class = None

            print(f"    💡 Suggested mapping:")
            print(f'    "{sensor_name}": {{')
            device_class_str = (
                f'"{suggested_device_class}"' if suggested_device_class else "None"
            )
            unit_str = f'"{unit}"' if unit else "None"
            print(f'        "device_class": {device_class_str},')
            print(f'        "unit": {unit_str},')
            print(f'        "state_class": "measurement",')
            print(f'        "name": "{first_instance["description"]}",')
            print(f"    }},")
    else:
        print("  🎉 No missing mappings found!")

    print(f"\n📋 Validation Summary:")
    total_devices = len(device_summary)
    total_sensors = sum(d["sensors_found"] for d in device_summary)
    total_mapped = sum(d["mapped_sensors"] for d in device_summary)

    print(f"  📱 Total devices tested: {total_devices}")
    print(f"  🔌 Total sensors found: {total_sensors}")
    print(f"  ✅ Sensors with mappings: {total_mapped}")
    print(f"  ❌ Sensors missing mappings: {len(missing_mappings)}")
    print(
        f"  📊 Overall coverage: {(total_mapped/total_sensors*100) if total_sensors > 0 else 0:.1f}%"
    )

    return len(missing_mappings) == 0


if __name__ == "__main__":
    success = validate_sensor_mappings()
    print(f"\n{'🎉 VALIDATION PASSED' if success else '⚠️  VALIDATION FOUND ISSUES'}")
    sys.exit(0 if success else 1)
