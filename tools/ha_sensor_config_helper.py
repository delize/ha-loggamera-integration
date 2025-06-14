#!/usr/bin/env python3
"""
Home Assistant Loggamera Sensor Configuration Helper

This script generates YAML configuration snippets for visualizing Loggamera sensors
in Home Assistant dashboards, energy dashboard, etc.

Usage:
  python ha_sensor_config_helper.py API_KEY DEVICE_ID

Example:
  python ha_sensor_config_helper.py YOUR_API_KEY YOUR_DEVICE_ID
"""

import argparse
import json
import os
import sys
from datetime import datetime

import requests

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"


class HAConfigHelper:
    """Helper for generating Home Assistant configs."""

    def __init__(self, api_key: str, device_id: int):
        """Initialize the helper."""
        self.api_key = api_key
        self.device_id = device_id

        # Get device data
        self.device_info = self.get_device_info()
        if not self.device_info:
            print("❌ Could not get device information")
            sys.exit(1)

        self.device_name = self.device_info.get("Title", f"Device-{device_id}")
        self.device_type = self.device_info.get("Class", "Unknown")

        # Get device data from appropriate endpoint
        self.device_data = self.get_device_data()
        if not self.device_data:
            print("❌ Could not get device data")
            sys.exit(1)

        # Create an output directory
        os.makedirs("ha_configs", exist_ok=True)

        # Create device-specific output file
        self.output_file = f"ha_configs/{self.device_type}_{device_id}_config.yaml"

    def make_request(self, endpoint, data):
        """Make a request to the API."""
        url = f"{BASE_URL}/{endpoint}"
        data["ApiKey"] = self.api_key

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                timeout=30,
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP error: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def get_device_info(self):
        """Get device information."""
        # First try to get organizations
        org_response = self.make_request("Organizations", {})

        if "Data" not in org_response or "Organizations" not in org_response["Data"]:
            print("❌ Failed to fetch organizations")
            return None

        organizations = org_response["Data"]["Organizations"]
        if not organizations:
            print("❌ No organizations found")
            return None

        # Use the first organization or let user select
        if len(organizations) > 1:
            print("Multiple organizations found:")
            for i, org in enumerate(organizations):
                print(f"{i+1}: {org['Name']} (ID: {org['Id']})")
            selection = input("Select organization number: ")
            try:
                org_id = organizations[int(selection) - 1]["Id"]
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                org_id = organizations[0]["Id"]
                print(f"Using first organization: {organizations[0]['Name']}")
        else:
            org_id = organizations[0]["Id"]
            print(f"Using organization: {organizations[0]['Name']}")

        # Get devices
        devices_response = self.make_request("Devices", {"OrganizationId": org_id})

        if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
            print("❌ Failed to fetch devices")
            return None

        devices = devices_response["Data"]["Devices"]

        # Find our device
        for device in devices:
            if device["Id"] == self.device_id:
                return device

        print(f"❌ Device with ID {self.device_id} not found")
        return None

    def get_device_data(self):
        """Get device data from the appropriate endpoint."""
        if self.device_type == "PowerMeter":
            endpoints = ["PowerMeter", "RawData", "GenericDevice"]
        elif self.device_type == "RoomSensor":
            endpoints = ["RoomSensor", "RawData", "GenericDevice"]
        elif self.device_type == "WaterMeter":
            endpoints = ["WaterMeter", "RawData", "GenericDevice"]
        else:
            endpoints = ["RawData", "GenericDevice"]

        for endpoint in endpoints:
            print(f"Trying {endpoint} endpoint...")
            response = self.make_request(endpoint, {"DeviceId": self.device_id})

            if (
                "Data" in response
                and "Values" in response["Data"]
                and response["Data"]["Values"]
            ):
                print(f"✅ Found data in {endpoint} endpoint")
                return response

        return None

    def get_values(self):
        """Get sensor values from device data."""
        if "Data" not in self.device_data or "Values" not in self.device_data["Data"]:
            return []

        return self.device_data["Data"]["Values"]

    def generate_sensor_entity_id(self, name, clear_name):
        """Generate a sensor entity ID from its name."""
        # Start with lowercase, remove special chars, replace spaces with underscores
        if clear_name:
            base = clear_name.lower().replace(" ", "_")
        else:
            base = name.lower()

        # Remove any special characters
        base = "".join(c for c in base if c.isalnum() or c == "_")

        # Add prefix based on device type and device id
        return f"sensor.loggamera_{self.device_type.lower()}_{self.device_id}_{base}"

    def generate_energy_dashboard_config(self):
        """Generate energy dashboard configuration."""
        energy_config = []

        # Only applicable for PowerMeter
        if self.device_type != "PowerMeter":
            return energy_config

        values = self.get_values()

        # Find energy consumption sensor
        energy_consumption = None
        for value in values:
            name = value.get("Name", "")
            clear_name = value.get("ClearTextName", "")

            if (
                name == "ConsumedTotalInkWh"
                or "total förbrukning" in clear_name.lower()
            ):
                energy_consumption = self.generate_sensor_entity_id(name, clear_name)
                break

        if energy_consumption:
            energy_config.append(
                f"""
# Home Assistant Energy Dashboard Configuration
energy:
  # Add this to your configuration.yaml
  energy_sources:
    - type: grid
      flow_from:
        - entity_id: {energy_consumption}
          format: total
          unit_of_measurement: kWh
"""
            )

        return energy_config

    def generate_lovelace_cards(self):
        """Generate Lovelace card configurations."""
        cards = []
        values = self.get_values()

        if self.device_type == "PowerMeter":
            # Find energy and power sensors
            energy_sensor = None
            power_sensor = None

            for value in values:
                name = value.get("Name", "")
                clear_name = value.get("ClearTextName", "")

                if (
                    name == "ConsumedTotalInkWh"
                    or "total förbrukning" in clear_name.lower()
                ):
                    energy_sensor = self.generate_sensor_entity_id(name, clear_name)
                elif name == "PowerInkW" or "effekt" in clear_name.lower():
                    power_sensor = self.generate_sensor_entity_id(name, clear_name)

            # Power card
            if power_sensor:
                cards.append(
                    f"""
# Power Gauge Card
type: gauge
entity: {power_sensor}
min: 0
max: 5
name: Current Power
unit: kW
severity:
  green: 0
  yellow: 2
  red: 4
"""
                )

            # Energy History Card
            if energy_sensor:
                cards.append(
                    f"""
# Energy History Card
type: statistics-graph
entities:
  - entity: {energy_sensor}
    name: Energy Consumption
period: day
"""
                )

            # Energy & Power Glance Card
            if energy_sensor and power_sensor:
                cards.append(
                    f"""
# Energy & Power Glance Card
type: glance
entities:
  - entity: {energy_sensor}
    name: Total Energy
  - entity: {power_sensor}
    name: Current Power
title: {self.device_name} Energy
"""
                )

        # Generic sensor card for all values
        sensor_entities = []
        for value in values:
            name = value.get("Name", "")
            clear_name = value.get("ClearTextName", "")
            entity_id = self.generate_sensor_entity_id(name, clear_name)

            sensor_entities.append(f"  - entity: {entity_id}")

        if sensor_entities:
            entities_str = "\n".join(sensor_entities)
            cards.append(
                f"""
# All Sensors Entity Card
type: entities
entities:
{entities_str}
title: {self.device_name} Sensors
"""
            )

        return cards

    def generate_device_automation(self):
        """Generate device automation examples."""
        automations = []
        values = self.get_values()

        if self.device_type == "PowerMeter":
            # Find power sensor
            power_sensor = None

            for value in values:
                name = value.get("Name", "")
                clear_name = value.get("ClearTextName", "")

                if name == "PowerInkW" or "effekt" in clear_name.lower():
                    power_sensor = self.generate_sensor_entity_id(name, clear_name)

            # High power usage automation
            if power_sensor:
                automations.append(
                    f"""
# High Power Usage Notification
automation:
  - alias: "Notify when power usage is high"
    trigger:
      - platform: numeric_state
        entity_id: {power_sensor}
        above: 3.5
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "High Power Usage Alert"
          message: "Current power usage is {{ {{ states('{power_sensor}') }} }} kW"
"""
                )

        return automations

    def generate_all_configs(self):
        """Generate all configurations and write to file."""
        print(f"Generating configs for {self.device_name} ({self.device_type})...")

        with open(self.output_file, "w") as f:
            f.write(f"# Home Assistant Configuration for {self.device_name}\n")
            f.write(f"# Device Type: {self.device_type}\n")
            f.write(f"# Device ID: {self.device_id}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Energy dashboard config
            energy_configs = self.generate_energy_dashboard_config()
            if energy_configs:
                f.write("# ==== Energy Dashboard Configuration ====\n")
                for config in energy_configs:
                    f.write(config)
                f.write("\n\n")

            # Lovelace cards
            cards = self.generate_lovelace_cards()
            if cards:
                f.write("# ==== Lovelace Dashboard Cards ====\n")
                f.write("# Add these to your Lovelace dashboard\n\n")
                for i, card in enumerate(cards, 1):
                    f.write(f"# --- Card {i} ---\n")
                    f.write(card)
                    f.write("\n\n")

            # Automations
            automations = self.generate_device_automation()
            if automations:
                f.write("# ==== Automation Examples ====\n")
                f.write(
                    "# Add these to your automations.yaml or use the Automation Editor\n\n"
                )
                for i, automation in enumerate(automations, 1):
                    f.write(f"# --- Automation {i} ---\n")
                    f.write(automation)
                    f.write("\n\n")

            # Entity list
            values = self.get_values()
            if values:
                f.write("# ==== Available Entities ====\n")
                for value in values:
                    name = value.get("Name", "")
                    clear_name = value.get("ClearTextName", "")
                    value_type = value.get("ValueType", "")
                    unit_type = value.get("UnitType", "")
                    unit_presentation = value.get("UnitPresentation", "")

                    entity_id = self.generate_sensor_entity_id(name, clear_name)

                    f.write(f"# {clear_name or name}\n")
                    f.write(f"# Entity ID: {entity_id}\n")
                    f.write(f"# Value Type: {value_type}\n")
                    f.write(f"# Unit: {unit_presentation} ({unit_type})\n\n")

        print(f"✅ Configuration written to {self.output_file}")


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(
        description="Home Assistant Loggamera Sensor Configuration Helper"
    )
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument("device_id", type=int, help="Device ID to generate config for")

    args = parser.parse_args()

    helper = HAConfigHelper(args.api_key, args.device_id)
    helper.generate_all_configs()


if __name__ == "__main__":
    main()
