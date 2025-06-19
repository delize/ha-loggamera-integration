#!/usr/bin/env python3
"""
Check for data gaps in Loggamera API responses.

This tool checks the current data gap status and provides detailed information
about any devices experiencing data issues.

Usage:
    python tools/check_data_gaps.py API_KEY [--organization-id ORG_ID] [--verbose]

Example:
    python tools/check_data_gaps.py your_api_key_here --verbose
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.loggamera.api import LoggameraAPI


def main():
    """Check for data gaps and API health issues."""
    parser = argparse.ArgumentParser(description="Check Loggamera API data gaps")
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument("--organization-id", help="Organization ID (optional)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key is required", file=sys.stderr)
        return 1

    try:
        # Initialize API client
        print("Initializing Loggamera API client...")
        api = LoggameraAPI(api_key=args.api_key, organization_id=args.organization_id)

        # Get devices to populate data gap tracker
        print("Fetching device list...")
        devices_response = api.get_devices()

        if not devices_response.get("Data", {}).get("Devices"):
            print("No devices found or API error")
            return 1

        devices = devices_response["Data"]["Devices"]
        print(f"Found {len(devices)} devices")

        # Test each device to populate gap tracker
        print("\nTesting device data availability...")
        for device in devices:
            device_id = device["Id"]
            device_type = device["Class"]
            device_name = device.get("Title", f"{device_type} {device_id}")

            if args.verbose:
                print(f"  Testing device {device_id} ({device_name})...")

            try:
                # Try to get device data - this will populate the gap tracker
                device_data = api.get_device_data(device_id, device_type)
                has_data = api._has_valid_data(device_data)

                if args.verbose:
                    status = "✓ OK" if has_data else "✗ NO DATA"
                    print(f"    {status}")

            except Exception as e:
                if args.verbose:
                    print(f"    ✗ ERROR: {e}")

        # Get data gap status
        print("\nData Gap Analysis:")
        print("=" * 50)

        gap_status = api.get_data_gap_status()

        if args.json:
            print(json.dumps(gap_status, indent=2, default=str))
            return 0

        # Summary
        devices_with_gaps = gap_status.get("devices_with_gaps", 0)
        total_devices = gap_status.get("total_devices_tracked", 0)

        if devices_with_gaps == 0:
            print("✅ No data gaps detected!")
            print(f"All {total_devices} devices are reporting data successfully.")
        else:
            print(f"⚠️  Data gaps detected: {devices_with_gaps}/{total_devices} devices affected")

            # Show affected devices
            print("\nAffected Devices:")
            print("-" * 30)

            for device_id, device_status in gap_status.get("devices", {}).items():
                if device_status.get("has_active_gap", False):
                    gap_minutes = device_status.get("gap_duration_minutes", 0)
                    failures = device_status.get("consecutive_failures", 0)
                    endpoint = device_status.get("endpoint", "unknown")
                    total_gaps = device_status.get("total_gaps", 0)

                    print(f"Device {device_id}:")
                    print(f"  ⏱️  Gap Duration: {gap_minutes} minutes")
                    print(f"  🔄 Consecutive Failures: {failures}")
                    print(f"  🔗 Endpoint: {endpoint}")
                    print(f"  📊 Total Gaps (Session): {total_gaps}")
                    print()

        # Show summary statistics
        if gap_status.get("devices") and args.verbose:
            print("\nDetailed Statistics:")
            print("-" * 30)

            total_gaps_all = sum(
                device.get("total_gaps", 0) for device in gap_status["devices"].values()
            )
            print(f"Total gaps across all devices: {total_gaps_all}")

            # Find device with most gaps
            max_gaps_device = None
            max_gaps_count = 0
            for device_id, device_status in gap_status["devices"].items():
                gaps = device_status.get("total_gaps", 0)
                if gaps > max_gaps_count:
                    max_gaps_count = gaps
                    max_gaps_device = device_id

            if max_gaps_device:
                print(f"Device with most gaps: {max_gaps_device} ({max_gaps_count} gaps)")

            # Show devices with recent successful data
            recent_success = []
            for device_id, device_status in gap_status["devices"].items():
                if not device_status.get("has_active_gap", False):
                    minutes_since = device_status.get("minutes_since_last_success", 0)
                    if minutes_since < 60:  # Less than 1 hour ago
                        recent_success.append((device_id, minutes_since))

            if recent_success:
                print(f"\nDevices with recent successful data ({len(recent_success)}):")
                for device_id, minutes_ago in sorted(recent_success, key=lambda x: x[1]):
                    print(f"  Device {device_id}: {minutes_ago} minutes ago")

        # Recommendations
        if devices_with_gaps > 0:
            print("\n💡 Recommendations:")
            print("1. Check Home Assistant logs for specific error messages")
            print("2. Monitor the 'Loggamera API Health' binary sensor")
            print("3. Run this tool periodically to track gap patterns")
            print("4. Consider time-based correlation (e.g., 4 AM processing windows)")
            print("5. Compare test vs production environment behaviors")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
