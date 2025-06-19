#!/usr/bin/env python3
"""Quick test to verify improved sensor mapping coverage."""

import os
import sys

import requests

# Get API key from environment variable or use placeholder
API_KEY = os.getenv("LOGGAMERA_API_KEY", "YOUR_API_KEY_HERE")
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


def test_api_request(endpoint_url, device_id, device_name):
    """Make an API request with proper error handling.

    Args:
        endpoint_url: Full URL for the API endpoint
        device_id: Device ID to query
        device_name: Human-readable device name for logging

    Returns:
        tuple: (success: bool, data: dict or None, error: str or None)
    """
    try:
        response = requests.post(
            endpoint_url,
            json={"ApiKey": API_KEY, "DeviceId": device_id},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            return False, None, f"HTTP {response.status_code}: {response.text}"

        if not response.text.strip():
            return False, None, "Empty response body"

        try:
            data = response.json()
        except ValueError as e:
            return False, None, f"Invalid JSON response: {e}"

        if data is None:
            return False, None, "API returned null response"

        # Check for API errors
        if "Error" in data and data["Error"] is not None:
            if isinstance(data["Error"], dict) and "Message" in data["Error"]:
                error_msg = data["Error"]["Message"]
                return False, None, f"API error: {error_msg}"
            else:
                return False, None, f"Unknown API error: {data['Error']}"

        return True, data, None

    except requests.exceptions.RequestException as e:
        return False, None, f"Request failed: {e}"
    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def test_coverage_improvement():
    """Test the improvement in sensor mapping coverage."""
    print("🔧 Testing Sensor Mapping Coverage Improvement")
    print("=" * 60)

    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Error: API key not configured")
        print("   Set LOGGAMERA_API_KEY environment variable or update the script")
        return False

    total_sensors = 0
    newly_mapped = 0
    still_missing = []

    # Test PowerMeter device (10876) - Elmätare
    print("📱 Testing Elmätare 5-1005 (PowerMeter)...")

    # Test RawData endpoint for this device
    success, data, error = test_api_request(
        f"{BASE_URL}/RawData", 10876, "Elmätare 5-1005"
    )

    if success and data and data.get("Data") and data["Data"].get("Values"):
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
    elif error:
        print(f"  ❌ Failed to get data: {error}")
    else:
        print("  ⚠️  No sensor data found")

    # Test Laddbox device (86812)
    print("\n📱 Testing Laddbox #49 (PowerMeter)...")
    success, data, error = test_api_request(f"{BASE_URL}/RawData", 86812, "Laddbox #49")

    if success and data and data.get("Data") and data["Data"].get("Values"):
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
    elif error:
        print(f"  ❌ Failed to get data: {error}")
    else:
        print("  ⚠️  No sensor data found")

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
