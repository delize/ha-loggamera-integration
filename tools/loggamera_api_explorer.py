#!/usr/bin/env python3
"""
Loggamera API Explorer 2

A simple utility to explore the Loggamera API and test different endpoints.
This script is useful for debugging integration issues.

Usage:
  python loggamera_api_explorer_2.py API_KEY ENDPOINT [--device-id DEVICE_ID] [--org-id ORG_ID]

Examples:
  python loggamera_api_explorer_2.py YOUR_API_KEY Organizations
  python loggamera_api_explorer_2.py YOUR_API_KEY Devices --org-id YOURORGID
  python loggamera_api_explorer_2.py YOUR_API_KEY PowerMeter --device-id YOURDEVICEID
  python loggamera_api_explorer_2.py YOUR_API_KEY RawData --device-id YOURDEVICEID
"""

import argparse
import json
import sys
from datetime import datetime

import requests

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"


def make_api_request(
    endpoint, api_key, device_id=None, org_id=None, pretty_print=True, from_date=None
):
    """Make a request to the API and display the result."""
    url = f"{BASE_URL}/{endpoint}"

    # Build data payload
    data = {}

    # Special handling for PowerMeter endpoint based on example
    if endpoint == "PowerMeter" and device_id:
        # Use the format from the example:
        # {"ApiKey": "YOUR_API_KEY", "DeviceId": YOUR_DEVICE_ID, "DateTimeUtc": "2019-02-26T10:48:00Z"}
        date_time = (
            from_date if from_date else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        data = {"ApiKey": api_key, "DeviceId": int(device_id), "DateTimeUtc": date_time}
    else:
        # Standard format for other endpoints
        if device_id:
            data["DeviceId"] = int(device_id)

        if org_id:
            data["OrganizationId"] = int(org_id)

        if from_date:
            data["FromDate"] = from_date

    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}

    print(f"Making request to: {url}")
    print(f"Request headers: {json.dumps(headers, indent=2)}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()

                # Check if pretty print is requested
                if pretty_print:
                    formatted_result = json.dumps(result, indent=2)
                    print(f"Response:\n{formatted_result}")
                else:
                    print(f"Response: {result}")

                # Special handling for PowerMeter to extract readings
                if (
                    endpoint == "PowerMeter"
                    and "Data" in result
                    and result["Data"] is not None
                ):
                    if "PowerReadings" in result["Data"]:
                        readings = result["Data"]["PowerReadings"]
                        if readings:
                            print(f"\nFound {len(readings)} power readings")
                            print(
                                f"Latest reading: {json.dumps(readings[-1], indent=2)}"
                            )

                            # For energy dashboard compatibility
                            if "ConsumedTotalInkWh" in readings[-1]:
                                print(
                                    f"\nEnergy consumption: {readings[-1]['ConsumedTotalInkWh']} kWh"
                                )
                            if "PowerInkW" in readings[-1]:
                                print(f"Current power: {readings[-1]['PowerInkW']} kW")

                    if "Values" in result["Data"]:
                        values = result["Data"]["Values"]
                        print(f"\nFound {len(values)} values in response")
                        for val in values:
                            if "Name" in val and "Value" in val:
                                unit = val.get("UnitPresentation", "")
                                print(f"{val['Name']} = {val['Value']} {unit}")

                return result
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw response: {response.text}")
                return None
        else:
            print(f"HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Run the explorer."""
    parser = argparse.ArgumentParser(description="Loggamera API Explorer")
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument(
        "endpoint",
        help="API endpoint to test (e.g., Organizations, Devices, PowerMeter)",
    )
    parser.add_argument(
        "--device-id", type=int, help="Device ID for device-specific endpoints"
    )
    parser.add_argument(
        "--org-id", type=int, help="Organization ID for organization-specific endpoints"
    )
    parser.add_argument(
        "--from-date",
        help="From date for historical data (ISO format, e.g., 2025-05-01T00:00:00Z)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Display raw response without pretty printing",
    )

    args = parser.parse_args()

    print(f"Loggamera API Explorer - Testing endpoint: {args.endpoint}")
    print("=" * 50)

    make_api_request(
        args.endpoint,
        args.api_key,
        args.device_id,
        args.org_id,
        not args.raw,
        args.from_date,
    )


if __name__ == "__main__":
    main()
