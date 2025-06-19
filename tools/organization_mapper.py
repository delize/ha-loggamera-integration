#!/usr/bin/env python3
"""
Comprehensive Organization Mapper for Loggamera API

This tool iterates through all organizations and devices accessible with an API key,
mapping out the complete sensor landscape including IDs, names, variables, measurements,
and endpoint coverage.

Usage:
  python organization_mapper.py API_KEY [--output FILE] [--format json|csv|markdown] [--verbose]

Examples:
  python organization_mapper.py YOUR_API_KEY --output mapping.json
  python organization_mapper.py YOUR_API_KEY --format csv --output sensors.csv
  python organization_mapper.py YOUR_API_KEY --format markdown --verbose
"""

import argparse
import csv
import json
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import certifi
import requests

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"

# All available endpoints to test
ENDPOINTS = [
    "PowerMeter",
    "RoomSensor",
    "WaterMeter",
    "HeatMeter",  # Note: No dedicated endpoint, uses RawData
    "HeatPump",
    "CoolingUnit",
    "RawData",
    "GenericDevice",
    "GetCapabilities",
    "Scenarios",
]


class OrganizationMapper:
    """Maps the complete sensor landscape across all organizations."""

    def __init__(self, api_key: str, verbose: bool = False):
        self.api_key = api_key
        self.verbose = verbose
        self.organizations = []
        self.devices = []
        self.sensors = []
        self.endpoint_coverage = defaultdict(set)
        self.device_type_endpoints = defaultdict(list)
        self.sensor_statistics = defaultdict(int)

    def log(self, message: str, level: str = "info"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "info": "ℹ️ ",
            "success": "✅",
            "warning": "⚠️ ",
            "error": "❌",
            "debug": "🔧",
        }.get(level, "📝")

        if level != "debug" or self.verbose:
            print(f"[{timestamp}] {prefix} {message}")

    def make_api_request(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make an API request with error handling."""
        url = f"{BASE_URL}/{endpoint}"

        if self.verbose:
            self.log(f"Request to {endpoint}: {data}", "debug")

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                timeout=30,
                verify=certifi.where(),
            )

            if response.status_code == 200:
                result = response.json()

                # Check for API-level errors
                if result.get("Message") == "access denied":
                    self.log(f"{endpoint}: Access denied", "warning")
                    return None
                elif result.get("Message") == "invalid endpoint":
                    self.log(f"{endpoint}: Invalid endpoint", "warning")
                    return None
                elif result.get("Error") and result["Error"] != "null":
                    self.log(f"{endpoint}: API error - {result['Error']}", "warning")
                    return None

                return result

            else:
                self.log(f"{endpoint}: HTTP {response.status_code}", "warning")
                return None

        except requests.exceptions.RequestException as e:
            self.log(f"{endpoint}: Request failed - {e}", "error")
            return None

    def discover_organizations(self) -> bool:
        """Discover all accessible organizations."""
        self.log("Discovering organizations...")

        result = self.make_api_request("Organizations", {"ApiKey": self.api_key})

        if not result or "Data" not in result:
            self.log("Failed to get organizations", "error")
            return False

        orgs = result["Data"].get("Organizations", [])

        for org in orgs:
            org_data = {
                "id": org["Id"],
                "name": org["Name"],
                "devices": [],
                "device_count": 0,
                "sensor_count": 0,
                "endpoint_coverage": set(),
            }
            self.organizations.append(org_data)

        self.log(f"Found {len(self.organizations)} organizations", "success")
        return True

    def discover_devices(self) -> bool:
        """Discover all devices across all organizations."""
        self.log("Discovering devices across all organizations...")

        total_devices = 0

        for org in self.organizations:
            self.log(f"Scanning organization: {org['name']} (ID: {org['id']})")

            result = self.make_api_request(
                "Devices", {"ApiKey": self.api_key, "OrganizationId": org["id"]}
            )

            if not result or "Data" not in result:
                self.log(
                    f"Failed to get devices for organization {org['name']}", "warning"
                )
                continue

            devices = result["Data"].get("Devices", [])

            for device in devices:
                device_data = {
                    "id": device["Id"],
                    "name": device.get("Title", f"Unnamed Device {device['Id']}"),
                    "type": device["Class"],
                    "organization_id": org["id"],
                    "organization_name": org["name"],
                    "sensors": [],
                    "endpoints": {},
                    "sensor_count": 0,
                    "mapped_endpoints": [],
                }

                self.devices.append(device_data)
                org["devices"].append(device_data)
                total_devices += 1

            org["device_count"] = len(devices)
            self.log(f"  Found {len(devices)} devices")

        self.log(f"Total devices discovered: {total_devices}", "success")
        return total_devices > 0

    def map_device_sensors(self, device: Dict[str, Any]) -> None:
        """Map all sensors for a specific device across all endpoints."""
        self.log(f"Mapping sensors for {device['name']} ({device['type']})", "debug")

        sensors_found = 0

        for endpoint in ENDPOINTS:
            # Skip HeatMeter endpoint as it doesn't exist
            if endpoint == "HeatMeter":
                continue

            # Special handling for scenarios (organization-level)
            if endpoint == "Scenarios":
                result = self.make_api_request(
                    endpoint,
                    {
                        "ApiKey": self.api_key,
                        "OrganizationId": device["organization_id"],
                    },
                )
            else:
                result = self.make_api_request(
                    endpoint, {"ApiKey": self.api_key, "DeviceId": device["id"]}
                )

            if not result or "Data" not in result:
                device["endpoints"][endpoint] = {"status": "failed", "sensors": []}
                continue

            data = result["Data"]
            endpoint_sensors = []

            # Handle different response formats
            if "Values" in data and data["Values"]:
                # Standard sensor data format
                for value in data["Values"]:
                    sensor = self.extract_sensor_info(value, endpoint, device)
                    endpoint_sensors.append(sensor)
                    self.sensors.append(sensor)
                    sensors_found += 1

            elif "Scenarios" in data and endpoint == "Scenarios":
                # Scenarios format
                for scenario in data["Scenarios"]:
                    sensor = {
                        "id": str(scenario["Id"]),
                        "name": scenario["Name"],
                        "description": scenario.get("Description", ""),
                        "type": "scenario",
                        "value": None,
                        "unit": None,
                        "device_id": device["id"],
                        "device_name": device["name"],
                        "device_type": device["type"],
                        "organization_id": device["organization_id"],
                        "organization_name": device["organization_name"],
                        "endpoint": endpoint,
                        "value_type": "SCENARIO",
                        "clear_text_name": scenario["Name"],
                    }
                    endpoint_sensors.append(sensor)
                    self.sensors.append(sensor)
                    sensors_found += 1

            elif "Capabilities" in data and endpoint == "GetCapabilities":
                # Capabilities format
                for capability in data["Capabilities"]:
                    sensor = {
                        "id": capability.get("Id", "unknown"),
                        "name": capability["Name"],
                        "description": capability.get("Description", ""),
                        "type": "capability",
                        "value": capability.get("Mode", None),
                        "unit": None,
                        "device_id": device["id"],
                        "device_name": device["name"],
                        "device_type": device["type"],
                        "organization_id": device["organization_id"],
                        "organization_name": device["organization_name"],
                        "endpoint": endpoint,
                        "value_type": "CAPABILITY",
                        "clear_text_name": capability["Name"],
                    }
                    endpoint_sensors.append(sensor)
                    self.sensors.append(sensor)
                    sensors_found += 1

            # Record endpoint status
            if endpoint_sensors:
                device["endpoints"][endpoint] = {
                    "status": "success",
                    "sensors": endpoint_sensors,
                    "count": len(endpoint_sensors),
                }
                device["mapped_endpoints"].append(endpoint)
                self.endpoint_coverage[device["type"]].add(endpoint)
                self.device_type_endpoints[device["type"]].append(endpoint)
            else:
                device["endpoints"][endpoint] = {
                    "status": "no_data" if result else "failed",
                    "sensors": [],
                    "count": 0,
                }

        device["sensor_count"] = sensors_found

        # Update organization sensor count
        for org in self.organizations:
            if org["id"] == device["organization_id"]:
                org["sensor_count"] += sensors_found
                org["endpoint_coverage"].update(device["mapped_endpoints"])
                break

    def extract_sensor_info(
        self, value: Dict[str, Any], endpoint: str, device: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract comprehensive sensor information from API response."""
        return {
            "id": str(value.get("Id", value.get("Name", "unknown"))),
            "name": value.get("Name", "unknown"),
            "description": value.get("ClearTextName", value.get("Description", "")),
            "type": "sensor",
            "value": value.get("Value"),
            "unit": value.get("UnitPresentation", value.get("Unit", "")),
            "unit_type": value.get("UnitType", ""),
            "value_type": value.get("ValueType", ""),
            "device_id": device["id"],
            "device_name": device["name"],
            "device_type": device["type"],
            "organization_id": device["organization_id"],
            "organization_name": device["organization_name"],
            "endpoint": endpoint,
            "clear_text_name": value.get("ClearTextName", ""),
            "timestamp": datetime.now().isoformat(),
        }

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive mapping statistics."""
        # Convert endpoint_coverage sets to lists for JSON serialization
        device_type_endpoints = {}
        for device_type, endpoints in self.endpoint_coverage.items():
            device_type_endpoints[device_type] = list(endpoints)

        stats = {
            "summary": {
                "total_organizations": len(self.organizations),
                "total_devices": len(self.devices),
                "total_sensors": len(self.sensors),
                "timestamp": datetime.now().isoformat(),
            },
            "device_types": defaultdict(int),
            "sensor_types": defaultdict(int),
            "endpoint_usage": defaultdict(int),
            "organization_breakdown": [],
            "device_type_endpoints": device_type_endpoints,
            "sensor_name_frequency": defaultdict(int),
        }

        # Device type breakdown
        for device in self.devices:
            stats["device_types"][device["type"]] += 1

        # Sensor analysis
        for sensor in self.sensors:
            stats["sensor_types"][sensor["type"]] += 1
            stats["endpoint_usage"][sensor["endpoint"]] += 1
            stats["sensor_name_frequency"][sensor["name"]] += 1

        # Organization breakdown
        for org in self.organizations:
            stats["organization_breakdown"].append(
                {
                    "id": org["id"],
                    "name": org["name"],
                    "device_count": org["device_count"],
                    "sensor_count": org["sensor_count"],
                    "endpoint_coverage": list(org["endpoint_coverage"]),
                }
            )

        # Convert defaultdicts to regular dicts for JSON serialization
        stats["device_types"] = dict(stats["device_types"])
        stats["sensor_types"] = dict(stats["sensor_types"])
        stats["endpoint_usage"] = dict(stats["endpoint_usage"])
        stats["sensor_name_frequency"] = dict(stats["sensor_name_frequency"])

        return stats

    def run_mapping(self) -> bool:
        """Execute the complete mapping process."""
        self.log("🗺️  Starting comprehensive organization mapping", "info")

        # Step 1: Discover organizations
        if not self.discover_organizations():
            return False

        # Step 2: Discover devices
        if not self.discover_devices():
            return False

        # Step 3: Map sensors for each device
        self.log("Mapping sensors for all devices...")
        for i, device in enumerate(self.devices, 1):
            self.log(f"Progress: {i}/{len(self.devices)} - {device['name']}", "debug")
            self.map_device_sensors(device)

        self.log(
            f"Mapping complete! Found {len(self.sensors)} total sensors", "success"
        )
        return True

    def export_json(self, output_file: str) -> None:
        """Export complete mapping to JSON."""
        # Convert sets to lists for JSON serialization
        organizations_serializable = []
        for org in self.organizations:
            org_copy = org.copy()
            org_copy["endpoint_coverage"] = list(org["endpoint_coverage"])
            organizations_serializable.append(org_copy)

        mapping_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "api_key_prefix": f"{self.api_key[:5]}...{self.api_key[-5:]}",
                "total_organizations": len(self.organizations),
                "total_devices": len(self.devices),
                "total_sensors": len(self.sensors),
            },
            "organizations": organizations_serializable,
            "devices": self.devices,
            "sensors": self.sensors,
            "statistics": self.generate_statistics(),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, indent=2, ensure_ascii=False)

        self.log(f"JSON export saved to {output_file}", "success")

    def export_csv(self, output_file: str) -> None:
        """Export sensor data to CSV."""
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Sensor_ID",
                    "Sensor_Name",
                    "Description",
                    "Type",
                    "Value",
                    "Unit",
                    "Unit_Type",
                    "Value_Type",
                    "Device_ID",
                    "Device_Name",
                    "Device_Type",
                    "Organization_ID",
                    "Organization_Name",
                    "Endpoint",
                    "Clear_Text_Name",
                ]
            )

            # Write sensor data
            for sensor in self.sensors:
                writer.writerow(
                    [
                        sensor["id"],
                        sensor["name"],
                        sensor["description"],
                        sensor["type"],
                        sensor["value"],
                        sensor["unit"],
                        sensor.get("unit_type", ""),
                        sensor.get("value_type", ""),
                        sensor["device_id"],
                        sensor["device_name"],
                        sensor["device_type"],
                        sensor["organization_id"],
                        sensor["organization_name"],
                        sensor["endpoint"],
                        sensor.get("clear_text_name", ""),
                    ]
                )

        self.log(f"CSV export saved to {output_file}", "success")

    def export_markdown(self, output_file: str) -> None:
        """Export mapping to Markdown report."""
        stats = self.generate_statistics()

        md_content = f"""# Loggamera Organization Mapping Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Organizations**: {stats['summary']['total_organizations']}
- **Devices**: {stats['summary']['total_devices']}
- **Sensors**: {stats['summary']['total_sensors']}

## Organizations

"""

        for org in self.organizations:
            md_content += f"""### {org['name']} (ID: {org['id']})

- **Devices**: {org['device_count']}
- **Total Sensors**: {org['sensor_count']}
- **Endpoint Coverage**: {', '.join(sorted(list(org['endpoint_coverage'])))}

#### Devices

"""
            for device in org["devices"]:
                md_content += f"""##### {device['name']} ({device['type']})

- **Device ID**: {device['id']}
- **Sensor Count**: {device['sensor_count']}
- **Active Endpoints**: {', '.join(device['mapped_endpoints'])}

"""

                if device["sensor_count"] > 0:
                    md_content += "**Sensors:**\n\n"
                    for endpoint, endpoint_data in device["endpoints"].items():
                        if (
                            endpoint_data["status"] == "success"
                            and endpoint_data["sensors"]
                        ):
                            md_content += f"*{endpoint} Endpoint:*\n"
                            for sensor in endpoint_data["sensors"]:
                                unit_info = (
                                    f" ({sensor['unit']})" if sensor["unit"] else ""
                                )
                                value_info = (
                                    f" = {sensor['value']}"
                                    if sensor["value"] is not None
                                    else ""
                                )
                                md_content += f"- **{sensor['name']}**: {sensor['description']}{unit_info}{value_info}\n"
                            md_content += "\n"

        md_content += f"""
## Device Type Endpoint Coverage

"""
        for device_type, endpoints in stats["device_type_endpoints"].items():
            md_content += f"- **{device_type}**: {', '.join(sorted(endpoints))}\n"

        md_content += f"""
## Sensor Statistics

### Most Common Sensor Names

"""
        sorted_sensors = sorted(
            stats["sensor_name_frequency"].items(), key=lambda x: x[1], reverse=True
        )[:20]
        for sensor_name, count in sorted_sensors:
            md_content += f"- **{sensor_name}**: {count} instances\n"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        self.log(f"Markdown report saved to {output_file}", "success")


def main():
    """Run the organization mapper."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Loggamera Organization Mapper"
    )
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create mapper instance
    mapper = OrganizationMapper(args.api_key, args.verbose)

    # Run the mapping
    if not mapper.run_mapping():
        print("❌ Mapping failed!")
        sys.exit(1)

    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"loggamera_mapping_{timestamp}.{args.format}"

    # Export results
    if args.format == "json":
        mapper.export_json(args.output)
    elif args.format == "csv":
        mapper.export_csv(args.output)
    elif args.format == "markdown":
        mapper.export_markdown(args.output)

    # Print summary
    stats = mapper.generate_statistics()
    print(f"\n🎉 Mapping Complete!")
    print(
        f"📊 Found {stats['summary']['total_sensors']} sensors across {stats['summary']['total_devices']} devices in {stats['summary']['total_organizations']} organizations"
    )
    print(f"📁 Results saved to: {args.output}")


if __name__ == "__main__":
    main()
