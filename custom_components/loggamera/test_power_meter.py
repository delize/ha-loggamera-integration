#!/usr/bin/env python3
"""
Loggamera PowerMeter Test Script

This script focuses on testing the PowerMeter device type,
which is what your Loggamera account has.

Usage:
  python test_power_meter.py YOUR_API_KEY DEVICE_ID

"""

import requests
import json
import sys
import argparse
import certifi
from datetime import datetime

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"

def make_request(endpoint, data):
    """Make a request to the API."""
    url = f"{BASE_URL}/{endpoint}"
    
    print(f"Making request to {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30,
            verify=certifi.where()
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Response text: {response.text}")
                return None
        else:
            print(f"HTTP error: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as error:
        print(f"Request error: {error}")
        return None

def test_power_meter(api_key, device_id):
    """Test all endpoints that might work with a PowerMeter."""
    print(f"Testing PowerMeter device with ID: {device_id}")
    
    # Test PowerMeter endpoint
    print("\n1. Testing PowerMeter endpoint:")
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    response = make_request("PowerMeter", {
        "ApiKey": api_key,
        "DeviceId": device_id,
        "DateTimeUtc": now
    })
    
    if response and "Data" in response and "Values" in response["Data"]:
        print("SUCCESS! PowerMeter endpoint works.")
        print("Values:")
        for value in response["Data"]["Values"]:
            print(f"  - {value['ClearTextName']}: {value['Value']} {value['UnitPresentation']}")
    else:
        print("PowerMeter endpoint failed, trying RawData instead.")
        
        # Try RawData endpoint
        print("\n2. Testing RawData endpoint:")
        raw_response = make_request("RawData", {
            "ApiKey": api_key,
            "DeviceId": device_id,
            "DateTimeUtc": now
        })
        
        if raw_response and "Data" in raw_response and "Values" in raw_response["Data"]:
            print("SUCCESS! RawData endpoint works.")
            print("Values:")
            for value in raw_response["Data"]["Values"]:
                print(f"  - {value['ClearTextName']}: {value['Value']} {value['UnitPresentation']}")
        else:
            print("RawData endpoint failed too.")
    
    # Test GetCapabilities endpoint
    print("\n3. Testing GetCapabilities endpoint:")
    cap_response = make_request("GetCapabilities", {
        "ApiKey": api_key,
        "DeviceId": device_id
    })
    
    if cap_response and "Data" in cap_response and "Capabilities" in cap_response["Data"]:
        print("SUCCESS! GetCapabilities endpoint works.")
        print("Capabilities:")
        for cap in cap_response["Data"]["Capabilities"]:
            print(f"  - {cap['Name']} ({cap.get('Mode', '')})")
    else:
        print("GetCapabilities endpoint failed.")
    
    # Try GenericDevice endpoint as fallback
    print("\n4. Testing GenericDevice endpoint as fallback:")
    generic_response = make_request("GenericDevice", {
        "ApiKey": api_key,
        "DeviceId": device_id,
        "DateTimeUtc": now
    })
    
    if generic_response and "Data" in generic_response and "Values" in generic_response["Data"]:
        print("SUCCESS! GenericDevice endpoint works.")
        print("Values:")
        for value in generic_response["Data"]["Values"]:
            print(f"  - {value['ClearTextName']}: {value['Value']} {value['UnitPresentation']}")
    else:
        print("GenericDevice endpoint failed.")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test Loggamera PowerMeter')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('device_id', type=int, help='Your PowerMeter device ID')
    
    args = parser.parse_args()
    
    test_power_meter(args.api_key, args.device_id)

if __name__ == '__main__':
    main()