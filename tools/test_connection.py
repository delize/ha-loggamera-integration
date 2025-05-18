#!/usr/bin/env python3
"""
Loggamera API Connection Tester

This script tests the connection to the Loggamera API and verifies that
your API key can retrieve organizations and devices.

Usage: python3 test_connection.py YOUR_API_KEY [ORGANIZATION_ID]
"""

import sys
import json
import logging
import requests
import ssl
import certifi
import platform
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("loggamera_test")

# API constants
BASE_URL = "https://platform.loggamera.se/api/v2"
ORGANIZATIONS_ENDPOINT = "Organizations"
DEVICES_ENDPOINT = "Devices"

def log_system_info():
    """Log system and environment information."""
    logger.info("=== System Information ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    logger.info(f"Certifi version: {certifi.__version__}")
    logger.info(f"Certifi path: {certifi.where()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Requests version: {requests.__version__}")
    logger.info(f"API URL: {BASE_URL}")
    logger.info("=========================")

def make_request(endpoint, data):
    """Make a request to the Loggamera API."""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        logger.info(f"Making request to {url}")
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(data),
            timeout=30,
            verify=certifi.where()  # Explicitly use certifi for TLS verification
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Check for API error
                if data.get("Error") is not None and data.get("Error") != "null" and data.get("Error") != "":
                    logger.error(f"API error: {data.get('Error')}")
                    return None
                    
                return data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response text: {response.text}")
                return None
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.SSLError as ssl_error:
        logger.error(f"SSL Error: {ssl_error}")
        
        # Try to determine more specific SSL error details
        error_str = str(ssl_error)
        if "CERTIFICATE_VERIFY_FAILED" in error_str:
            logger.error("Certificate verification failed. This could be due to a missing CA certificate.")
            logger.error(f"Certificate path used: {certifi.where()}")
            logger.error("\nTry running the diagnose_tls.sh script to fix this issue.")
        elif "WRONG_VERSION_NUMBER" in error_str:
            logger.error("Wrong TLS protocol version. The server might not support the TLS version being used.")
            
        return None
    except requests.RequestException as error:
        logger.error(f"Error communicating with Loggamera API: {error}")
        return None

def get_organizations(api_key):
    """Get organization data."""
    data = {"ApiKey": api_key}
    return make_request(ORGANIZATIONS_ENDPOINT, data)

def get_devices(api_key, organization_id=None):
    """Get device data."""
    data = {"ApiKey": api_key}
    if organization_id:
        data["OrganizationId"] = organization_id
    return make_request(DEVICES_ENDPOINT, data)

def main():
    """Main entry point."""
    # Check command-line arguments
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} YOUR_API_KEY [ORGANIZATION_ID]")
        sys.exit(1)
    
    api_key = sys.argv[1]
    organization_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("\n=== Loggamera API Connection Test ===\n")
    
    # Log system information
    log_system_info()
    
    # Test API key with organizations endpoint
    print("\nTesting connection to retrieve organizations...")
    orgs_response = get_organizations(api_key)
    
    if not orgs_response:
        print("❌ Failed to retrieve organizations. Check the logs for details.")
        sys.exit(1)
    
    print("✅ Successfully connected to Loggamera API!")
    
    # Extract organizations
    if "Data" in orgs_response and "Organizations" in orgs_response["Data"]:
        organizations = orgs_response["Data"]["Organizations"]
        print(f"\nFound {len(organizations)} organizations:")
        
        for i, org in enumerate(organizations):
            print(f"  {i+1}. {org.get('Name', 'Unknown')} (ID: {org.get('Id', 'Unknown')})")
        
        # If user didn't provide an organization ID, use the first one
        if not organization_id and organizations:
            organization_id = organizations[0]["Id"]
            print(f"\nUsing organization ID: {organization_id}")
    else:
        print("No organizations found in the response.")
        if not organization_id:
            print("You must specify an organization ID manually.")
            sys.exit(1)
    
    # Test API key with devices endpoint
    print("\nTesting connection to retrieve devices...")
    devices_response = get_devices(api_key, organization_id)
    
    if not devices_response:
        print("❌ Failed to retrieve devices. Check the logs for details.")
        sys.exit(1)
    
    # Extract devices
    if "Data" in devices_response and "Devices" in devices_response["Data"]:
        devices = devices_response["Data"]["Devices"]
        print(f"\n✅ Successfully retrieved {len(devices)} devices:")
        
        for i, device in enumerate(devices):
            device_name = device.get("Name", "Unknown")
            device_id = device.get("Id", "Unknown")
            device_type = device.get("Type", "Unknown")
            print(f"  {i+1}. {device_name} (ID: {device_id}, Type: {device_type})")
    else:
        print("No devices found in the response.")
    
    print("\n=== Connection Test Complete ===")
    print("\nIf you had any issues, check the logs for details.")
    print("You can also try running the diagnose_tls.sh script to diagnose and fix SSL/TLS issues.")

if __name__ == "__main__":
    main()