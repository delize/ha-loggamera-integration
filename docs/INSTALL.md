# Installation Guide for Loggamera Integration

This guide covers different methods to install the Loggamera integration for Home Assistant.

## Prerequisites

Before installing, ensure you have:

1. A functioning Home Assistant installation (version 2023.1.0 or newer)
2. A Loggamera account and API key
3. Admin access to your Home Assistant instance

## Installation Methods

### Method 1: Manual Installation (Recommended for testing)

1. Download this repository:
   - Click the green "Code" button at the top of the repository page
   - Select "Download ZIP"
   - Extract the ZIP file on your computer

2. Copy the integration files:
   - Locate the `custom_components` directory in your Home Assistant configuration folder
   - If it doesn't exist, create it
   - Copy the `loggamera` directory from the extracted files into the `custom_components` directory
   - The result should be: `[your Home Assistant config]/custom_components/loggamera/`

3. Restart Home Assistant

### Method 2: Using HACS (Home Assistant Community Store)

If you have HACS installed, you can add this repository as a custom repository:

1. Open Home Assistant
2. Go to HACS in your sidebar
3. Click on "Integrations"
4. Click the three dots in the top right corner
5. Select "Custom repositories"
6. Add the repository URL:
   - Enter the GitHub URL for this repository
   - Select "Integration" as the category
   - Click "Add"

7. Install the integration:
   - Search for "Loggamera" in HACS integrations
   - Click "Install"
   - Restart Home Assistant

## Configuration

After installation, you need to configure the integration:

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click the "+ Add Integration" button in the bottom right
3. Search for "Loggamera" and select it
4. Enter your API key when prompted
5. Click "Submit"

## Troubleshooting Installation Issues

If you encounter issues during installation:

1. Check the Home Assistant logs for error messages
2. Verify that the integration files are in the correct location
3. Make sure you've restarted Home Assistant after installation
4. See the [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) guide for more help

## Updating the Integration

### Manual Update

1. Download the latest version of the repository
2. Replace the `loggamera` directory in your `custom_components` folder
3. Restart Home Assistant

### HACS Update

1. Open HACS in Home Assistant
2. Go to the "Integrations" tab
3. Find "Loggamera" in your installed integrations
4. If an update is available, click "Update"
5. Restart Home Assistant

## Uninstalling

If you need to uninstall the integration:

1. Go to Settings → Devices & Services
2. Find the Loggamera integration
3. Click on it and select "Delete"
4. Restart Home Assistant
5. Remove the `loggamera` directory from your `custom_components` folder
