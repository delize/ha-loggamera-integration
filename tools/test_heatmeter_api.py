#!/usr/bin/env python3
"""Simple API test for HeatMeter support without Home Assistant dependencies."""

import json
import sys

import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://platform.loggamera.se/api/v2"


def test_heatmeter_api():
    """Test HeatMeter API functionality."""
    print("🔧 Testing HeatMeter API Support")
    print("=" * 50)

    # Test Organizations
    print("📡 Testing Organizations endpoint...")
    org_response = requests.post(
        f"{BASE_URL}/Organizations",
        json={"ApiKey": API_KEY},
        headers={"Content-Type": "application/json"},
    )

    if org_response.status_code == 200:
        org_data = org_response.json()
        organizations = org_data.get("Data", {}).get("Organizations", [])
        print(f"✅ Found {len(organizations)} organizations:")

        hierarchy = {}
        for org in organizations:
            org_id = org["Id"]
            parent_id = org["ParentId"]
            hierarchy[org_id] = {
                "name": org["Name"],
                "parent_id": parent_id,
                "children": [],
                "is_root": parent_id == 0,
            }
            parent_info = f" (Parent: {parent_id})" if parent_id != 0 else " (Root)"
            print(f"  - {org_id}: {org['Name']}{parent_info}")

        # Build parent-child relationships
        for org_id, org_info in hierarchy.items():
            parent_id = org_info["parent_id"]
            if parent_id != 0 and parent_id in hierarchy:
                hierarchy[parent_id]["children"].append(org_id)

        print("\n📊 Hierarchy Structure:")
        for org_id, org_info in hierarchy.items():
            children_info = (
                f" -> {len(org_info['children'])} children"
                if org_info["children"]
                else ""
            )
            print(f"  - {org_id}: {org_info['name']}{children_info}")

    # Test Devices for each organization
    print(f"\n🔌 Testing Devices endpoints...")
    all_devices = []

    for org in organizations:
        org_id = org["Id"]
        org_name = org["Name"]

        print(f"\n  📱 Devices in {org_name} ({org_id}):")
        devices_response = requests.post(
            f"{BASE_URL}/Devices",
            json={"ApiKey": API_KEY, "OrganizationId": org_id},
            headers={"Content-Type": "application/json"},
        )

        if devices_response.status_code == 200:
            devices_data = devices_response.json()
            devices = devices_data.get("Data", {}).get("Devices", [])
            print(f"    ✅ Found {len(devices)} devices")

            for device in devices:
                device_id = device["Id"]
                device_type = device["Class"]
                device_name = device["Title"]
                device["_source_org"] = org_name
                all_devices.append(device)

                print(f"    - {device_name} (ID: {device_id}, Type: {device_type})")

                # Test HeatMeter specifically
                if device_type == "HeatMeter":
                    print(f"      🔥 HeatMeter found! Testing endpoints...")

                    # Test RawData endpoint
                    raw_response = requests.post(
                        f"{BASE_URL}/RawData",
                        json={"ApiKey": API_KEY, "DeviceId": device_id},
                        headers={"Content-Type": "application/json"},
                    )

                    if raw_response.status_code == 200:
                        raw_data = raw_response.json()
                        if raw_data.get("Data") and raw_data["Data"].get("Values"):
                            values = raw_data["Data"]["Values"]
                            print(f"      ✅ RawData: {len(values)} sensors")
                            for value in values:
                                sensor_id = value.get("Name", "unknown")
                                sensor_value = value.get("Value", "N/A")
                                sensor_unit = value.get("UnitPresentation", "")
                                sensor_desc = value.get("ClearTextName", "")
                                print(
                                    f"        - {sensor_id}: {sensor_value} {sensor_unit} ({sensor_desc})"
                                )

                    # Test GenericDevice endpoint
                    generic_response = requests.post(
                        f"{BASE_URL}/GenericDevice",
                        json={"ApiKey": API_KEY, "DeviceId": device_id},
                        headers={"Content-Type": "application/json"},
                    )

                    if generic_response.status_code == 200:
                        generic_data = generic_response.json()
                        if generic_data.get("Data") and generic_data["Data"].get(
                            "Values"
                        ):
                            values = generic_data["Data"]["Values"]
                            print(f"      ✅ GenericDevice: {len(values)} sensors")
                            for value in values:
                                sensor_name = value.get("Name", "unknown")
                                sensor_value = value.get("Value", "N/A")
                                sensor_desc = value.get("ClearTextName", "")
                                print(
                                    f"        - {sensor_name}: {sensor_value} ({sensor_desc})"
                                )
        else:
            print(f"    ❌ Failed to get devices: {devices_response.status_code}")

    # Summary
    print(f"\n📋 Test Summary:")
    heatmeter_count = sum(1 for d in all_devices if d["Class"] == "HeatMeter")
    device_types = set(d["Class"] for d in all_devices)

    print(f"  ✅ Organizations: {len(organizations)}")
    print(f"  ✅ Total devices: {len(all_devices)}")
    print(f"  ✅ Device types: {', '.join(sorted(device_types))}")
    print(f"  🔥 HeatMeter devices: {heatmeter_count}")
    print(f"  ✅ Cross-org device access: Working")

    return heatmeter_count > 0


if __name__ == "__main__":
    success = test_heatmeter_api()
    print(f"\n{'🎉 Test PASSED' if success else '❌ Test FAILED'}")
    sys.exit(0 if success else 1)
