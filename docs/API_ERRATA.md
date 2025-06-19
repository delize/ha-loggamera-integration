# Loggamera API Errata

> **Version**: Platform API v2
> **Document Updated**: 2025-01-18
> **Integration Version**: 0.7.3+

This document catalogs known discrepancies, inconsistencies, and undocumented behaviors in the Loggamera Platform API v2 that differ from expected or documented behavior.

---

## Table of Contents

1. [Spelling and Naming Errors](#spelling-and-naming-errors)
2. [Missing API Endpoints](#missing-api-endpoints)
3. [Response Format Inconsistencies](#response-format-inconsistencies)
4. [Authentication Issues](#authentication-issues)
5. [Endpoint Availability Problems](#endpoint-availability-problems)
6. [Data Type and Value Inconsistencies](#data-type-and-value-inconsistencies)
7. [SSL/TLS Certificate Issues](#ssltls-certificate-issues)
8. [Update Frequency Limitations](#update-frequency-limitations)
9. [Organization Access Patterns](#organization-access-patterns)
10. [Error Handling Inconsistencies](#error-handling-inconsistencies)

---

## Spelling and Naming Errors

### 1. "Voltate" Instead of "Voltage"

**Issue**: API consistently returns misspelled "Voltate" in sensor names.

**Affected Endpoints**: RawData
**Device Types**: ChargingStation
**Sensor IDs**: 544426, 544427, 544428

**API Response**:
```json
{
  "ClearTextName": "Voltate (Phase 1)",
  "Name": "544426"
}
```

**Expected**: "Voltage (Phase 1)"

**Workaround**: Integration corrects spelling in sensor display names.

**Files**: `custom_components/loggamera/sensor.py:240-252`

---

### 2. "Signal-Noice" Instead of "Signal-Noise"

**Issue**: API returns "Signal-Noice relation (Snr)" instead of "Signal-Noise ratio (SNR)".

**Affected Endpoints**: RawData
**Sensor ID**: 543837

**API Response**:
```json
{
  "ClearTextName": "Signal-Noice relation (Snr)",
  "Name": "543837"
}
```

**Expected**: "Signal-Noise ratio (SNR)"

**Workaround**: Integration corrects terminology in sensor display names.

**Files**: `custom_components/loggamera/sensor.py:336`

---

## Missing API Endpoints

### 1. HeatMeter Endpoint Does Not Exist

**Issue**: Despite HeatMeter being a supported device type, there is no dedicated `/HeatMeter` endpoint.

**Impact**: HeatMeter devices must rely on generic endpoints (RawData, GenericDevice) for data retrieval.

**Expected**: `POST /api/v2/HeatMeter` endpoint similar to PowerMeter, WaterMeter, etc.

**Actual**: Endpoint returns "invalid endpoint" error.

**Workaround**:
- Primary data source: `/RawData` endpoint
- Fallback for alarms: `/GenericDevice` endpoint
- Special sensor mapping for HeatMeter RawData IDs (544310-544324)

**Files**: `custom_components/loggamera/api.py:244-247`

---

## Response Format Inconsistencies

### 1. Empty Response Bodies

**Issue**: Some endpoints return HTTP 200 with completely empty response bodies.

**Affected Endpoints**: Various device-specific endpoints
**Conditions**: When endpoint doesn't support the device type

**Expected**: JSON error response or HTTP error status

**Actual**: Empty string response body

**Workaround**: Check for empty response text before JSON parsing.

**Files**: `custom_components/loggamera/api.py:119-121`

---

### 2. Inconsistent Error Message Structure

**Issue**: Error messages are returned in different formats across endpoints.

**Format 1** (Most endpoints):
```json
{
  "Error": "error message string"
}
```

**Format 2** (Some endpoints):
```json
{
  "Error": {
    "Message": "error message string"
  }
}
```

**Impact**: Requires complex error parsing logic.

**Workaround**: Check both string and object error formats.

**Files**: `custom_components/loggamera/api.py:128-141`

---

### 3. Null vs Missing ValueType Fields

**Issue**: `ValueType` field is often null in RawData responses rather than being omitted or having a meaningful value.

**Impact**: Cannot determine sensor data type directly from ValueType.

**Workaround**: Infer data types from UnitType and Value content.

**Files**: `custom_components/loggamera/sensor.py:1015-1031`

---

## Authentication Issues

### 1. API Key in Request Body, Not Headers

**Issue**: API requires API key in JSON request body rather than standard HTTP Authorization header.

**Standard Practice**: `Authorization: Bearer <api_key>` header
**Loggamera API**: Include `"ApiKey": "<api_key>"` in request body

**Impact**: Non-standard authentication method.

**Files**: `custom_components/loggamera/api.py:104-106`

---

## Endpoint Availability Problems

### 1. Inconsistent Endpoint Support by Device Type

**Issue**: Not all endpoints work with all device types, but this is not documented.

**Examples**:
- PowerMeter devices: PowerMeter endpoint works, RoomSensor endpoint fails
- HeatMeter devices: No dedicated endpoint, must use RawData
- Some devices: Capabilities endpoint not available

**Expected**: Clear documentation of which endpoints support which device types.

**Workaround**: Implement endpoint caching and fallback mechanisms.

**Files**: `custom_components/loggamera/api.py:278-313`

---

### 2. "Invalid Endpoint" vs "Access Denied"

**Issue**: API returns "invalid endpoint" for both unsupported endpoints and permission issues.

**Impact**: Cannot distinguish between true endpoint unavailability and permission problems.

**Workaround**: Cache endpoint availability to avoid repeated failures.

**Files**: `custom_components/loggamera/api.py:61-62, 135`

---

## Data Type and Value Inconsistencies

### 1. Inconsistent Unit Case Sensitivity

**Issue**: API returns both lowercase and uppercase variants for the same unit type.

**Examples**:
- `"ConsumedTotalInm3"` (lowercase m3)
- `"ConsumedTotalInM3"` (uppercase M3)

**Impact**: Requires mapping both variants to the same sensor type.

**Files**: `custom_components/loggamera/sensor.py:609-614`

---

### 2. String vs Numeric Value Types

**Issue**: Numeric values are sometimes returned as strings, sometimes as numbers.

**Impact**: Requires type conversion and validation in integration.

**Workaround**: Convert string numbers to appropriate numeric types.

---

## SSL/TLS Certificate Issues

### 1. Certificate Verification Failures

**Issue**: SSL certificate verification frequently fails in various environments, particularly Docker containers.

**Common Errors**:
- `CERTIFICATE_VERIFY_FAILED`
- `WRONG_VERSION_NUMBER`
- Missing CA certificates

**Workaround**: Explicit certificate path specification using certifi library.

**Files**: Multiple tool files, `tools/diagnose_tls.sh`

---

## Update Frequency Limitations

### 1. PowerMeter Data Update Intervals

**Issue**: PowerMeter endpoint data only updates approximately every 30 minutes regardless of polling frequency.

**Impact**: More frequent polling doesn't yield more current data.

**Expected**: Real-time or configurable update intervals.

**Documentation**: Should be clearly documented in API specs.

**Files**: `custom_components/loggamera/api.py:42-45`

---

## Organization Access Patterns

### 1. Complex Child Organization Access

**Issue**: Accessing devices in child organizations requires temporarily switching organization context.

**Process**:
1. Store original organization ID
2. Switch to child organization ID
3. Make device request
4. Restore original organization ID

**Expected**: Single request with organization hierarchy support.

**Impact**: Requires complex state management.

**Files**: `custom_components/loggamera/__init__.py:235-263`

---

## Error Handling Inconsistencies

### 1. Capabilities Endpoint Error Behavior

**Issue**: Capabilities endpoint may not be available for all devices but returns "invalid endpoint" instead of empty capabilities.

**Expected**: Empty capabilities response `{"ReadCapabilities": [], "WriteCapabilities": []}`.

**Workaround**: Catch "invalid endpoint" error and return empty capabilities.

**Files**: `custom_components/loggamera/api.py:369-380`

---

### 2. Scenarios Endpoint Availability

**Issue**: Scenarios endpoint may not be available for all organizations.

**Expected**: Empty scenarios list when no scenarios exist.

**Actual**: "invalid endpoint" error for organizations without scenario support.

**Workaround**: Return empty scenarios list on endpoint error.

**Files**: `custom_components/loggamera/api.py:396-405`

---

## Integration Workarounds Summary

The Home Assistant integration implements the following workarounds for these API issues:

### Fallback Mechanisms
- **Endpoint cascading**: Try primary endpoint, fall back to RawData, then GenericDevice
- **Endpoint caching**: Remember which endpoints are invalid to avoid repeated failures
- **Error normalization**: Handle multiple error response formats

### Data Normalization
- **Spelling correction**: Fix API typos in display names
- **Type conversion**: Convert string numbers to appropriate numeric types
- **Unit standardization**: Handle case variations in unit names

### Reliability Improvements
- **SSL handling**: Explicit certificate management
- **Timeout handling**: Reasonable timeouts with retry logic
- **State management**: Careful organization context switching

---

## Recommendations for API Improvements

1. **Standardize Error Responses**: Use consistent error message format across all endpoints
2. **Fix Spelling Errors**: Correct "Voltate" to "Voltage" and "Signal-Noice" to "Signal-Noise"
3. **Add HeatMeter Endpoint**: Implement dedicated `/HeatMeter` endpoint
4. **Document Endpoint Support**: Clearly specify which endpoints work with which device types
5. **Improve Authentication**: Support standard Authorization headers
6. **Consistent Data Types**: Return numeric values as numbers, not strings
7. **Update Frequency Documentation**: Document actual update intervals for each endpoint
8. **Graceful Degradation**: Return empty arrays instead of "invalid endpoint" errors

---

**Note**: This errata is based on integration development experience and may not reflect the latest API documentation. Always consult official Loggamera API documentation for authoritative information.
