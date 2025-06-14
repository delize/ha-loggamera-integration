#!/usr/bin/env python3
"""
Loggamera API Test Tool

A simple utility to directly test Loggamera API calls using different formats.
This tool is useful for debugging integration issues.

Usage:
  python api_test.py [--test TESTNAME] API_KEY [DEVICE_ID]

Examples:
  python api_test.py YOUR_API_KEY
  python api_test.py --test organizations YOUR_API_KEY
  python api_test.py --test powermeter YOUR_API_KEY YOUR_DEVICE_ID
  python api_test.py --test combined YOUR_API_KEY YOUR_DEVICE_ID
"""

import argparse
import json
import sys
from datetime import datetime

import requests

BASE_URL = "https://platform.loggamera.se/api/v2"


def test_organizations(api_key):
    """Test Organizations endpoint."""
    url = f"{BASE_URL}/Organizations"
    headers = {"Content-Type": "application/json"}
    data = {"ApiKey": api_key}

    print(f"Testing Organizations - API key in body")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_powermeter(api_key, device_id):
    """Test PowerMeter endpoint with both request formats."""
    print("\nTesting PowerMeter endpoint - Simple format")
    print("=" * 80)

    # Test without DateTimeUtc first (simple format)
    url = f"{BASE_URL}/PowerMeter"
    headers = {"Content-Type": "application/json"}
    data = {"ApiKey": api_key, "DeviceId": int(device_id)}

    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 80)

    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status code: {response.status_code}")

    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        # If we have values, print them
        if (
            "Data" in result
            and result["Data"] is not None
            and "Values" in result["Data"]
        ):
            values = result["Data"]["Values"]
            print(f"\nFound {len(values)} values:")
            for value in values:
                name = value.get("Name", "unknown")
                clear_name = value.get("ClearTextName", name)
                val = value.get("Value", "")
                unit = value.get("UnitPresentation", "")
                print(f"- {clear_name} ({name}): {val} {unit}")
        else:
            print("\nNo values found in the response")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")

    # Now test with DateTimeUtc
    print("\nTesting PowerMeter endpoint - With DateTimeUtc")
    print("=" * 80)

    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    data_with_time = {
        "ApiKey": api_key,
        "DeviceId": int(device_id),
        "DateTimeUtc": current_time,
    }

    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Request data: {json.dumps(data_with_time, indent=2)}")
    print("-" * 80)

    response = requests.post(url, headers=headers, json=data_with_time, timeout=30)
    print(f"Status code: {response.status_code}")

    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        # If we have values, print them
        if (
            "Data" in result
            and result["Data"] is not None
            and "Values" in result["Data"]
        ):
            values = result["Data"]["Values"]
            print(f"\nFound {len(values)} values:")
            for value in values:
                name = value.get("Name", "unknown")
                clear_name = value.get("ClearTextName", name)
                val = value.get("Value", "")
                unit = value.get("UnitPresentation", "")
                print(f"- {clear_name} ({name}): {val} {unit}")
        else:
            print("\nNo values found in the response")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw response: {response.text}")


def test_devices(api_key, org_id=None):
    """Test Devices endpoint with organization ID."""
    url = f"{BASE_URL}/Devices"
    headers = {"Content-Type": "application/json"}
    data = {"ApiKey": api_key}
    if org_id:
        data["OrganizationId"] = int(org_id)

    print(f"\nTesting Devices - With org ID")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_raw_data(api_key, device_id):
    """Test RawData endpoint."""
    url = f"{BASE_URL}/RawData"
    headers = {"Content-Type": "application/json"}
    data = {"ApiKey": api_key, "DeviceId": int(device_id)}

    print(f"\nTesting RawData")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def test_combined_power_meter(api_key, device_id):
    """Test both RawData and PowerMeter endpoints and combine the results."""
    print(
        "\nTesting COMBINED PowerMeter data (from both RawData and PowerMeter endpoints)"
    )
    print("=" * 80)

    # Get PowerMeter data - try simple format first
    power_meter_data = {}
    power_meter_values = []
    print("1. Fetching PowerMeter data (simple format)...")
    try:
        url = f"{BASE_URL}/PowerMeter"
        headers = {"Content-Type": "application/json"}
        data = {"ApiKey": api_key, "DeviceId": int(device_id)}

        # Print detailed request info for debugging
        print(f"   URL: {url}")
        print(f"   Request data: {json.dumps(data, indent=2)}")

        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"   Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            # Print preview of response
            response_preview = json.dumps(result, indent=2)
            if len(response_preview) > 500:
                response_preview = response_preview[:500] + "..."
            print(f"   Response preview: {response_preview}")

            if (
                "Data" in result
                and result["Data"] is not None
                and "Values" in result["Data"]
                and result["Data"]["Values"]
            ):
                power_meter_data = result
                power_meter_values = result["Data"]["Values"]
                print(
                    f"   Success! Got {len(power_meter_values)} values from PowerMeter endpoint"
                )

                # Print key PowerMeter values
                print("\n   PowerMeter Key Values:")
                for value in power_meter_values:
                    name = value.get("Name", "unknown")
                    clear_name = value.get("ClearTextName", name)
                    val = value.get("Value", "")
                    unit = value.get("UnitPresentation", "")
                    if name in ["ConsumedTotalInkWh", "PowerInkW"]:
                        print(f"   - {clear_name} ({name}): {val} {unit}")
            else:
                print("   No values found in PowerMeter response with simple format")
                # Try with DateTimeUtc if simple format didn't work
                print("\n1b. Trying PowerMeter with DateTimeUtc...")
                current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                data_with_time = {
                    "ApiKey": api_key,
                    "DeviceId": int(device_id),
                    "DateTimeUtc": current_time,
                }

                print(f"   Request data: {json.dumps(data_with_time, indent=2)}")

                response = requests.post(
                    url, headers=headers, json=data_with_time, timeout=30
                )
                print(f"   Status code: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    response_preview = json.dumps(result, indent=2)
                    if len(response_preview) > 500:
                        response_preview = response_preview[:500] + "..."
                    print(f"   Response preview: {response_preview}")

                    if (
                        "Data" in result
                        and result["Data"] is not None
                        and "Values" in result["Data"]
                        and result["Data"]["Values"]
                    ):
                        power_meter_data = result
                        power_meter_values = result["Data"]["Values"]
                        print(
                            f"   Success! Got {len(power_meter_values)} values from PowerMeter endpoint with DateTimeUtc"
                        )

                        # Print key PowerMeter values
                        print("\n   PowerMeter Key Values:")
                        for value in power_meter_values:
                            name = value.get("Name", "unknown")
                            clear_name = value.get("ClearTextName", name)
                            val = value.get("Value", "")
                            unit = value.get("UnitPresentation", "")
                            if name in ["ConsumedTotalInkWh", "PowerInkW"]:
                                print(f"   - {clear_name} ({name}): {val} {unit}")
                    else:
                        print(
                            "   No values found in PowerMeter response with DateTimeUtc"
                        )
        else:
            print(f"   HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Get RawData
    raw_data = {}
    raw_values = []
    print("\n2. Fetching RawData...")
    try:
        url = f"{BASE_URL}/RawData"
        headers = {"Content-Type": "application/json"}
        data = {"ApiKey": api_key, "DeviceId": int(device_id)}

        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if (
                "Data" in result
                and result["Data"] is not None
                and "Values" in result["Data"]
            ):
                raw_data = result
                raw_values = result["Data"]["Values"]
                print(f"   Success! Got {len(raw_values)} values from RawData endpoint")

                # Print key RawData values
                print("\n   RawData Key Values:")
                for value in raw_values:
                    name = value.get("Name", "unknown")
                    clear_name = value.get("ClearTextName", name)
                    val = value.get("Value", "")
                    unit = value.get("UnitPresentation", "")
                    if name in ["544352", "544399", "550205", "550206", "550207"]:
                        print(f"   - {clear_name} ({name}): {val} {unit}")
            else:
                print("   No values found in RawData response")
        else:
            print(f"   HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # Combine the data
    print("\n3. Combining data from both endpoints...")
    combined_values = []

    # Add all PowerMeter values first
    combined_values.extend(power_meter_values)
    print(f"   Starting with {len(power_meter_values)} PowerMeter values")

    # If no PowerMeter values, create synthetic ones from RawData
    if not power_meter_values:
        synthetic_count = 0
        for value in raw_values:
            if value.get("Name") == "544352":  # Energy imported
                # Create ConsumedTotalInkWh equivalent
                synthetic_value = {
                    "Name": "ConsumedTotalInkWh",
                    "ClearTextName": "Total förbrukning",
                    "ValueType": "DECIMAL",
                    "Value": value.get("Value", "0"),
                    "UnitType": "KwH",
                    "UnitPresentation": "kWh",
                    "_synthetic": True,  # Mark as synthetic for debugging
                }
                combined_values.append(synthetic_value)
                synthetic_count += 1

            if value.get("Name") == "544399":  # Power
                # Convert from W to kW for PowerInkW
                try:
                    power_w = float(value.get("Value", "0"))
                    power_kw = power_w / 1000.0

                    # Create PowerInkW equivalent
                    synthetic_value = {
                        "Name": "PowerInkW",
                        "ClearTextName": "Effekt",
                        "ValueType": "DECIMAL",
                        "Value": str(power_kw),
                        "UnitType": "KW",
                        "UnitPresentation": "kW",
                        "_synthetic": True,  # Mark as synthetic for debugging
                    }
                    combined_values.append(synthetic_value)
                    synthetic_count += 1
                except (ValueError, TypeError):
                    print(f"   Could not convert RawData power value to kW")

        if synthetic_count > 0:
            print(
                f"   Created {synthetic_count} synthetic PowerMeter values from RawData"
            )

    # Add RawData values that don't already exist in the combined set
    existing_names = [v.get("Name") for v in combined_values]
    existing_cleartext = [
        v.get("ClearTextName") for v in combined_values if v.get("ClearTextName")
    ]

    added_count = 0
    for value in raw_values:
        # Skip if the Name already exists
        if value.get("Name") in existing_names:
            continue

        # Also skip if there's a clear text name match to avoid duplicates
        clear_name = value.get("ClearTextName")
        if clear_name and clear_name in existing_cleartext:
            continue

        # Add this unique value
        combined_values.append(value)
        existing_names.append(value.get("Name"))
        if clear_name:
            existing_cleartext.append(clear_name)
        added_count += 1

    print(f"   Added {added_count} unique values from RawData")
    print(f"   Combined data has {len(combined_values)} values total")

    # Print a summary of the combined data
    print("\nCOMBINED DATA SUMMARY")
    print("-" * 80)

    print("IMPORTANT SENSORS:")
    for value in combined_values:
        name = value.get("Name", "unknown")
        clear_name = value.get("ClearTextName", name)
        val = value.get("Value", "")
        unit = value.get("UnitPresentation", "")

        if value.get("_synthetic"):
            source = "RawData (synthetic)"
        elif name in [
            "ConsumedTotalInkWh",
            "PowerInkW",
            "alarmActive",
            "alarmInClearText",
        ]:
            source = "PowerMeter"
        else:
            source = "RawData"

        # Skip empty values
        if not val and val != "0":
            continue

        # Print important sensors with asterisks
        if name in [
            "ConsumedTotalInkWh",
            "PowerInkW",
            "544352",
            "544399",
            "550205",
            "550206",
            "550207",
        ]:
            print(f"* {clear_name} ({name}): {val} {unit} (Source: {source})")

    print("\nALL OTHER VALUES:")
    for value in combined_values:
        name = value.get("Name", "unknown")
        clear_name = value.get("ClearTextName", name)
        val = value.get("Value", "")
        unit = value.get("UnitPresentation", "")

        if value.get("_synthetic"):
            source = "RawData (synthetic)"
        elif name in [
            "ConsumedTotalInkWh",
            "PowerInkW",
            "alarmActive",
            "alarmInClearText",
        ]:
            source = "PowerMeter"
        else:
            source = "RawData"

        # Skip empty values
        if not val and val != "0":
            continue

        # Skip important sensors (already printed above)
        if name in [
            "ConsumedTotalInkWh",
            "PowerInkW",
            "544352",
            "544399",
            "550205",
            "550206",
            "550207",
        ]:
            continue

        print(f"{clear_name} ({name}): {val} {unit} (Source: {source})")

    return {
        "raw_data": raw_data,
        "power_meter_data": power_meter_data,
        "combined_values": combined_values,
    }


def main():
    """Run API tests."""
    parser = argparse.ArgumentParser(description="Loggamera API Test Tool")
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument(
        "device_id", nargs="?", help="Device ID for device-specific tests"
    )
    parser.add_argument("--org-id", help="Organization ID")
    parser.add_argument(
        "--test",
        choices=["organizations", "powermeter", "devices", "raw", "combined", "all"],
        default="all",
        help="Test to run",
    )

    args = parser.parse_args()

    if args.test == "organizations" or args.test == "all":
        test_organizations(args.api_key)

    if args.test == "devices" or args.test == "all":
        test_devices(args.api_key, args.org_id)

    if (args.test == "powermeter" or args.test == "all") and args.device_id:
        test_powermeter(args.api_key, args.device_id)

    if (args.test == "raw" or args.test == "all") and args.device_id:
        test_raw_data(args.api_key, args.device_id)

    if (args.test == "combined" or args.test == "all") and args.device_id:
        test_combined_power_meter(args.api_key, args.device_id)

    if args.test in ["powermeter", "raw", "combined", "all"] and not args.device_id:
        print(
            "Error: device_id is required for PowerMeter, RawData, and Combined tests"
        )


if __name__ == "__main__":
    main()
