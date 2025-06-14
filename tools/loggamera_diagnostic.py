#!/usr/bin/env python3
"""
Loggamera Diagnostic Tool

This script is a comprehensive diagnostic tool for the Loggamera API.
It tests all endpoints and provides detailed information about the response.

Usage:
  python loggamera_diagnostic.py API_KEY [--verbose] [--org-id ORG_ID] [--device-id DEVICE_ID]

Example:
  python loggamera_diagnostic.py YOUR_API_KEY --verbose
"""

import argparse
import json
import ssl
import sys
from datetime import datetime
from pprint import pprint

import certifi
import requests

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"
ENDPOINTS = {
    "organizations": "Organizations",
    "devices": "Devices",
    "power_meter": "PowerMeter",
    "room_sensor": "RoomSensor",
    "generic_device": "GenericDevice",
    "water_meter": "WaterMeter",
    "cooling_unit": "CoolingUnit",
    "heat_pump": "HeatPump",
    "raw_data": "RawData",
    "capabilities": "GetCapabilities",
    "scenarios": "Scenarios",
}


def print_header(title, char="="):
    """Print a section header."""
    print(f"\n{title}")
    print(char * len(title))


def make_api_request(endpoint, data, verbose=False):
    """Make a request to the API and return the result."""
    url = f"{BASE_URL}/{endpoint}"

    if verbose:
        print(f"Request URL: {url}")
        print(f"Request data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30,
            verify=certifi.where(),
        )

        if verbose:
            print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                if verbose:
                    print("Response JSON:")
                    pprint(result)

                # Check for common error messages
                if "Message" in result and result["Message"] == "access denied":
                    print("⚠️ Access denied error!")
                    return None
                elif "Message" in result and result["Message"] == "invalid endpoint":
                    print("⚠️ Invalid endpoint error!")
                    return None
                elif (
                    "Error" in result and result["Error"] and result["Error"] != "null"
                ):
                    print(f"⚠️ API error: {result['Error']}")
                    return None

                return result
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response as JSON: {e}")
                if verbose:
                    print(f"Response text: {response.text}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            if verbose:
                print(f"Response text: {response.text}")
            return None
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL error: {e}")
        print(f"Certificate path: {certifi.where()}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None


def test_organizations(api_key, verbose=False):
    """Test the Organizations endpoint."""
    print_header("Testing Organizations Endpoint")

    data = {"ApiKey": api_key}
    result = make_api_request(ENDPOINTS["organizations"], data, verbose)

    if result and "Data" in result and "Organizations" in result["Data"]:
        organizations = result["Data"]["Organizations"]
        print(f"✅ Success! Found {len(organizations)} organizations:")
        for org in organizations:
            print(f"  • {org['Name']} (ID: {org['Id']})")
        return organizations
    else:
        print("❌ Failed to get organizations")
        return []


def test_devices(api_key, org_id, verbose=False):
    """Test the Devices endpoint."""
    print_header("Testing Devices Endpoint")

    data = {"ApiKey": api_key, "OrganizationId": org_id}
    result = make_api_request(ENDPOINTS["devices"], data, verbose)

    if result and "Data" in result and "Devices" in result["Data"]:
        devices = result["Data"]["Devices"]
        print(f"✅ Success! Found {len(devices)} devices:")
        for device in devices:
            print(
                f"  • {device['Title'] or 'Unnamed'} (ID: {device['Id']}, Type: {device['Class']})"
            )
        return devices
    else:
        print("❌ Failed to get devices")
        return []


def test_device_data(api_key, device_id, device_type, verbose=False):
    """Test device-specific endpoints."""
    print_header(f"Testing {device_type} Endpoint for Device {device_id}")

    # Determine endpoint based on device type
    endpoint_key = None
    if device_type == "PowerMeter":
        endpoint_key = "power_meter"
    elif device_type == "RoomSensor":
        endpoint_key = "room_sensor"
    elif device_type == "WaterMeter":
        endpoint_key = "water_meter"
    elif device_type == "CoolingUnit":
        endpoint_key = "cooling_unit"
    elif device_type == "HeatPump":
        endpoint_key = "heat_pump"
    else:
        endpoint_key = "generic_device"

    # Make the request without DateTimeUtc to get current data
    data = {"ApiKey": api_key, "DeviceId": device_id}
    result = make_api_request(ENDPOINTS[endpoint_key], data, verbose)

    if result and "Data" in result and "Values" in result["Data"]:
        values = result["Data"]["Values"]
        print(f"✅ Success! Found {len(values)} values:")
        for value in values:
            print(
                f"  • {value['ClearTextName']}: {value['Value']} {value.get('UnitPresentation', '')}"
            )
        return values
    else:
        print(f"❌ Failed to get data for {device_type} endpoint")
        return None


def test_raw_data(api_key, device_id, verbose=False):
    """Test the RawData endpoint."""
    print_header(f"Testing RawData Endpoint for Device {device_id}")

    # Make the request without DateTimeUtc to get current data
    data = {"ApiKey": api_key, "DeviceId": device_id}
    result = make_api_request(ENDPOINTS["raw_data"], data, verbose)

    if result and "Data" in result and "Values" in result["Data"]:
        values = result["Data"]["Values"]
        print(f"✅ Success! Found {len(values)} values in raw data:")
        for value in values:
            print(
                f"  • {value['ClearTextName']}: {value['Value']} {value.get('UnitPresentation', '')}"
            )
        return values
    else:
        print("❌ Failed to get raw data")
        return None


def test_capabilities(api_key, device_id, verbose=False):
    """Test the GetCapabilities endpoint."""
    print_header(f"Testing Capabilities Endpoint for Device {device_id}")

    # Make the request
    data = {"ApiKey": api_key, "DeviceId": device_id}
    result = make_api_request(ENDPOINTS["capabilities"], data, verbose)

    if result and "Data" in result and "Capabilities" in result["Data"]:
        capabilities = result["Data"]["Capabilities"]
        print(f"✅ Success! Found {len(capabilities)} capabilities:")
        for cap in capabilities:
            print(f"  • {cap['Name']} ({cap.get('Mode', '')})")
        return capabilities
    else:
        print("❌ Failed to get capabilities")
        return None


def test_scenarios(api_key, org_id, verbose=False):
    """Test the Scenarios endpoint."""
    print_header("Testing Scenarios Endpoint")

    data = {"ApiKey": api_key, "OrganizationId": org_id}
    result = make_api_request(ENDPOINTS["scenarios"], data, verbose)

    if result and "Data" in result and "Scenarios" in result["Data"]:
        scenarios = result["Data"]["Scenarios"]
        print(f"✅ Success! Found {len(scenarios)} scenarios:")
        for scenario in scenarios:
            print(f"  • {scenario['Name']} (ID: {scenario['Id']})")
        return scenarios
    else:
        print("❌ Failed to get scenarios or no scenarios found")
        return []


def test_generic_device(api_key, device_id, verbose=False):
    """Test the GenericDevice endpoint as a fallback."""
    print_header(f"Testing GenericDevice Endpoint for Device {device_id}")

    # Make the request without DateTimeUtc
    data = {"ApiKey": api_key, "DeviceId": device_id}
    result = make_api_request(ENDPOINTS["generic_device"], data, verbose)

    if result and "Data" in result and "Values" in result["Data"]:
        values = result["Data"]["Values"]
        print(f"✅ Success! Found {len(values)} values:")
        for value in values:
            print(
                f"  • {value['ClearTextName']}: {value['Value']} {value.get('UnitPresentation', '')}"
            )
        return values
    else:
        print("❌ Failed to get data for GenericDevice endpoint")
        return None


def print_system_info():
    """Print system information."""
    print_header("System Information")
    print(f"Python: {sys.version}")
    print(f"OpenSSL: {ssl.OPENSSL_VERSION}")
    print(f"Certificate: {certifi.where()}")
    print(f"API URL: {BASE_URL}")


def main():
    """Run the diagnostics."""
    parser = argparse.ArgumentParser(description="Loggamera API Diagnostic Tool")
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose output"
    )
    parser.add_argument("--org-id", type=int, help="Specify organization ID")
    parser.add_argument("--device-id", type=int, help="Specify device ID")

    args = parser.parse_args()

    print("🔍 Loggamera API Diagnostic Tool 🔍")
    print("=" * 40)

    if args.verbose:
        print_system_info()

    # Test Organizations endpoint
    organizations = test_organizations(args.api_key, args.verbose)

    if not organizations:
        print("\n❌ Critical error: Cannot get organizations. Check your API key.")
        return

    # Get organization ID (from args or first from list)
    org_id = args.org_id
    if not org_id and organizations:
        org_id = organizations[0]["Id"]
        print(f"\nℹ️ Using organization ID: {org_id}")

    # Test Devices endpoint
    devices = test_devices(args.api_key, org_id, args.verbose)

    if not devices:
        print("\n❌ Critical error: Cannot get devices.")
        return

    # Get device ID (from args or first from list)
    device_id = args.device_id
    if not device_id and devices:
        device_id = devices[0]["Id"]
        device_type = devices[0]["Class"]
        print(f"\nℹ️ Using device ID: {device_id} (Type: {device_type})")
    else:
        # Find device type for the specified device ID
        device_type = next(
            (d["Class"] for d in devices if d["Id"] == device_id), "GenericDevice"
        )

    # Test device-specific endpoint
    values = test_device_data(args.api_key, device_id, device_type, args.verbose)

    # If device-specific endpoint fails, try RawData as fallback
    if not values:
        print("\nℹ️ Trying RawData endpoint as fallback...")
        values = test_raw_data(args.api_key, device_id, args.verbose)

    # If RawData fails, try GenericDevice as a final fallback
    if not values:
        print("\nℹ️ Trying GenericDevice endpoint as final fallback...")
        values = test_generic_device(args.api_key, device_id, args.verbose)

    # Test capabilities
    capabilities = test_capabilities(args.api_key, device_id, args.verbose)

    # Test scenarios
    scenarios = test_scenarios(args.api_key, org_id, args.verbose)

    # Print summary
    print_header("Diagnostic Summary", "-")

    print("Organization access:", "✅ Success" if organizations else "❌ Failed")
    print("Device access:", "✅ Success" if devices else "❌ Failed")
    print("Device data access:", "✅ Success" if values else "❌ Failed")
    print("Capabilities access:", "✅ Success" if capabilities else "❌ Failed")
    print("Scenarios access:", "✅ Success" if scenarios else "❌ Failed")

    print("\nRecommended integration settings:")
    print(f"API Key: {args.api_key[:5]}...{args.api_key[-5:]}")
    print(f"Organization ID: {org_id}")

    print("\n🔍 Diagnostic complete! 🔍")


if __name__ == "__main__":
    main()
