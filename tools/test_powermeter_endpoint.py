#!/usr/bin/env python3
"""
Loggamera PowerMeter Test

This script focuses on testing the PowerMeter device type and provides
information about data update timestamps to help understand the update patterns.

Usage:
  python test_powermeter_endpoint.py API_KEY DEVICE_ID

Example:
  python test_powermeter_endpoint.py 05DEE511FE25F65555556JKHH87562 9729
"""

import requests
import json
import sys
import argparse
import certifi
from datetime import datetime

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"

def check_ssl_info():
    """Check SSL/TLS configuration."""
    print("SSL/TLS Information:")
    print(f"- Certifi version: {certifi.__version__}")
    print(f"- Certifi location: {certifi.where()}")
    
    try:
        import ssl
        print(f"- OpenSSL version: {ssl.OPENSSL_VERSION}")
    except (ImportError, AttributeError):
        print("- OpenSSL version: Unknown")
    
    # Check if requests is using certifi
    print(f"- Requests is using certifi: {requests.certs.where() == certifi.where()}")

def format_response(response):
    """Format the response data for easier readability."""
    formatted = {}
    
    if "Data" not in response:
        return "No Data field in response"
    
    data = response["Data"]
    
    # Extract timestamp
    if "LogDateTimeUtc" in data:
        formatted["timestamp"] = data["LogDateTimeUtc"]
        
        # Parse timestamp to show how old the data is
        try:
            timestamp = datetime.fromisoformat(data["LogDateTimeUtc"].replace('Z', '+00:00'))
            now = datetime.utcnow()
            age = now - timestamp
            formatted["data_age"] = f"{age.total_seconds() / 60:.1f} minutes"
        except (ValueError, AttributeError):
            formatted["data_age"] = "Unknown"
    
    # Extract values
    if "Values" in data:
        values = {}
        for value in data["Values"]:
            name = value.get("ClearTextName", value.get("Name", "Unknown"))
            values[name] = {
                "value": value.get("Value", "N/A"),
                "unit": value.get("UnitPresentation", ""),
                "internal_name": value.get("Name", ""),
                "type": value.get("ValueType", "Unknown"),
            }
        formatted["values"] = values
    
    return formatted

def test_powermeter(api_key, device_id, verbose=False):
    """Test the PowerMeter endpoint."""
    print(f"Testing PowerMeter endpoint for device {device_id}")
    
    # Check SSL information
    check_ssl_info()
    print("\n" + "-" * 50 + "\n")
    
    # Setup payload
    payload = json.dumps({
        "ApiKey": api_key,
        "DeviceId": device_id
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    # First, test the PowerMeter endpoint
    print(f"Testing PowerMeter endpoint...")
    url = f"{BASE_URL}/PowerMeter"
    
    try:
        response = requests.post(url, headers=headers, data=payload, verify=certifi.where())
        
        if response.status_code == 200:
            result = response.json()
            
            if "Message" in result and "access denied" in result["Message"]:
                print(f"❌ Authentication failed: {result['Message']}")
                return
            
            print("✅ PowerMeter endpoint accessible")
            
            # Format and display the response
            formatted = format_response(result)
            
            if isinstance(formatted, str):
                print(f"❌ {formatted}")
            else:
                print("\nPowerMeter Data:")
                if "timestamp" in formatted:
                    print(f"- Timestamp: {formatted['timestamp']}")
                    print(f"- Data age: {formatted['data_age']}")
                
                if "values" in formatted:
                    print("\nValues:")
                    for name, value_data in formatted["values"].items():
                        print(f"- {name}: {value_data['value']} {value_data['unit']}")
                        if verbose:
                            print(f"  Internal name: {value_data['internal_name']}")
                            print(f"  Type: {value_data['type']}")
            
            # If verbose, show the raw response
            if verbose:
                print("\nRaw response:")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Now test the RawData endpoint as fallback
    print(f"Testing RawData endpoint (fallback)...")
    url = f"{BASE_URL}/RawData"
    
    try:
        response = requests.post(url, headers=headers, data=payload, verify=certifi.where())
        
        if response.status_code == 200:
            result = response.json()
            
            if "Message" in result and result["Message"] == "invalid endpoint":
                print("❌ RawData endpoint not available")
            elif "Message" in result and "access denied" in result["Message"]:
                print(f"❌ Authentication failed: {result['Message']}")
            else:
                print("✅ RawData endpoint accessible")
                
                # If verbose, show the raw response
                if verbose:
                    print("\nRaw response:")
                    print(json.dumps(result, indent=2))
                else:
                    # Just show if data is available
                    if "Data" in result and "Values" in result["Data"] and result["Data"]["Values"]:
                        print(f"- Values available: {len(result['Data']['Values'])}")
                    else:
                        print("- No values available")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "-" * 50)
    print("\nUpdate Frequency Analysis:")
    print("The PowerMeter endpoint typically updates data approximately every 30 minutes.")
    print("For detailed update pattern analysis, run:")
    print(f"python monitor_powermeter_updates.py --api-key YOUR_API_KEY --device-id {device_id} --interval 300 --duration 24")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test Loggamera PowerMeter endpoint')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('device_id', help='The device ID to test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    
    test_powermeter(args.api_key, args.device_id, args.verbose)

if __name__ == "__main__":
    main()