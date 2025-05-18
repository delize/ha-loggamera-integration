"""
INSECURE API client for Loggamera.

WARNING: This is an INSECURE version of the API client that disables SSL verification.
DO NOT use this in production - it is provided ONLY for troubleshooting SSL issues.

When used, this client bypasses certificate verification, which makes your connection
vulnerable to man-in-the-middle attacks.
"""

import logging
import requests
import json
import sys
import platform
import ssl
import warnings
from datetime import datetime

# Suppress InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger("loggamera_insecure")

class LoggameraInsecureAPI:
    """INSECURE API client for Loggamera."""
    
    def __init__(self, api_key):
        """Initialize the INSECURE API client."""
        self.api_key = api_key
        self.base_url = "https://platform.loggamera.se/api/v2"
        
        # Display a very prominent security warning
        print("\n")
        print("!"*80)
        print("! WARNING: USING INSECURE API CLIENT WITH SSL VERIFICATION DISABLED")
        print("! This is highly insecure and should ONLY be used for troubleshooting")
        print("! DO NOT use this in production!")
        print("!"*80)
        print("\n")
        
        _LOGGER.warning("Initializing INSECURE API client with SSL verification disabled")
        
        # Create a session with SSL verification disabled
        self.session = requests.Session()
        self.session.verify = False
        
        # Log system info
        self._log_system_info()
    
    def _log_system_info(self):
        """Log system information."""
        _LOGGER.info(f"Python version: {sys.version}")
        _LOGGER.info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
        _LOGGER.info(f"Platform: {platform.platform()}")
        _LOGGER.info(f"Base URL: {self.base_url}")
    
    def get_organizations(self):
        """Get organizations (insecurely)."""
        url = f"{self.base_url}/Organizations"
        data = {"ApiKey": self.api_key}
        
        _LOGGER.info(f"Making insecure request to {url}")
        
        try:
            response = self.session.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(data),
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                _LOGGER.error(f"Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.Timeout:
            _LOGGER.error("Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Request failed: {str(e)}")
            return None

def main():
    """Test the insecure API client."""
    if len(sys.argv) < 2:
        print("Usage: python api_client_insecure.py YOUR_API_KEY")
        sys.exit(1)
    
    api_key = sys.argv[1]
    client = LoggameraInsecureAPI(api_key)
    
    print("\nTesting insecure connection to get organizations...")
    result = client.get_organizations()
    
    if result:
        print("\nConnection successful!")
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        print("\nIMPORTANT: This connection was made insecurely. Do not use in production!")
    else:
        print("\nConnection failed. See logs for details.")

if __name__ == "__main__":
    main()