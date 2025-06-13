#!/usr/bin/env python3
"""
Loggamera PowerMeter Endpoint Test

This script tests the PowerMeter endpoint to determine if it works
with your specific API key and device ID.

Usage:
  python test_powermeter_endpoint.py API_KEY DEVICE_ID

Example:
  python test_powermeter_endpoint.py YOUR_API_KEY YOUR_DEVICE_ID
"""

import requests
import json
import sys
import argparse

def test_power_meter(api_key, device_id):
    """Test the PowerMeter endpoint."""
    print(f"Testing PowerMeter device with ID: {device_id}")
    
    # 1. Test PowerMeter endpoint
    print("\n1. Testing PowerMeter endpoint:")
    pm_url = "https://platform.loggamera.se/api/v2/PowerMeter"
    pm_data = {
        "ApiKey": api_key,
        "DeviceId": device_id
    }
    
    print(f"Making request to {pm_url}")
    print(f"Request data: {json.dumps(pm_data, indent=2)}")
    
    try:
        response = requests.post(
            pm_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(pm_data),
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response = response.json()
            
            # Check for error messages
            if "Message" in response and response["Message"] == "invalid endpoint":
                print("❌ PowerMeter endpoint not available")
                response = None
            elif "Error" in response and response["Error"] and response["Error"].get("Message") == "invalid endpoint":
                print("❌ PowerMeter endpoint not available")
                response = None
            
            # Check if we have data
            if response and "Data" in response and "Values" in response["Data"]:
                values = response["Data"]["Values"]
                print(f"✅ Success! Found {len(values)} values in PowerMeter endpoint:")
                for value in values:
                    print(f"  • {value.get('ClearTextName', value.get('Name', 'Unknown'))}: {value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}")
                return response
            else:
                print("❌ No data in PowerMeter response")
                if response:
                    print(f"Response: {json.dumps(response, indent=2)}")
                response = None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            try:
                print(f"Response: {response.text}")
            except:
                pass
            response = None
    except Exception as e:
        print(f"❌ Error: {e}")
        response = None
    
    # 2. If PowerMeter endpoint fails, try RawData
    if not response:
        print("\n2. Testing RawData endpoint:")
        raw_url = "https://platform.loggamera.se/api/v2/RawData"
        raw_data = {
            "ApiKey": api_key,
            "DeviceId": device_id
        }
        
        print(f"Making request to {raw_url}")
        print(f"Request data: {json.dumps(raw_data, indent=2)}")
        
        try:
            response = requests.post(
                raw_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(raw_data),
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                response = response.json()
                
                # Check for error messages
                if "Message" in response and response["Message"] == "invalid endpoint":
                    print("❌ RawData endpoint not available")
                    response = None
                elif "Error" in response and response["Error"] and response["Error"].get("Message") == "invalid endpoint":
                    print("❌ RawData endpoint not available")
                    response = None
                
                # Check if we have data
                if response and "Data" in response and "Values" in response["Data"]:
                    values = response["Data"]["Values"]
                    print(f"✅ Success! Found {len(values)} values in RawData endpoint:")
                    for value in values:
                        print(f"  • {value.get('ClearTextName', value.get('Name', 'Unknown'))}: {value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}")
                    
                    # Check if we can find power value
                    power_value = next((v for v in values if v.get("ClearTextName") == "Power"), None)
                    if power_value:
                        print(f"\nPower value found: {power_value.get('Value', 'N/A')} {power_value.get('UnitPresentation', '')}")
                    
                    # Check if we can find energy value
                    energy_value = next((v for v in values if v.get("ClearTextName") == "Energy imported "), None)
                    if energy_value:
                        print(f"Energy value found: {energy_value.get('Value', 'N/A')} {energy_value.get('UnitPresentation', '')}")
                    
                    return response
                else:
                    print("❌ No data in RawData response")
                    if response:
                        print(f"Response: {json.dumps(response, indent=2)}")
                    response = None
            else:
                print(f"❌ HTTP error: {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                response = None
        except Exception as e:
            print(f"❌ Error: {e}")
            response = None
    
    # 3. If RawData endpoint fails, try GenericDevice
    if not response:
        print("\n3. Testing GenericDevice endpoint:")
        generic_url = "https://platform.loggamera.se/api/v2/GenericDevice"
        generic_data = {
            "ApiKey": api_key,
            "DeviceId": device_id
        }
        
        print(f"Making request to {generic_url}")
        print(f"Request data: {json.dumps(generic_data, indent=2)}")
        
        try:
            response = requests.post(
                generic_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(generic_data),
                timeout=30
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                response = response.json()
                
                # Check for error messages
                if "Message" in response and response["Message"] == "invalid endpoint":
                    print("❌ GenericDevice endpoint not available")
                    response = None
                elif "Error" in response and response["Error"] and response["Error"].get("Message") == "invalid endpoint":
                    print("❌ GenericDevice endpoint not available")
                    response = None
                
                # Check if we have data
                if response and "Data" in response and "Values" in response["Data"]:
                    values = response["Data"]["Values"]
                    print(f"✅ Success! Found {len(values)} values in GenericDevice endpoint:")
                    for value in values:
                        print(f"  • {value.get('ClearTextName', value.get('Name', 'Unknown'))}: {value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}")
                    return response
                else:
                    print("❌ No data in GenericDevice response")
                    if response:
                        print(f"Response: {json.dumps(response, indent=2)}")
                    response = None
            else:
                print(f"❌ HTTP error: {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                response = None
        except Exception as e:
            print(f"❌ Error: {e}")
            response = None
    
    # If all endpoints failed
    if not response:
        print("\n❌ All endpoints failed. Device data is not accessible.")
        return None

    return response

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test Loggamera PowerMeter Endpoint')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('device_id', type=int, help='Your PowerMeter device ID')
    
    args = parser.parse_args()
    
    test_power_meter(args.api_key, args.device_id)

if __name__ == "__main__":
    main()