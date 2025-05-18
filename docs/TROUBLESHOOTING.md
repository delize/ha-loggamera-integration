# Loggamera Integration Troubleshooting

This document provides solutions for common issues that might occur when using the Loggamera integration with Home Assistant.

## Table of Contents

- [SSL/TLS Certificate Issues](#ssltls-certificate-issues)
- [Connection Issues](#connection-issues)
- [Access Denied Errors](#access-denied-errors)
- [Missing Devices/Entities](#missing-devicesentities)
- [Data Update Issues](#data-update-issues)
- [Docker-specific Issues](#docker-specific-issues)

## SSL/TLS Certificate Issues

SSL/TLS certificate issues are common, especially in Docker environments where certificate authorities might not be properly installed.

### Certificate Issue Symptoms

- Error messages containing "CERTIFICATE_VERIFY_FAILED"
- Error messages about SSL/TLS verification
- Integration shows error "Cannot connect" during setup

### Certificate Issue Solutions

#### 1. Run the Diagnostic Script

The integration provides a diagnostic script that can help identify and fix certificate issues:

```bash
docker exec -it homeassistant bash -c "curl -s https://raw.githubusercontent.com/delize/ha-loggamera-integration/main/tools/diagnose_tls.sh | bash"
```

#### 2. Update CA Certificates

In Docker, you may need to update the CA certificates:

```bash
docker exec -it homeassistant bash -c "apt-get update && apt-get install -y ca-certificates"
```

#### 3. Update Certifi

Make sure the Python certifi package is up-to-date:

```bash
docker exec -it homeassistant bash -c "pip install --upgrade certifi"
```

#### 4. Custom CA Bundle

Create a custom CA certificate bundle:

```bash
docker exec -it homeassistant bash -c "mkdir -p /etc/ssl/certs/custom && cp /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/custom/cacert.pem"
```

Then, you'll need to modify the integration's API client to use this custom bundle.

## Connection Issues

If you're having trouble connecting to the Loggamera API:

### Connection Issue Symptoms

- "Cannot connect" errors during integration setup
- Timeout errors in logs

### Connection Issue Solutions

1. **Check Internet Connection**: Ensure your Home Assistant instance has proper internet access.

2. **Check Firewall Settings**: Make sure outbound connections to `platform.loggamera.se` on port 443 are allowed.

3. **DNS Resolution**: Verify that DNS resolution is working correctly.

```bash
docker exec -it homeassistant bash -c "ping platform.loggamera.se"
docker exec -it homeassistant bash -c "nslookup platform.loggamera.se"
```

## Access Denied Errors

If you're seeing "access denied" errors in the logs:

### Access Denied Symptoms

- Log entries with "API error: {'Message': 'access denied'}"
- Integration connects but doesn't show any devices

### Access Denied Solutions

1. **API Key**: Verify your API key is correct and has proper permissions.

2. **Organization ID**: Your API key might be tied to a specific organization. Try specifying the organization ID in the integration configuration.

3. **Check API Key Permissions**: Make sure your API key has access to the devices and data you're trying to access.

4. **API Key Revocation**: If your API key was revoked or expired, you'll need to get a new one.

5. **Reset the Integration**: Try removing and re-adding the integration with a correct API key.

## Missing Devices/Entities

If you've successfully connected but don't see your devices:

### Missing Devices Symptoms

- Integration shows as connected, but no devices/entities appear
- Some devices appear, but others are missing

### Missing Devices Solutions

1. **Wait for Discovery**: Sometimes it can take a few minutes for all devices to be discovered.

2. **Check Device Visibility**: Ensure your devices are visible in the Loggamera platform.

3. **Organization ID**: You might be using the wrong organization. Check if you have access to multiple organizations and specify the correct one.

4. **Restart Home Assistant**: Sometimes a full restart is needed for all entities to appear.

## Data Update Issues

If entities exist but don't update properly:

### Data Update Solutions

1. **Adjust Scan Interval**: Go to the integration options and adjust the scan interval. Default is 60 seconds.

2. **Check API Quotas**: Ensure you haven't exceeded API rate limits.

3. **Device Status**: Verify the devices are active and reporting data to Loggamera.

## Docker-specific Issues

Docker environments can have specific issues related to networking, certificates, and permissions:

### Docker-specific Solutions

1. **Certificate Path**: Docker containers might store certificates in different locations. Use the diagnostic script to identify the correct paths.

2. **Network Mode**: If using host network mode, ensure proper DNS resolution.

3. **Container Rebuilds**: After major Home Assistant updates, you might need to reinstall certificates.

```bash
docker exec -it homeassistant bash -c "apt-get update && apt-get install -y ca-certificates curl"
```

## Still Having Issues?

If you're still experiencing problems after trying these solutions:

1. Check the [GitHub Issues](https://github.com/delize/ha-loggamera-integration/issues) to see if others have reported the same problem.

2. Run the diagnostic script and attach the output when reporting issues.

3. Enable debug logging for the integration by adding this to your configuration.yaml:

```yaml
logger:
  default: warning
  logs:
    custom_components.loggamera: debug
```

Then restart Home Assistant and check the logs for more detailed error messages.
