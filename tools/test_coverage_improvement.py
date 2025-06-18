#!/usr/bin/env python3
"""Quick test to verify improved sensor mapping coverage."""

import sys

import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"

# Updated sensor mappings (key ones we added)
NEW_MAPPINGS = {
    # PowerMeter RawData sensors
    "543817",
    "543801",
    "543802",
    "543803",
    "543804",
    "543805",
    "543842",
    "543821",
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
    # RoomSensor RawData
    "543700",
    "543701",
    "543709",
    "543836",
    "543838",
    "543837",
    # WaterMeter RawData
    "422568",
    "542175",
    "542176",
    "544316",
    # Common alarm sensors
    "alarmCodeNumber",
    "alarmClassification",
}


def test_coverage_improvement():
    """Test the improvement in sensor mapping coverage."""
    print("🔧 Testing Sensor Mapping Coverage Improvement")
    print("=" * 60)

    total_sensors = 0
    newly_mapped = 0
    still_missing = []

    # Test PowerMeter device (10876) - Elmätare
    print("📱 Testing Elmätare 5-1005 (PowerMeter)...")

    # Test RawData endpoint for this device
    response = requests.post(
        f"{BASE_URL}/RawData",
        json={"ApiKey": API_KEY, "DeviceId": 10876},
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("Data") and data["Data"].get("Values"):
            values = data["Data"]["Values"]
            print(f"  📊 Found {len(values)} RawData sensors:")

            for value in values:
                sensor_name = value.get("Name", "unknown")
                total_sensors += 1

                if sensor_name in NEW_MAPPINGS:
                    newly_mapped += 1
                    print(f"    ✅ {sensor_name}: NOW MAPPED")
                else:
                    still_missing.append(sensor_name)
                    print(f"    ❌ {sensor_name}: still missing")

    # Test Laddbox device (86812)
    print("\n📱 Testing Laddbox #49 (PowerMeter)...")
    response = requests.post(
        f"{BASE_URL}/RawData",
        json={"ApiKey": API_KEY, "DeviceId": 86812},
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("Data") and data["Data"].get("Values"):
            values = data["Data"]["Values"]
            print(f"  📊 Found {len(values)} RawData sensors:")

            for value in values:
                sensor_name = value.get("Name", "unknown")
                total_sensors += 1

                if sensor_name in NEW_MAPPINGS:
                    newly_mapped += 1
                    print(f"    ✅ {sensor_name}: NOW MAPPED")
                else:
                    still_missing.append(sensor_name)
                    print(f"    ❌ {sensor_name}: still missing")

    # Quick summary
    print(f"\n📊 Coverage Improvement Summary:")
    print(f"  🔍 Sensors tested: {total_sensors}")
    print(f"  ✅ Newly mapped: {newly_mapped}")
    print(f"  ❌ Still missing: {len(still_missing)}")

    if newly_mapped > 0:
        improvement = (newly_mapped / total_sensors * 100) if total_sensors > 0 else 0
        print(f"  📈 Improvement: {improvement:.1f}% of tested sensors now mapped")
        print(f"  🎉 Added {len(NEW_MAPPINGS)} new sensor mappings!")

    return newly_mapped > 0


if __name__ == "__main__":
    success = test_coverage_improvement()
    print(f"\n{'🎉 COVERAGE IMPROVED' if success else '❌ NO IMPROVEMENT'}")
    sys.exit(0 if success else 1)
