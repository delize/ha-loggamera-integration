#!/usr/bin/env python3
"""
Loggamera API Explorer

A simple utility to explore the Loggamera API and test different endpoints.
This script is useful for debugging integration issues.

Usage:
  python loggamera_api_explorer.py API_KEY ENDPOINT [--device-id DEVICE_ID] [--org-id ORG_ID]

Examples:
  python loggamera_api_explorer.py YOUR_API_KEY Organizations
  python loggamera_api_explorer.py YOUR_API_KEY Devices --org-id 11050
  python loggamera_api_explorer.py YOUR_API_KEY PowerMeter --device-id 73785
  python loggamera_api_explorer.py YOUR_API_KEY RawData --device-id 73785
"""

import requests
import json
import sys
import argparse
from datetime import datetime

# API Configuration
BASE_URL = "https://platform.loggamera.se/api/v2"

def make_api_request(endpoint, api_key, device_id=None, org_id=None, pretty_print=True):
    """Make a request to the API and display the result."""
    url = f"{BASE_URL}/{endpoint}"
    
    # Build data payload
    data = {"ApiKey": api_key}
    
    if device_id:
        data["DeviceId"] = device_id
    
    if org_id:
        data["OrganizationId"] = org_id
    
    print(f"Making request to: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                # Check if pretty print is requested
                if pretty_print:
                    formatted_result = json.dumps(result, indent=2)
                    print(f"Response:\n{formatted_result}")
                else:
                    print(f"Response: {result}")
                    
                return result
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw response: {response.text}")
                return None
        else:
            print(f"HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Run the explorer."""
    parser = argparse.ArgumentParser(description='Loggamera API Explorer')
    parser.add_argument('api_key', help='Your Loggamera API key')
    parser.add_argument('endpoint', help='API endpoint to test (e.g., Organizations, Devices, PowerMeter)')
    parser.add_argument('--device-id', type=int, help='Device ID for device-specific endpoints')
    parser.add_argument('--org-id', type=int, help='Organization ID for organization-specific endpoints')
    parser.add_argument('--raw', action='store_true', help='Display raw response without pretty printing')
    
    args = parser.parse_args()
    
    print(f"Loggamera API Explorer - Testing endpoint: {args.endpoint}")
    print("=" * 50)
    
    make_api_request(args.endpoint, args.api_key, args.device_id, args.org_id, not args.raw)

if __name__ == "__main__":
    main()