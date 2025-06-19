#!/usr/bin/env python3
"""Final test of sensor mapping coverage."""

import os
import sys

import requests

# Get API key from environment variable or use placeholder
API_KEY = os.getenv("LOGGAMERA_API_KEY", "YOUR_API_KEY_HERE")
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


def make_api_request(endpoint_url, data=None):
    """Make an API request with proper error handling.

    Args:
        endpoint_url: Full URL for the API endpoint
        data: Optional request data (ApiKey will be added)

    Returns:
        tuple: (success: bool, response_data: dict or None, error: str or None)
    """
    try:
        if data is None:
            data = {}

        # Always include API key
        if "ApiKey" not in data:
            data["ApiKey"] = API_KEY

        response = requests.post(
            endpoint_url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 200:
            return False, None, f"HTTP {response.status_code}: {response.text}"

        if not response.text.strip():
            return False, None, "Empty response body"

        try:
            response_data = response.json()
        except ValueError as e:
            return False, None, f"Invalid JSON response: {e}"

        if response_data is None:
            return False, None, "API returned null response"

        # Check for API errors
        if "Error" in response_data and response_data["Error"] is not None:
            if (
                isinstance(response_data["Error"], dict)
                and "Message" in response_data["Error"]
            ):
                error_msg = response_data["Error"]["Message"]
                if error_msg == "invalid endpoint":
                    return False, None, f"Invalid endpoint: {endpoint_url}"
                return False, None, f"API error: {error_msg}"
            else:
                return False, None, f"Unknown API error: {response_data['Error']}"

        return True, response_data, None

    except requests.exceptions.RequestException as e:
        return False, None, f"Request failed: {e}"
    except Exception as e:
        return False, None, f"Unexpected error: {e}"


def test_final_coverage():
    """Test final sensor mapping coverage."""
    print("🎯 Final Sensor Mapping Coverage Test")
    print("=" * 50)

    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Error: API key not configured")
        print("   Set LOGGAMERA_API_KEY environment variable or update the script")
        return 0.0

    total_sensors = 0
    mapped_sensors = 0
    unmapped_sensors = []

    # Get all devices across organizations
    print("🏭 Getting organizations...")
    success, org_data, error = make_api_request(f"{BASE_URL}/Organizations")

    if not success:
        print(f"❌ Failed to get organizations: {error}")
        return 0.0

    if not org_data or not org_data.get("Data"):
        print("❌ No organization data found")
        return 0.0

    organizations = org_data.get("Data", {}).get("Organizations", [])
    if not organizations:
        print("❌ No organizations found")
        return 0.0

    print(f"✅ Found {len(organizations)} organizations")

    for org in organizations:
        org_id = org.get("Id")
        org_name = org.get("Name", f"Org {org_id}")

        if not org_id:
            continue

        print(f"\n🏢 Processing {org_name} (ID: {org_id})...")

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
        if not devices:
            print("  ⚠️  No devices found")
            continue

        print(f"  📱 Found {len(devices)} devices")

        for device in devices:
            device_id = device.get("Id")
            device_name = device.get("Title", f"Device {device_id}")
            device_type = device.get("Class", "Unknown")

            if not device_id:
                continue

            print(f"\n    📱 {device_name} ({device_type}):")

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
                success, data, error = make_api_request(
                    endpoint_url, {"DeviceId": device_id}
                )

                if success and data and data.get("Data") and data["Data"].get("Values"):
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
                                print(f"      ✅ {sensor_name} ({endpoint_name})")
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
                                    f"      ❌ {sensor_name} ({endpoint_name}): {sensor_desc}"
                                )
                elif error and "invalid endpoint" not in error.lower():
                    print(f"      ⚠️  {endpoint_name} failed: {error}")

            if device_total > 0:
                device_coverage = (device_mapped / device_total) * 100
                print(
                    f"    📊 Device coverage: {device_mapped}/{device_total} ({device_coverage:.1f}%)"
                )
            else:
                print("    ⚠️  No sensors found for this device")

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
    else:
        overall_coverage = 0.0
        print("⚠️  No sensors found to test")

    return overall_coverage


if __name__ == "__main__":
    try:
        coverage = test_final_coverage()
        print(f"\n🎯 Final Coverage: {coverage:.1f}%")

        if coverage >= 80:
            print("🎉 EXCELLENT COVERAGE!")
        elif coverage >= 60:
            print("✅ GOOD COVERAGE")
        elif coverage > 0:
            print("⚠️  MORE MAPPINGS NEEDED")
        else:
            print("🚫 NO DATA AVAILABLE")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
