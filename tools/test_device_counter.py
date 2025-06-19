#!/usr/bin/env python3
"""
Comprehensive test script for Loggamera device counter functionality.

This script tests the device counter sensor to ensure it:
1. Creates properly with correct attributes
2. Shows as available (not "Unavailable")
3. Returns correct device count values
4. Handles edge cases gracefully
5. Integrates properly with Home Assistant
"""

import json
import os
import sys
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

# Add the custom component to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components"))

from loggamera.const import DOMAIN

# Import the sensor module
from loggamera.sensor import LoggameraSensor, SensorStateClass


class TestDeviceCounter:
    """Test suite for device counter functionality."""

    def __init__(self):
        self.test_results = []
        self.mock_hass = Mock()
        self.mock_api = Mock()
        self.mock_api.organization_id = YOUR_ORG_ID_HERE

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(
            {"name": test_name, "passed": passed, "details": details}
        )
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        print()

    def create_mock_coordinator(self, devices_count: int = 1) -> Mock:
        """Create a mock coordinator with test data."""
        coordinator = Mock()

        # Create test devices list
        devices = []
        for i in range(devices_count):
            devices.append(
                {"Id": 12345 + i, "Title": f"Test Device {i+1}", "Class": "PowerMeter"}
            )

        coordinator.data = {"devices": devices, "device_data": {}}

        return coordinator

    def create_device_counter_sensor(self, devices_count: int = 1) -> LoggameraSensor:
        """Create a device counter sensor for testing."""
        coordinator = self.create_mock_coordinator(devices_count)

        # Create the value data as it would be created in the real sensor
        org_value_data = {
            "Name": "device_count",
            "Value": devices_count,  # This should be an integer now
            "UnitType": "Count",
            "UnitPresentation": "",
            "ValueType": "INTEGER",
            "ClearTextName": "Total Device Count",
        }

        # Create the sensor
        sensor = LoggameraSensor(
            coordinator=coordinator,
            api=self.mock_api,
            device_id="organization",
            device_type="Organization",
            device_name="Test Organization",
            value_data=org_value_data,
            hass=self.mock_hass,
            is_organization=True,
        )

        return sensor

    def test_1_sensor_creation_and_initialization(self):
        """Test 1: Validate sensor creation and initialization."""
        try:
            sensor = self.create_device_counter_sensor(1)

            # Check basic properties
            checks = [
                (sensor.sensor_name == "device_count", "Sensor name is 'device_count'"),
                (sensor.is_organization == True, "Is marked as organization sensor"),
                (sensor._attr_name == "Total Device Count", "Display name is correct"),
                (sensor._attr_icon == "mdi:counter", "Icon is set to counter"),
                (
                    sensor._attr_state_class == SensorStateClass.MEASUREMENT,
                    "State class is MEASUREMENT",
                ),
                (
                    sensor._attr_native_unit_of_measurement == "devices",
                    "Unit is 'devices'",
                ),
                (
                    sensor._attr_device_class is None,
                    "Device class is None (correct for counters)",
                ),
            ]

            failed_checks = []
            for check, description in checks:
                if not check:
                    failed_checks.append(description)

            if failed_checks:
                self.log_test(
                    "Test 1: Sensor Creation",
                    False,
                    f"Failed: {', '.join(failed_checks)}",
                )
            else:
                self.log_test(
                    "Test 1: Sensor Creation",
                    True,
                    "All initialization parameters correct",
                )

        except Exception as e:
            self.log_test(
                "Test 1: Sensor Creation", False, f"Exception during creation: {e}"
            )

    def test_2_sensor_availability_logic(self):
        """Test 2: Check sensor availability logic for organization sensors."""
        test_cases = [
            # (devices_count, coordinator_data_override, expected_available, description)
            (1, None, True, "Normal case with 1 device"),
            (5, None, True, "Multiple devices case"),
            (0, None, True, "Zero devices case (should still be available)"),
            (1, {"devices": []}, True, "Empty devices list"),
            (1, {}, False, "Missing devices key"),
            (
                1,
                None,
                False,
                "No coordinator data",
                True,
            ),  # Last param = clear coordinator data
        ]

        for i, test_case in enumerate(test_cases):
            devices_count, data_override, expected, description = test_case[:4]
            clear_data = len(test_case) > 4 and test_case[4]

            try:
                sensor = self.create_device_counter_sensor(devices_count)

                # Override coordinator data if specified
                if data_override is not None:
                    sensor.coordinator.data.update(data_override)
                elif clear_data:
                    sensor.coordinator.data = None

                actual_available = sensor.available

                if actual_available == expected:
                    self.log_test(
                        f"Test 2.{i+1}: Availability - {description}",
                        True,
                        f"Available={actual_available} as expected",
                    )
                else:
                    self.log_test(
                        f"Test 2.{i+1}: Availability - {description}",
                        False,
                        f"Expected available={expected}, got {actual_available}",
                    )

            except Exception as e:
                self.log_test(
                    f"Test 2.{i+1}: Availability - {description}",
                    False,
                    f"Exception: {e}",
                )

    def test_3_native_value_correctness(self):
        """Test 3: Verify native_value returns correct device count."""
        test_cases = [
            (0, "Zero devices"),
            (1, "Single device"),
            (3, "Multiple devices"),
            (10, "Many devices"),
        ]

        for devices_count, description in test_cases:
            try:
                sensor = self.create_device_counter_sensor(devices_count)
                actual_value = sensor.native_value

                # Check that it's the correct value and type
                value_correct = actual_value == devices_count
                type_correct = isinstance(actual_value, int)

                if value_correct and type_correct:
                    self.log_test(
                        f"Test 3: Native Value - {description}",
                        True,
                        f"Returns {actual_value} (int) correctly",
                    )
                else:
                    details = []
                    if not value_correct:
                        details.append(
                            f"Wrong value: expected {devices_count}, got {actual_value}"
                        )
                    if not type_correct:
                        details.append(
                            f"Wrong type: expected int, got {type(actual_value)}"
                        )

                    self.log_test(
                        f"Test 3: Native Value - {description}",
                        False,
                        f"{'; '.join(details)}",
                    )

            except Exception as e:
                self.log_test(
                    f"Test 3: Native Value - {description}", False, f"Exception: {e}"
                )

    def test_4_edge_cases_and_error_handling(self):
        """Test 4: Simulate coordinator data states and edge cases."""
        edge_cases = [
            # (setup_func, expected_available, expected_value, description)
            (
                lambda s: setattr(s.coordinator, "data", None),
                False,
                None,
                "Coordinator data is None",
            ),
            (
                lambda s: setattr(s.coordinator, "data", {}),
                False,
                None,
                "Coordinator data is empty dict",
            ),
            (
                lambda s: s.coordinator.data.pop("devices"),
                False,
                None,
                "Missing devices key",
            ),
            (
                lambda s: setattr(s.coordinator.data, "devices", None),
                True,
                0,
                "Devices is None",
            ),
            (lambda s: None, True, 1, "Normal operation baseline"),
        ]

        for i, (
            setup_func,
            expected_available,
            expected_value,
            description,
        ) in enumerate(edge_cases):
            try:
                sensor = self.create_device_counter_sensor(1)

                # Apply the edge case setup
                if setup_func:
                    setup_func(sensor)

                actual_available = sensor.available
                actual_value = sensor.native_value

                available_ok = actual_available == expected_available
                value_ok = actual_value == expected_value

                if available_ok and value_ok:
                    self.log_test(
                        f"Test 4.{i+1}: Edge Case - {description}",
                        True,
                        f"Available={actual_available}, Value={actual_value}",
                    )
                else:
                    details = []
                    if not available_ok:
                        details.append(
                            f"Available: expected {expected_available}, got {actual_available}"
                        )
                    if not value_ok:
                        details.append(
                            f"Value: expected {expected_value}, got {actual_value}"
                        )

                    self.log_test(
                        f"Test 4.{i+1}: Edge Case - {description}",
                        False,
                        f"{'; '.join(details)}",
                    )

            except Exception as e:
                self.log_test(
                    f"Test 4.{i+1}: Edge Case - {description}", False, f"Exception: {e}"
                )

    def test_5_home_assistant_integration(self):
        """Test 5: Validate sensor attributes and Home Assistant integration."""
        try:
            sensor = self.create_device_counter_sensor(1)

            # Test device_info for organization sensor
            device_info = sensor.device_info

            device_info_checks = [
                (
                    DOMAIN in str(device_info.get("identifiers", [])),
                    "Has correct domain identifier",
                ),
                (
                    "organization" in str(device_info.get("identifiers", [])),
                    "Has organization identifier",
                ),
                (
                    device_info.get("manufacturer") == "Loggamera",
                    "Correct manufacturer",
                ),
                (device_info.get("model") == "Loggamera Organization", "Correct model"),
                (device_info.get("name") == "Test Organization", "Correct device name"),
            ]

            # Test unique_id format
            unique_id = sensor.unique_id
            unique_id_ok = (
                unique_id
                and "loggamera_org_" in unique_id
                and "total_device_count" in unique_id
            )

            # Collect all checks
            all_checks = device_info_checks + [
                (unique_id_ok, f"Unique ID format correct: {unique_id}"),
                (hasattr(sensor, "_attr_state_class"), "Has state class attribute"),
                (
                    hasattr(sensor, "_attr_native_unit_of_measurement"),
                    "Has unit attribute",
                ),
                (hasattr(sensor, "_attr_icon"), "Has icon attribute"),
            ]

            failed_checks = []
            for check, description in all_checks:
                if not check:
                    failed_checks.append(description)

            if failed_checks:
                self.log_test(
                    "Test 5: HA Integration",
                    False,
                    f"Failed: {', '.join(failed_checks[:3])}{'...' if len(failed_checks) > 3 else ''}",
                )
            else:
                self.log_test(
                    "Test 5: HA Integration",
                    True,
                    "All Home Assistant integration attributes correct",
                )

        except Exception as e:
            self.log_test("Test 5: HA Integration", False, f"Exception: {e}")

    def run_all_tests(self):
        """Run all tests and provide summary."""
        print("🧪 Starting Device Counter Comprehensive Tests")
        print("=" * 60)
        print()

        # Run all test methods
        test_methods = [
            self.test_1_sensor_creation_and_initialization,
            self.test_2_sensor_availability_logic,
            self.test_3_native_value_correctness,
            self.test_4_edge_cases_and_error_handling,
            self.test_5_home_assistant_integration,
        ]

        for test_method in test_methods:
            test_method()

        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]

        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print(
            f"📈 SUCCESS RATE: {len(passed_tests)}/{len(self.test_results)} ({100*len(passed_tests)/len(self.test_results):.1f}%)"
        )

        if failed_tests:
            print("\n🔍 FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['name']}: {test['details']}")

        print("\n🎯 CONCLUSION:")
        if len(failed_tests) == 0:
            print("✅ All tests passed! Device counter is working correctly.")
        elif len(failed_tests) <= 2:
            print("⚠️  Minor issues found. Device counter mostly working.")
        else:
            print("❌ Significant issues found. Device counter needs attention.")

        return len(failed_tests) == 0


def main():
    """Run the test suite."""
    tester = TestDeviceCounter()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
