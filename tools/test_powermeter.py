#!/usr/bin/env python3
"""
Loggamera PowerMeter Test

This script tests different endpoints for a PowerMeter device
to determine which ones are actually available in your setup.
It also reports on data timestamps to understand update frequency.
"""

import requests
import json
import sys
import argparse
from datetime import datetime

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"
ENDPOINTS = [
    "PowerMeter",
    "RawData", 
    "GenericDevice",
    "GetCapabilities",
]

def make_request(endpoint, api_key, device_id):
    """Make a request to the API and return the result."""
    url = f"{BASE_URL}/{endpoint}"
    
    data = {
        "ApiKey": api_key,
        "DeviceId": device_id
    }
    
    print(f"Testing endpoint: {endpoint}")
    print(f"URL: {url}")
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
            result = response.json()
            
            # Check for error messages
            if "Message" in result and result["Message"] == "invalid endpoint":
                print(f"❌ Endpoint not available: {endpoint}")
                return None
            elif "Error" in result and result["Error"] and "Message" in result["Error"] and result["Error"]["Message"] == "invalid endpoint":
                print(f"❌ Endpoint not available: {endpoint}")
                return None
            
            # Check for timestamp in response
            if "Data" in result and "LogDateTimeUtc" in result["Data"]:
                timestamp = result["Data"]["LogDateTimeUtc"]
                print(f"📅 Data timestamp: {timestamp}")
                
                # Try to parse the timestamp to show how old it is
                try:
                    data_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    now = datetime.now().astimezone()
                    age = now - data_dt
                    print(f"⏱️ Data age: {age.total_seconds() / 60:.1f} minutes")
                except Exception as e:
                    print(f"Error parsing timestamp: {e}")
            
            # Check if we have data
            if "Data" in result and result["Data"] is not None:
                if "Values" in result["Data"]:
                    values = result["Data"]["Values"]
                    print(f"✅ Success! Found {len(values)} values:")
                    for value in values:
                        print(f"  • {value.get('ClearTextName', value.get('Name', 'Unknown'))}: {value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}")
                    return values
                elif "ReadCapabilities" in result["Data"] or "WriteCapabilities" in result["Data"]:
                    read_caps = result["Data"].get("ReadCapabilities", [])
                    write_caps = result["Data"].get("WriteCapabilities", [])
                    print(f"✅ Success! Found {len(read_caps)} read capabilities and {len(write_caps)} write capabilities")
                    return {"ReadCapabilities": read_caps, "WriteCapabilities": write_caps}
                else:
                    print("✅ Success! Response has data but no values or capabilities")
                    return result["Data"]
            else:
                print("❌ No data in response")
                print(f"Full response: {json.dumps(result, indent=2)}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_organizations(api_key):
    """Test the Organizations endpoint."""
    print("\n=== Testing Organizations ===")
    url = f"{BASE_URL}/Organizations"
    
    data = {"ApiKey": api_key}
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "Data" in result and "Organizations" in result["Data"]:
                organizations = result["Data"]["Organizations"]
                print(f"✅ Success! Found {len(organizations)} organizations:")
                for org in organizations:
                    print(f"  • {org['Name']} (ID: {org['Id']})")
                return organizations
            else:
                print("❌ No organizations found")
                return []
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_devices(api_key, org_id):
    """Test the Devices endpoint."""
    print("\n=== Testing Devices ===")
    url = f"{BASE_URL}/Devices"
    
    data = {"ApiKey": api_key, "OrganizationId": org_id}
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "Data" in result and "Devices" in result["Data"]:
                devices = result["Data"]["Devices"]
                print(f"✅ Success! Found {len(devices)} devices:")
                for device in devices:
                    print(f"  • {device.get('Title', 'Unnamed')} (ID: {device['Id']}, Type: {device['Class']})")
                return devices
            else:
                print("❌ No devices found")
                return []
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test Loggamera PowerMeter')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('--device-id', type=int, help='Device ID to test')
    parser.add_argument('--org-id', type=int, help='Organization ID to test')
    parser.add_argument('--monitor', action='store_true', help='Monitor for updates (checks every 5 minutes)')
    
    args = parser.parse_args()
    
    # First get organizations
    organizations = test_organizations(args.api_key)
    
    if not organizations and not args.org_id:
        print("Cannot continue without organization information")
        return
    
    # Use provided org ID or the first one found
    org_id = args.org_id or organizations[0]["Id"]
    
    # Get devices if no device ID provided
    if not args.device_id:
        devices = test_devices(args.api_key, org_id)
        
        if not devices:
            print("Cannot continue without device information")
            return
        
        # Filter to only PowerMeter devices
        power_meters = [d for d in devices if d["Class"] == "PowerMeter"]
        
        if not power_meters:
            print("No PowerMeter devices found")
            return
        
        device_id = power_meters[0]["Id"]
        print(f"\nUsing PowerMeter device ID: {device_id}")
    else:
        device_id = args.device_id
    
    # Test all endpoints
    print("\n=== Testing PowerMeter Endpoints ===")
    results = {}
    timestamps = {}
    
    for endpoint in ENDPOINTS:
        print(f"\n--- Testing {endpoint} ---")
        result = make_request(endpoint, args.api_key, device_id)
        results[endpoint] = result is not None
        
        # Store timestamp for later comparison
        if result and endpoint in ["PowerMeter", "RawData", "GenericDevice"]:
            # Get the response again to access the full structure
            url = f"{BASE_URL}/{endpoint}"
            data = {
                "ApiKey": args.api_key,
                "DeviceId": device_id
            }
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                timeout=30
            ).json()
            
            if "Data" in response and "LogDateTimeUtc" in response["Data"]:
                timestamps[endpoint] = response["Data"]["LogDateTimeUtc"]
    
    # Print summary
    print("\n=== Endpoint Availability Summary ===")
    for endpoint, available in results.items():
        print(f"{endpoint}: {'✅ Available' if available else '❌ Not Available'}")
    
    # Print timestamp comparison
    if timestamps:
        print("\n=== Timestamp Comparison ===")
        for endpoint, timestamp in timestamps.items():
            print(f"{endpoint}: {timestamp}")
        
        # Check if timestamps are the same across endpoints
        if len(set(timestamps.values())) == 1:
            print("✅ All endpoints report the same timestamp")
        else:
            print("⚠️ Endpoints report different timestamps")
    
    print("\nRecommendation for Home Assistant integration:")
    if results["PowerMeter"]:
        print("✅ Use PowerMeter endpoint for best results")
    elif results["RawData"]:
        print("✅ Use RawData endpoint as PowerMeter isn't available")
    elif results["GenericDevice"]:
        print("✅ Use GenericDevice endpoint as fallback")
    else:
        print("❌ No suitable endpoints available for data retrieval")
    
    # Print update frequency information
    print("\n=== Update Frequency Information ===")
    print("PowerMeter data typically updates approximately every 30 minutes")
    print("For best results, set the scan interval to 20 minutes (1200 seconds)")
    
    # If monitor mode is enabled
    if args.monitor:
        import time
        print("\n=== Starting Monitor Mode ===")
        print("Press Ctrl+C to exit")
        print("Checking for updates every 5 minutes...")
        
        last_timestamps = timestamps.copy()
        check_count = 0
        
        try:
            while True:
                check_count += 1
                time.sleep(300)  # 5 minutes
                
                print(f"\n=== Check #{check_count} at {datetime.now().strftime('%H:%M:%S')} ===")
                
                for endpoint in ["PowerMeter", "RawData"]:
                    if not results[endpoint]:
                        continue
                    
                    print(f"Checking {endpoint}...")
                    url = f"{BASE_URL}/{endpoint}"
                    data = {
                        "ApiKey": args.api_key,
                        "DeviceId": device_id
                    }
                    
                    try:
                        response = requests.post(
                            url, 
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(data),
                            timeout=30
                        ).json()
                        
                        if "Data" in response and "LogDateTimeUtc" in response["Data"]:
                            current_timestamp = response["Data"]["LogDateTimeUtc"]
                            if endpoint in last_timestamps:
                                if current_timestamp != last_timestamps[endpoint]:
                                    print(f"✅ UPDATE DETECTED for {endpoint}!")
                                    print(f"  Old: {last_timestamps[endpoint]}")
                                    print(f"  New: {current_timestamp}")
                                    last_timestamps[endpoint] = current_timestamp
                                else:
                                    print(f"⏳ No update for {endpoint}")
                            else:
                                print(f"📊 Initial timestamp for {endpoint}: {current_timestamp}")
                                last_timestamps[endpoint] = current_timestamp
                    except Exception as e:
                        print(f"Error checking {endpoint}: {e}")
        except KeyboardInterrupt:
            print("\nMonitor mode stopped")

if __name__ == "__main__":
    main()