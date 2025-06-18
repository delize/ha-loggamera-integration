#!/usr/bin/env python3
"""Final test of sensor mapping coverage."""

import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"

# Current sensor mappings from sensor.py (manually extracted for testing)
CURRENT_MAPPINGS = {
    # Organization/standard sensors
    "ConsumedTotalInkWh",
    "PowerInkW",
    "alarmActive",
    "alarmInClearText",
    "device_count",
    "organization_count",
    "parent_organization",
    "child_organizations",
    "user_count",
    "member_count",
    # HeatMeter sensors
    "544310",
    "544311",
    "544320",
    "544321",
    "544322",
    "544323",
    "544324",
    # PowerMeter RawData sensors
    "543817",
    "543801",
    "543802",
    "543803",
    "543804",
    "543805",
    "543842",
    "543821",
    "544352",
    "544353",
    "544399",
    # Laddbox sensors
    "544424",
    "544434",
    "544426",
    "544427",
    "544428",
    "544429",
    "544430",
    "544431",
    "544425",
    "544443",
    "544441",
    "544442",
    "544432",
    "544436",
    "544437",
    # RoomSensor sensors
    "Temperature",
    "RelativeHumidity",
    "543700",
    "543701",
    "543709",
    "543836",
    "543838",
    "543837",
    # WaterMeter sensors
    "ConsumedTotalInM3",
    "ConsumedSinceMidnightInLiters",
    "422568",
    "542175",
    "542176",
    "544316",
    # Common alarm sensors
    "alarmCodeNumber",
    "alarmClassification",
}


def test_final_coverage():
    """Test final sensor mapping coverage."""
    print("🎯 Final Sensor Mapping Coverage Test")
    print("=" * 50)

    total_sensors = 0
    mapped_sensors = 0
    unmapped_sensors = []

    # Get all devices across organizations
    org_response = requests.post(
        f"{BASE_URL}/Organizations",
        json={"ApiKey": API_KEY},
        headers={"Content-Type": "application/json"},
    )

    organizations = org_response.json().get("Data", {}).get("Organizations", [])

    for org in organizations:
        org_id = org["Id"]

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

            # Test main endpoint + RawData + GenericDevice
            endpoints = []

            # Primary endpoint based on device type
            if device_type == "PowerMeter":
                endpoints.append(("PowerMeter", f"{BASE_URL}/PowerMeter"))
            elif device_type == "RoomSensor":
                endpoints.append(("RoomSensor", f"{BASE_URL}/RoomSensor"))
            elif device_type == "WaterMeter":
                endpoints.append(("WaterMeter", f"{BASE_URL}/WaterMeter"))
            elif device_type == "HeatMeter":
                # HeatMeter uses RawData as primary
                pass

            # Always test RawData and GenericDevice
            endpoints.extend(
                [
                    ("RawData", f"{BASE_URL}/RawData"),
                    ("GenericDevice", f"{BASE_URL}/GenericDevice"),
                ]
            )

            device_mapped = 0
            device_total = 0

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
                            for value in values:
                                sensor_name = value.get("Name", "unknown")
                                sensor_desc = value.get("ClearTextName", "")
                                sensor_value = value.get("Value", "N/A")
                                sensor_unit = value.get("UnitPresentation", "")

                                total_sensors += 1
                                device_total += 1

                                if sensor_name in CURRENT_MAPPINGS:
                                    mapped_sensors += 1
                                    device_mapped += 1
                                    print(f"    ✅ {sensor_name} ({endpoint_name})")
                                else:
                                    unmapped_sensors.append(
                                        {
                                            "name": sensor_name,
                                            "device": device_name,
                                            "endpoint": endpoint_name,
                                            "description": sensor_desc,
                                            "value": sensor_value,
                                            "unit": sensor_unit,
                                        }
                                    )
                                    print(
                                        f"    ❌ {sensor_name} ({endpoint_name}): {sensor_desc}"
                                    )

            if device_total > 0:
                device_coverage = (device_mapped / device_total) * 100
                print(
                    f"  📊 Device coverage: {device_mapped}/{device_total} ({device_coverage:.1f}%)"
                )

    # Final summary
    print(f"\n" + "=" * 60)
    print(f"🎯 FINAL COVERAGE RESULTS")
    print(f"=" * 60)

    if total_sensors > 0:
        overall_coverage = (mapped_sensors / total_sensors) * 100
        print(
            f"📈 Overall Coverage: {mapped_sensors}/{total_sensors} ({overall_coverage:.1f}%)"
        )
        print(f"📦 Total mappings available: {len(CURRENT_MAPPINGS)}")
        print(f"❌ Still missing: {len(unmapped_sensors)} sensors")

        if unmapped_sensors:
            print(f"\n🔍 Remaining unmapped sensors:")
            for sensor in unmapped_sensors[:10]:
                print(
                    f"  - {sensor['name']}: {sensor['description']} ({sensor['endpoint']})"
                )
            if len(unmapped_sensors) > 10:
                print(f"  ... and {len(unmapped_sensors) - 10} more")

    return overall_coverage if total_sensors > 0 else 0


if __name__ == "__main__":
    coverage = test_final_coverage()
    print(f"\n🎯 Final Coverage: {coverage:.1f}%")

    if coverage >= 80:
        print("🎉 EXCELLENT COVERAGE!")
    elif coverage >= 60:
        print("✅ GOOD COVERAGE")
    else:
        print("⚠️  MORE MAPPINGS NEEDED")
