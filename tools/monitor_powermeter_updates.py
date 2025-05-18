#!/usr/bin/env python3
"""
PowerMeter Update Monitor

This script monitors a PowerMeter device for data updates and logs
the update patterns to help determine optimal polling frequencies.

Usage:
  python monitor_powermeter_updates.py --api-key YOUR_API_KEY --device-id DEVICE_ID 
                                       [--interval SECONDS] [--duration HOURS]

Example:
  python monitor_powermeter_updates.py --api-key 05DEE511FE25F65555556JKHH87562 --device-id 9729 --interval 60 --duration 24
"""

import requests
import json
import time
import argparse
import os
from datetime import datetime, timedelta
import logging

# Setup logging
def setup_logging(device_id):
    """Set up logging for the monitor."""
    # Create logs directory if it doesn't exist
    os.makedirs("powermeter_logs", exist_ok=True)
    
    # Create a timestamp for the log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"powermeter_logs/powermeter_device_{device_id}_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Monitoring PowerMeter device {device_id}")
    logging.info(f"Logging to {log_file}")
    
    return log_file

def query_powermeter(api_key, device_id):
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
        response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"HTTP error: {response.status_code}")
            logging.error(response.text)
            return None
    except Exception as e:
        logging.error(f"Error querying API: {e}")
        return None

def monitor_updates(api_key, device_id, interval, duration):
    """Monitor PowerMeter updates for the specified duration."""
    log_file = setup_logging(device_id)
    
    # Calculate end time
    end_time = datetime.now() + timedelta(hours=duration) if duration else None
    
    # Stats
    last_timestamp = None
    poll_count = 0
    update_count = 0
    update_intervals = []
    last_update_time = None
    
    try:
        logging.info(f"Starting monitoring with {interval} second interval")
        logging.info(f"Monitoring will continue for {duration} hours" if duration else "Monitoring will continue until stopped")
        
        while True:
            # Check if we've reached the end time
            if end_time and datetime.now() >= end_time:
                logging.info(f"Reached monitoring duration of {duration} hours")
                break
            
            # Poll the API
            poll_count += 1
            now = datetime.now()
            
            logging.info(f"Poll #{poll_count} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            response = query_powermeter(api_key, device_id)
            
            if response and "Data" in response and "LogDateTimeUtc" in response["Data"]:
                current_timestamp = response["Data"]["LogDateTimeUtc"]
                
                # Get some key values to log
                values = response["Data"].get("Values", [])
                energy = None
                power = None
                
                for value in values:
                    if value.get("Name") == "ConsumedTotalInkWh":
                        energy = f"{value.get('Value')} {value.get('UnitPresentation', '')}"
                    elif value.get("Name") == "PowerInkW":
                        power = f"{value.get('Value')} {value.get('UnitPresentation', '')}"
                
                if last_timestamp is None:
                    # First poll
                    logging.info(f"Initial data timestamp: {current_timestamp}")
                    logging.info(f"Energy: {energy or 'N/A'}, Power: {power or 'N/A'}")
                    last_timestamp = current_timestamp
                    last_update_time = now
                elif current_timestamp != last_timestamp:
                    # Timestamp changed - we have an update
                    update_count += 1
                    
                    # Calculate time since last update
                    update_interval_minutes = (now - last_update_time).total_seconds() / 60
                    update_intervals.append(update_interval_minutes)
                    
                    logging.info(f"UPDATE DETECTED! #{update_count}")
                    logging.info(f"Previous timestamp: {last_timestamp}")
                    logging.info(f"New timestamp: {current_timestamp}")
                    logging.info(f"Time since last update: {update_interval_minutes:.2f} minutes")
                    logging.info(f"Energy: {energy or 'N/A'}, Power: {power or 'N/A'}")
                    
                    last_timestamp = current_timestamp
                    last_update_time = now
                else:
                    # No update
                    time_since_update = (now - last_update_time).total_seconds() / 60
                    logging.info(f"No change in data. Timestamp still {current_timestamp}")
                    logging.info(f"Time since last update: {time_since_update:.2f} minutes")
                    logging.info(f"Energy: {energy or 'N/A'}, Power: {power or 'N/A'}")
            else:
                logging.warning("Failed to get valid response from API")
            
            # Log stats periodically
            if poll_count % 10 == 0:
                logging.info(f"STATS: {update_count} updates in {poll_count} polls ({update_count/poll_count*100:.1f}%)")
                
                if update_intervals:
                    avg_interval = sum(update_intervals) / len(update_intervals)
                    min_interval = min(update_intervals)
                    max_interval = max(update_intervals)
                    
                    logging.info(f"Update intervals (minutes) - Avg: {avg_interval:.2f}, Min: {min_interval:.2f}, Max: {max_interval:.2f}")
                    logging.info(f"Recommended polling interval: {avg_interval/2:.2f} minutes")
            
            # Wait for the next poll
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    
    # Final statistics
    logging.info("\n========= FINAL STATISTICS =========")
    logging.info(f"Total polls: {poll_count}")
    logging.info(f"Total updates: {update_count}")
    logging.info(f"Update percentage: {update_count/poll_count*100:.2f}%")
    
    if update_intervals:
        avg_interval = sum(update_intervals) / len(update_intervals)
        min_interval = min(update_intervals)
        max_interval = max(update_intervals)
        
        logging.info(f"Update intervals (minutes):")
        logging.info(f"  Average: {avg_interval:.2f}")
        logging.info(f"  Minimum: {min_interval:.2f}")
        logging.info(f"  Maximum: {max_interval:.2f}")
        
        # Recommend polling interval (half the average update interval is a good rule of thumb)
        recommended_interval = round(avg_interval / 2)
        logging.info(f"\nRECOMMENDED POLLING INTERVAL: {recommended_interval} minutes ({recommended_interval*60} seconds)")
        
        # More detailed recommendations
        if avg_interval > 25:
            logging.info("NOTE: PowerMeter data appears to update approximately every 30 minutes")
            logging.info("A 15-20 minute polling interval is recommended for balance between timeliness and efficiency")
    
    logging.info(f"\nLog file: {log_file}")
    return log_file

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Monitor PowerMeter updates')
    parser.add_argument('--api-key', required=True, help='Your Loggamera API key')
    parser.add_argument('--device-id', required=True, type=int, help='Device ID to monitor')
    parser.add_argument('--interval', type=int, default=300, help='Polling interval in seconds (default: 300)')
    parser.add_argument('--duration', type=float, help='Monitoring duration in hours (if not provided, runs until stopped)')
    
    args = parser.parse_args()
    
    monitor_updates(args.api_key, args.device_id, args.interval, args.duration)

if __name__ == "__main__":
    main()