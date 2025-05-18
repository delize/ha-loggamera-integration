#!/usr/bin/env python3
"""
Loggamera PowerMeter Analyzer

This script analyzes a PowerMeter device to extract all available
data points and presents them in a structured format.

Usage:
  python analyze_power_meter.py API_KEY DEVICE_ID

Example:
  python basic_powermeter_output.py YOUR_API_KEY DEVICE_ID 
"""

import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"

# Known value mappings
VALUE_MAPPINGS = {
    # Common PowerMeter names
    "ConsumedTotalInkWh": {"name": "Total Energy Imported", "unit": "kWh", "category": "Energy"},
    "PowerInkW": {"name": "Total Power", "unit": "kW", "category": "Power"},
    "EnergyPhase1InkWh": {"name": "Energy (Phase 1)", "unit": "kWh", "category": "Energy"},
    "EnergyPhase2InkWh": {"name": "Energy (Phase 2)", "unit": "kWh", "category": "Energy"},
    "EnergyPhase3InkWh": {"name": "Energy (Phase 3)", "unit": "kWh", "category": "Energy"},
    "CurrentPhase1InA": {"name": "Current (Phase 1)", "unit": "A", "category": "Current"},
    "CurrentPhase2InA": {"name": "Current (Phase 2)", "unit": "A", "category": "Current"},
    "CurrentPhase3InA": {"name": "Current (Phase 3)", "unit": "A", "category": "Current"},
    "VoltagePhase1InV": {"name": "Voltage (Phase 1)", "unit": "V", "category": "Voltage"},
    "VoltagePhase2InV": {"name": "Voltage (Phase 2)", "unit": "V", "category": "Voltage"},
    "VoltagePhase3InV": {"name": "Voltage (Phase 3)", "unit": "V", "category": "Voltage"},
    
    # RawData numeric IDs for common values
    "544352": {"name": "Energy Imported", "unit": "kWh", "category": "Energy"},
    "544353": {"name": "Energy Imported Interval", "unit": "kWh", "category": "Energy"},
    "544399": {"name": "Power", "unit": "W", "category": "Power"},
    "544463": {"name": "Energy (Phase 1)", "unit": "kWh", "category": "Energy"},
    "544464": {"name": "Energy (Phase 2)", "unit": "kWh", "category": "Energy"},
    "544465": {"name": "Energy (Phase 3)", "unit": "kWh", "category": "Energy"},
    "544391": {"name": "Current (Phase 1)", "unit": "A", "category": "Current"},
    "544393": {"name": "Current (Phase 2)", "unit": "A", "category": "Current"},
    "544394": {"name": "Current (Phase 3)", "unit": "A", "category": "Current"},
    "544395": {"name": "Voltage (Phase 1)", "unit": "V", "category": "Voltage"},
    "544396": {"name": "Voltage (Phase 2)", "unit": "V", "category": "Voltage"},
    "544397": {"name": "Voltage (Phase 3)", "unit": "V", "category": "Voltage"},
    "549990": {"name": "Exported Energy", "unit": "kWh", "category": "Energy"},
    "550224": {"name": "Exported Energy Interval", "unit": "kWh", "category": "Energy"},
    "550205": {"name": "Power (Phase 1)", "unit": "W", "category": "Power"},
    "550206": {"name": "Power (Phase 2)", "unit": "W", "category": "Power"},
    "550207": {"name": "Power (Phase 3)", "unit": "W", "category": "Power"},
}

class SensorData:
    """Class to represent a sensor data point."""
    
    def __init__(self, name: str, value: Any, unit: str = "", category: str = ""):
        """Initialize the sensor data."""
        self.name = name
        self.value = value
        self.unit = unit
        self.category = category
    
    def __str__(self) -> str:
        """Return a string representation."""
        return f"{self.name}: {self.value} {self.unit}"

def make_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the API."""
    url = f"{BASE_URL}/{endpoint}"
    
    print(f"Making request to {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}

def process_values(values: List[Dict[str, Any]]) -> List[SensorData]:
    """Process the values and return a list of SensorData objects."""
    sensors = []
    
    for value in values:
        name = value.get("Name", "")
        clear_name = value.get("ClearTextName", name)
        raw_value = value.get("Value", "")
        unit_type = value.get("UnitType", "")
        unit_presentation = value.get("UnitPresentation", "")
        
        # Try to determine category and clean name
        category = ""
        clean_name = clear_name
        unit = unit_presentation
        
        # Check if we have a mapping for this value
        if name in VALUE_MAPPINGS:
            mapping = VALUE_MAPPINGS[name]
            clean_name = mapping["name"]
            unit = mapping["unit"]
            category = mapping["category"]
        
        # Try to infer category if not defined
        if not category:
            if "energy" in clear_name.lower() or "kwh" in unit_type.lower():
                category = "Energy"
            elif "power" in clear_name.lower() or "kw" in unit_type.lower() or "watt" in unit_type.lower():
                category = "Power"
            elif "current" in clear_name.lower() or "ampere" in unit_type.lower():
                category = "Current"
            elif "voltage" in clear_name.lower() or "volt" in unit_type.lower():
                category = "Voltage"
            elif "temperature" in clear_name.lower() or "celsius" in unit_type.lower():
                category = "Temperature"
            elif "alarm" in clear_name.lower():
                category = "Alarm"
        
        # Try to convert numeric values
        try:
            if unit_type in ["KwH", "KW", "Watt", "DegreesCelsius", "CubicMeters", "V", "Volt", "A", "Ampere"]:
                processed_value = float(raw_value)
            elif value.get("ValueType") == "BOOLEAN":
                processed_value = raw_value.lower() in ["true", "1", "yes", "on"]
            else:
                processed_value = raw_value
        except (ValueError, TypeError):
            processed_value = raw_value
        
        sensors.append(SensorData(clean_name, processed_value, unit, category))
    
    return sensors

def analyze_power_meter(api_key: str, device_id: int) -> None:
    """Analyze a PowerMeter device."""
    print(f"Analyzing PowerMeter device with ID: {device_id}")
    
    # 1. Get device info
    devices_response = make_request("Devices", {
        "ApiKey": api_key,
        "OrganizationId": None  # Will be filled by API if known
    })
    
    device_info = None
    if "Data" in devices_response and "Devices" in devices_response["Data"]:
        for device in devices_response["Data"]["Devices"]:
            if device.get("Id") == device_id:
                device_info = device
                break
    
    if device_info:
        print("\nDevice Information:")
        print(f"  Name: {device_info.get('Title', 'Unknown')}")
        print(f"  Type: {device_info.get('Class', 'Unknown')}")
        print(f"  Brand: {device_info.get('Brand', 'Unknown')}")
        print(f"  Serial: {device_info.get('Serial', 'Unknown')}")
        print(f"  Alarm State: {'Yes' if device_info.get('IsInAlarmState', False) else 'No'}")
    else:
        print("Device information not found")
    
    # 2. Try to get PowerMeter data
    power_meter_response = make_request("PowerMeter", {
        "ApiKey": api_key,
        "DeviceId": device_id
    })
    
    power_meter_values = []
    if "Data" in power_meter_response and "Values" in power_meter_response["Data"]:
        power_meter_values = power_meter_response["Data"]["Values"]
        print(f"\nPowerMeter endpoint: {len(power_meter_values)} values found")
    else:
        print("\nPowerMeter endpoint: No values found")
    
    # 3. Try to get RawData
    raw_data_response = make_request("RawData", {
        "ApiKey": api_key,
        "DeviceId": device_id
    })
    
    raw_data_values = []
    if "Data" in raw_data_response and "Values" in raw_data_response["Data"]:
        raw_data_values = raw_data_response["Data"]["Values"]
        print(f"RawData endpoint: {len(raw_data_values)} values found")
    else:
        print("RawData endpoint: No values found")
    
    # 4. Process values from both sources
    all_sensors = []
    
    if power_meter_values:
        all_sensors.extend(process_values(power_meter_values))
    
    if raw_data_values:
        all_sensors.extend(process_values(raw_data_values))
    
    # 5. Organize sensors by category
    sensors_by_category = {}
    for sensor in all_sensors:
        category = sensor.category or "Miscellaneous"
        if category not in sensors_by_category:
            sensors_by_category[category] = []
        sensors_by_category[category].append(sensor)
    
    # 6. Display results by category
    print("\nAnalysis Results:")
    print("=" * 50)
    
    total_sensors = 0
    for category, sensors in sorted(sensors_by_category.items()):
        print(f"\n{category}:")
        print("-" * len(category))
        
        # Sort sensors by name within category
        for sensor in sorted(sensors, key=lambda s: s.name):
            print(f"  {sensor}")
            total_sensors += 1
    
    print("\nSummary:")
    print(f"Total sensors found: {total_sensors}")
    print(f"Categories: {', '.join(sorted(sensors_by_category.keys()))}")
    
    # 7. Provide Home Assistant integration recommendations
    print("\nHome Assistant Integration Recommendations:")
    print("=" * 50)
    
    if "Energy" in sensors_by_category:
        print("✅ Energy sensors found - good for energy monitoring")
    else:
        print("❌ No energy sensors found")
    
    if "Power" in sensors_by_category:
        print("✅ Power sensors found - good for real-time consumption monitoring")
    else:
        print("❌ No power sensors found")
    
    if "Current" in sensors_by_category or "Voltage" in sensors_by_category:
        print("✅ Electrical measurement sensors found - good for detailed monitoring")
    else:
        print("❌ No electrical measurement sensors found")
    
    if "Alarm" in sensors_by_category:
        print("✅ Alarm sensors found - will be available as binary sensors")
    else:
        print("❌ No alarm sensors found")
    
    # 8. Provide configuration recommendations
    endpoint_to_use = None
    if len(power_meter_values) > 0:
        endpoint_to_use = "PowerMeter"
    elif len(raw_data_values) > 0:
        endpoint_to_use = "RawData"
    
    if endpoint_to_use:
        print(f"\nRecommended primary endpoint: {endpoint_to_use}")

def main():
    """Run the analyzer."""
    parser = argparse.ArgumentParser(description='Loggamera PowerMeter Analyzer')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('device_id', type=int, help='PowerMeter device ID to analyze')
    
    args = parser.parse_args()
    
    analyze_power_meter(args.api_key, args.device_id)

if __name__ == "__main__":
    main()