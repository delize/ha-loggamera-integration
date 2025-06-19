#!/usr/bin/env python3
"""Test script to verify HeatMeter support and organization hierarchy functionality."""

import asyncio
import logging
import sys
from datetime import timedelta

from custom_components.loggamera.__init__ import LoggameraDataUpdateCoordinator
from custom_components.loggamera.api import LoggameraAPI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

API_KEY = "YOUR_API_KEY_HERE"
ORG_ID = YOUR_ORG_ID_HERE  # Parent organization


class MockHass:
    """Mock Home Assistant object for testing."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    async def async_add_executor_job(self, func, *args, **kwargs):
        """Mock executor job - just run the function."""
        return func(*args, **kwargs)


async def test_heatmeter_support():
    """Test HeatMeter device support and organization hierarchy."""
    print("🔧 Testing HeatMeter Support and Organization Hierarchy")
    print("=" * 60)

    # Initialize API and coordinator
    api = LoggameraAPI(api_key=API_KEY, organization_id=ORG_ID)
    mock_hass = MockHass()

    coordinator = LoggameraDataUpdateCoordinator(
        hass=mock_hass,
        api=api,
        name="Test Coordinator",
        update_interval=timedelta(seconds=300),
    )

    try:
        # Fetch data
        print("📡 Fetching data from API...")
        data = await coordinator._async_update_data()

        # Test organization hierarchy
        print("\n🏢 Organization Hierarchy:")
        if "organizations" in data:
            for org in data["organizations"]:
                parent_info = (
                    f" (Parent: {org['ParentId']})"
                    if org["ParentId"] != 0
                    else " (Root)"
                )
                print(f"  - {org['Id']}: {org['Name']}{parent_info}")

        if "organization_hierarchy" in data:
            print("\n📊 Hierarchy Structure:")
            for org_id, org_info in data["organization_hierarchy"].items():
                children_info = (
                    f" -> {len(org_info['children'])} children"
                    if org_info["children"]
                    else ""
                )
                print(f"  - {org_id}: {org_info['name']}{children_info}")

        # Test devices from all organizations
        print(f"\n🔌 Devices Found ({len(data.get('devices', []))} total):")
        heatmeter_found = False

        for device in data.get("devices", []):
            device_id = device["Id"]
            device_type = device["Class"]
            device_name = device["Title"]
            org_source = device.get("_source_organization_name", "current org")

            print(
                f"  - {device_name} (ID: {device_id}, Type: {device_type}) from {org_source}"
            )

            if device_type == "HeatMeter":
                heatmeter_found = True
                print(f"    ✅ HeatMeter found! Testing sensor data...")

                # Test HeatMeter device data
                device_data = data.get("device_data", {}).get(str(device_id))
                if device_data and "Data" in device_data and device_data["Data"]:
                    values = device_data["Data"].get("Values", [])
                    print(f"    📊 Found {len(values)} sensor values:")
                    for value in values:
                        sensor_name = value.get("Name", "unknown")
                        sensor_value = value.get("Value", "N/A")
                        sensor_unit = value.get("UnitPresentation", "")
                        sensor_description = value.get("ClearTextName", "")
                        print(
                            f"      - {sensor_name}: {sensor_value} {sensor_unit} ({sensor_description})"
                        )

                # Test RawData for HeatMeter
                raw_data_key = f"rawdata_{device_id}"
                raw_data = data.get("device_data", {}).get(raw_data_key)
                if raw_data and "Data" in raw_data:
                    raw_values = raw_data["Data"].get("Values", [])
                    print(f"    🔍 Found {len(raw_values)} RawData values:")
                    for value in raw_values:
                        sensor_name = value.get("Name", "unknown")
                        sensor_value = value.get("Value", "N/A")
                        sensor_unit = value.get("UnitPresentation", "")
                        sensor_description = value.get("ClearTextName", "")
                        print(
                            f"      - {sensor_name}: {sensor_value} {sensor_unit} ({sensor_description})"
                        )

        # Summary
        print(f"\n📋 Test Summary:")
        print(f"  ✅ Organizations: {len(data.get('organizations', []))}")
        print(f"  ✅ Devices: {len(data.get('devices', []))}")
        print(
            f"  {'✅' if heatmeter_found else '❌'} HeatMeter support: {'Found' if heatmeter_found else 'Not found'}"
        )
        print(
            f"  ✅ Organization hierarchy: {'Working' if data.get('organization_hierarchy') else 'Missing'}"
        )

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_heatmeter_support())
    sys.exit(0 if success else 1)
