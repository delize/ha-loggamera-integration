# Troubleshooting Guide for Loggamera Integration

This guide helps resolve common issues with the Loggamera Home Assistant integration.

## SSL/TLS Connection Issues

The most common problems are related to SSL/TLS connections to the Loggamera API server.

### TLSv1 Alert Internal Error

**Error message:**

```text
Error communicating with Loggamera API: HTTPSConnectionPool(host='platform.loggamera.se', port=443): Max retries exceeded with url: /Api/v2/Organizations (Caused by SSLError(SSLError(1, '[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error (_ssl.c:1028)')))
```

**Possible solutions:**

1. **Test connection using the provided script:**

   ```bash
   cd tools
   python test_connection.py YOUR_API_KEY
   ```

2. **Check TLS compatibility:**
   The Loggamera API might require a specific version of TLS. You can test which versions work using OpenSSL:

   ```bash
   openssl s_client -connect platform.loggamera.se:443 -tls1_2
   ```

3. **Ensure Home Assistant has up-to-date CA certificates:**
   - If running in Docker, make sure your container has current CA certificates
   - If running on a Linux system: `sudo apt-get update && sudo apt-get install ca-certificates`

4. **Network issues:**
   - Check if your network firewall is blocking the connection
   - Try from a different network if possible

## API Key Issues

If you're getting authentication errors:

1. **Verify your API key:**
   - Make sure you've copied the entire API key correctly
   - Check for trailing spaces or line breaks

2. **API key permissions:**
   - Your API key must have the right permissions for the organizations you want to access
   - Check in the Loggamera platform if your API key has the correct access level

## General Connectivity Issues

1. **Network connectivity:**
   - Check if you can access `https://platform.loggamera.se` from the device running Home Assistant
   - Verify that outbound connections to port 443 are allowed

2. **DNS issues:**
   - Try adding this line to your hosts file: `platform.loggamera.se IP_ADDRESS`
   - Replace IP_ADDRESS with the actual IP of the server (you can find it using: `nslookup platform.loggamera.se`)

## No Devices Showing

If you've connected successfully but don't see any devices:

1. **Check organization ID:**
   - The integration will try to discover all devices visible to your API key
   - If you have multiple organizations, it might not be finding the right one
   - Try setting organization_id manually in configuration.yaml if needed

2. **API limitations:**
   - Check if there are any limitations on your API key in the Loggamera platform

## Logs and Diagnostics

To enable debug logging for the integration:

1. Add this to your configuration.yaml:

   ```yaml
   logger:
     default: warning
     logs:
       custom_components.loggamera: debug
   ```

2. Restart Home Assistant

3. Check the logs for detailed error messages:
   - Home Assistant web interface: Developer Tools > Logs
   - Or in your HA log file location

## Contact Support

If none of these solutions work, collect the following information:

1. Debug logs from Home Assistant
2. Output from the test_connection.py script
3. Information about your Home Assistant installation (version, how it's installed)

Then:

1. Open an issue on our GitHub repository
2. Or contact Loggamera support at [support@loggamera.se](mailto:support@loggamera.se)
