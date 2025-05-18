#!/usr/bin/env python3
"""
Basic PowerMeter Output

This script queries the Loggamera PowerMeter endpoint and checks for data updates.
It can be run once or in polling mode to track update frequency.

Usage:
  python basic_powermeter_output.py --api-key YOUR_API_KEY --device-id DEVICE_ID [--poll SECONDS]

Example:
  python basic_powermeter_output.py --api-key YOUR_API_KEY --device-id DEVICE_ID --poll 300
"""

import requests
import json
import sys
import time
import argparse
from datetime import datetime

def query_powermeter(api_key, device_id, verbose=True):
    """Query the PowerMeter endpoint and return the response."""
    url = "https://platform.loggamera.se/api/v2/PowerMeter"

    payload = json.dumps({
        "ApiKey": api_key,
        "DeviceId": device_id,
    })
    
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        if verbose:
            print(f"Querying {url}...")
        
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            if verbose:
                print(f"HTTP error: {response.status_code}")
                print(response.text)
            return None
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return None

def print_response(response, verbose=True):
    """Print the response in a readable format."""
    if not response:
        print("No response data")
        return
    
    if "Data" not in response:
        print("No Data field in response")
        print(json.dumps(response, indent=2))
        return
    
    data = response["Data"]
    
    # Extract timestamp
    timestamp = data.get("LogDateTimeUtc", "Unknown")
    print(f"Log Timestamp: {timestamp}")
    
    # Extract values
    values = data.get("Values", [])
    
    if not values:
        print("No values in response")
        return
    
    print("Values:")
    for value in values:
        name = value.get("Name", "Unknown")
        clear_name = value.get("ClearTextName", name)
        value_type = value.get("ValueType", "Unknown")
        unit = value.get("UnitPresentation", "")
        
        print(f"  {clear_name}: {value.get('Value', 'N/A')} {unit} ({name}, {value_type})")
    
    if verbose:
        print("\nRaw response:")
        print(json.dumps(response, indent=2))

def poll_powermeter(api_key, device_id, interval, count=None):
    """Poll the PowerMeter endpoint at regular intervals."""
    print(f"Polling PowerMeter endpoint every {interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    last_timestamp = None
    updates = 0
    polls = 0
    
    try:
        while True:
            now = datetime.now()
            print(f"\n[{now.strftime('%H:%M:%S')}] Poll #{polls+1}")
            
            response = query_powermeter(api_key, device_id, verbose=False)
            polls += 1
            
            if response and "Data" in response and "LogDateTimeUtc" in response["Data"]:
                current_timestamp = response["Data"]["LogDateTimeUtc"]
                
                if last_timestamp is None:
                    # First poll
                    print(f"Initial timestamp: {current_timestamp}")
                    print_response(response, verbose=False)
                    last_timestamp = current_timestamp
                elif current_timestamp != last_timestamp:
                    # Timestamp changed - we have an update
                    updates += 1
                    print(f"✅ UPDATE DETECTED! ({updates} total)")
                    print(f"Previous: {last_timestamp}")
                    print(f"Current:  {current_timestamp}")
                    print_response(response, verbose=False)
                    last_timestamp = current_timestamp
                else:
                    # No change
                    print(f"No update (timestamp still {current_timestamp})")
                    
                    # Show current power and energy without printing full response
                    values = response["Data"].get("Values", [])
                    energy = None
                    power = None
                    
                    for value in values:
                        if value["Name"] == "ConsumedTotalInkWh":
                            energy = f"{value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}"
                        elif value["Name"] == "PowerInkW":
                            power = f"{value.get('Value', 'N/A')} {value.get('UnitPresentation', '')}"
                    
                    if energy or power:
                        print(f"Energy: {energy or 'N/A'}, Power: {power or 'N/A'}")
            else:
                print("Error or no response")
            
            # Show stats
            if polls > 1:
                print(f"Stats: {updates} updates in {polls} polls ({updates/polls*100:.1f}%)")
                
                if updates > 0:
                    print(f"Average: 1 update per {polls/updates:.1f} polls (approx. {polls/updates*interval/60:.1f} minutes)")
            
            # Check if we've reached our poll count
            if count and polls >= count:
                print(f"\nCompleted {count} polls")
                break
            
            # Sleep for the interval
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nPolling stopped by user")
        print(f"Summary: {updates} updates in {polls} polls over {polls*interval/60:.1f} minutes")
        if updates > 0:
            print(f"Average update frequency: approximately every {polls/updates*interval/60:.1f} minutes")

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Query Loggamera PowerMeter endpoint')
    parser.add_argument('--api-key', required=True, help='Your Loggamera API key')
    parser.add_argument('--device-id', required=True, type=int, help='Device ID to query')
    parser.add_argument('--poll', type=int, help='Poll interval in seconds (if not provided, only polls once)')
    parser.add_argument('--count', type=int, help='Number of polls to perform (if not provided, polls indefinitely)')
    parser.add_argument('--raw', action='store_true', help='Only print raw response')
    
    args = parser.parse_args()
    
    if args.poll:
        poll_powermeter(args.api_key, args.device_id, args.poll, args.count)
    else:
        # Single query
        response = query_powermeter(args.api_key, args.device_id)
        
        if args.raw:
            print(json.dumps(response, indent=2))
        else:
            print_response(response)

if __name__ == "__main__":
    main()
