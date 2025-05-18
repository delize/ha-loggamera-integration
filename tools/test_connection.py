#!/usr/bin/env python3
"""
Test connection to Loggamera API.
This script helps diagnose connection issues with the Loggamera API.
"""

import argparse
import ssl
import sys
import json
import platform
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import socket
import datetime


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)


def print_info(label, value):
    """Print formatted info."""
    print(f"{label.ljust(25)}: {value}")


def check_tls_with_requests(url, api_key):
    """Try to connect using different TLS configurations with requests."""
    print_section("Testing connection with requests")
    
    # Define TLS versions to try
    tls_versions = [
        ("Default", None),
        ("TLS 1.2", ssl.PROTOCOL_TLSv1_2),
    ]
    
    for name, version in tls_versions:
        print(f"\nTrying with {name} TLS settings:")
        try:
            session = requests.Session()
            
            # Create adapter with specific TLS version if provided
            if version:
                class CustomAdapter(HTTPAdapter):
                    def init_poolmanager(self, *args, **kwargs):
                        context = create_urllib3_context()
                        # Set the protocol version
                        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | 
                                           ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)
                
                adapter = CustomAdapter()
                session.mount('https://', adapter)
            
            # Make the request
            data = {"ApiKey": api_key}
            start_time = datetime.datetime.now()
            response = session.post(
                url,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=10
            )
            end_time = datetime.datetime.now()
            
            # Print results
            print(f"  Status code: {response.status_code}")
            print(f"  Response time: {(end_time - start_time).total_seconds():.2f} seconds")
            if response.text:
                try:
                    json_response = response.json()
                    print(f"  Response: {json.dumps(json_response, indent=2)[:200]}...")
                except:
                    print(f"  Response: {response.text[:200]}...")
            
            print(f"  SUCCESS with {name} TLS settings")
            return True
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            print(f"  FAILED with {name} TLS settings")
    
    return False


def check_socket_connection(host, port=443):
    """Check basic socket connection to the host."""
    print_section("Testing basic socket connection")
    
    try:
        start_time = datetime.datetime.now()
        sock = socket.create_connection((host, port), timeout=5)
        end_time = datetime.datetime.now()
        
        print_info("Connection", "SUCCESS")
        print_info("Connection time", f"{(end_time - start_time).total_seconds():.2f} seconds")
        
        # Get socket info
        local_addr, local_port = sock.getsockname()
        print_info("Local address", f"{local_addr}:{local_port}")
        
        remote_addr, remote_port = sock.getpeername()
        print_info("Remote address", f"{remote_addr}:{remote_port}")
        
        sock.close()
        return True
    except Exception as e:
        print_info("Connection", "FAILED")
        print_info("Error", str(e))
        return False


def print_system_info():
    """Print system information."""
    print_section("System Information")
    
    print_info("Python version", sys.version.replace('\n', ' '))
    print_info("Platform", platform.platform())
    print_info("OpenSSL version", ssl.OPENSSL_VERSION)
    print_info("Default TLS version", ssl._DEFAULT_CIPHERS)
    
    # Try to get more SSL info
    context = ssl.create_default_context()
    print_info("SSL verify mode", context.verify_mode)
    print_info("SSL check hostname", context.check_hostname)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test connection to Loggamera API")
    parser.add_argument("api_key", help="Your Loggamera API key")
    parser.add_argument("--url", default="https://platform.loggamera.se/api/v2/Organizations",
                        help="API URL to test (default: %(default)s)")
    args = parser.parse_args()
    
    host = args.url.split("//")[1].split("/")[0]
    print(f"Testing connection to {args.url}")
    print(f"Host: {host}")
    
    # Print system info
    print_system_info()
    
    # Check basic socket connection
    socket_ok = check_socket_connection(host)
    
    # Check TLS connections
    if socket_ok:
        tls_ok = check_tls_with_requests(args.url, args.api_key)
    
    print_section("Results")
    if socket_ok:
        print("✓ Basic socket connection: SUCCESS")
        if tls_ok:
            print("✓ TLS connection: SUCCESS")
            print("\nYour system can successfully connect to the Loggamera API!")
        else:
            print("✗ TLS connection: FAILED")
            print("\nYour system can connect to the server but has TLS issues.")
            print("This might be due to:")
            print("- Outdated SSL/TLS libraries")
            print("- Missing CA certificates")
            print("- Firewall blocking TLS negotiation")
    else:
        print("✗ Basic socket connection: FAILED")
        print("\nYour system cannot connect to the Loggamera server.")
        print("This might be due to:")
        print("- Network connectivity issues")
        print("- Firewall blocking outbound connections")
        print("- DNS resolution problems")


if __name__ == "__main__":
    main()