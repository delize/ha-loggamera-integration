#!/bin/sh
# Loggamera TLS/SSL Diagnosis Tool for Home Assistant Docker
# This script helps diagnose certificate and TLS issues with the Loggamera integration

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

printf "${BLUE}=========================================================\n${NC}"
printf "${BLUE}  Loggamera TLS/SSL Diagnosis Tool for Home Assistant\n${NC}"
printf "${BLUE}=========================================================\n${NC}"
printf "\n"

# Check if running in Docker - using standard POSIX-compatible syntax
if [ ! -f /.dockerenv ] && [ ! -f /run/.containerenv ]; then
    printf "${YELLOW}WARNING: This script is designed to run inside a Home Assistant Docker container.\n${NC}"
    printf "${YELLOW}You can run it with:\n${NC}"
    printf "${GREEN}docker exec -it homeassistant bash -c \"curl -s https://raw.githubusercontent.com/delize/ha-loggamera-integration/main/tools/diagnose_tls.sh | bash\"\n${NC}"
    printf "\n"
    printf "${YELLOW}Continue anyway? (y/n)\n${NC}"
    read -r answer
    if [ "$answer" != "y" ]; then
        printf "${RED}Exiting script as requested.\n${NC}"
        exit 1
    fi
fi

printf "${BLUE}Checking system information...\n${NC}"
# More portable OS detection that works with POSIX shells
if [ -f /etc/os-release ]; then
    os_name=$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d \")
else
    os_name=$(uname -a)
fi
printf "OS: %s\n" "$os_name"
printf "Python version: %s\n" "$(python3 --version 2>&1)"
printf "Docker: %s\n" "$([ -f /.dockerenv ] && echo 'Yes' || echo 'No')"
printf "\n"

# Check for required tools
printf "${BLUE}Checking for required tools...\n${NC}"
missing_tools=false

# Check for OpenSSL
if ! command -v openssl > /dev/null 2>&1; then
    printf "${RED}✗ OpenSSL not found\n${NC}"
    printf "  Installing OpenSSL...\n"
    if command -v apt-get > /dev/null 2>&1; then
        apt-get update && apt-get install -y openssl ca-certificates
        if [ $? -ne 0 ]; then
            printf "${RED}Failed to install OpenSSL\n${NC}"
            missing_tools=true
        else
            printf "${GREEN}✓ OpenSSL installed\n${NC}"
        fi
    else
        printf "${RED}Cannot install OpenSSL (apt-get not found)\n${NC}"
        missing_tools=true
    fi
else
    printf "${GREEN}✓ OpenSSL found: %s\n${NC}" "$(openssl version)"
fi

# Check for curl
if ! command -v curl > /dev/null 2>&1; then
    printf "${RED}✗ curl not found\n${NC}"
    printf "  Installing curl...\n"
    if command -v apt-get > /dev/null 2>&1; then
        apt-get update && apt-get install -y curl
        if [ $? -ne 0 ]; then
            printf "${RED}Failed to install curl\n${NC}"
            missing_tools=true
        else
            printf "${GREEN}✓ curl installed\n${NC}"
        fi
    else
        printf "${RED}Cannot install curl (apt-get not found)\n${NC}"
        missing_tools=true
    fi
else
    printf "${GREEN}✓ curl found: %s\n${NC}" "$(curl --version | head -n1)"
fi

if [ "$missing_tools" = true ]; then
    printf "${RED}Could not install all required tools. Some tests may fail.\n${NC}"
fi

# Check for certifi
printf "\n${BLUE}Checking Python certifi...\n${NC}"
if python3 -c "import certifi; print(f'certifi version: {certifi.__version__}, path: {certifi.where()}')"; then
    printf "${GREEN}✓ certifi is properly installed\n${NC}"
    certifi_path=$(python3 -c "import certifi; print(certifi.where())")
else
    printf "${RED}✗ certifi not found or error importing\n${NC}"
    printf "  Installing certifi...\n"
    if command -v pip > /dev/null 2>&1 || command -v pip3 > /dev/null 2>&1; then
        pip_cmd="pip"
        if ! command -v pip > /dev/null 2>&1; then
            pip_cmd="pip3"
        fi
        $pip_cmd install --upgrade certifi
        if [ $? -eq 0 ]; then
            printf "${GREEN}✓ certifi installed\n${NC}"
            certifi_path=$(python3 -c "import certifi; print(certifi.where())")
        else
            printf "${RED}Failed to install certifi\n${NC}"
        fi
    else
        printf "${RED}Cannot install certifi (pip/pip3 not found)\n${NC}"
    fi
fi

# Test basic connectivity
printf "\n${BLUE}Testing basic connectivity to Loggamera API...\n${NC}"
if curl -s --head https://platform.loggamera.se > /dev/null 2>&1; then
    printf "${GREEN}✓ Basic connectivity successful\n${NC}"
else
    printf "${RED}✗ Basic connectivity failed\n${NC}"
    printf "  This might be a network issue. Check if your Home Assistant can access external URLs.\n"
fi

# Test SSL/TLS connection
printf "\n${BLUE}Testing SSL/TLS connection to Loggamera API...\n${NC}"
if openssl s_client -connect platform.loggamera.se:443 -servername platform.loggamera.se </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    printf "${GREEN}✓ SSL/TLS connection successful\n${NC}"
else
    printf "${RED}✗ SSL/TLS connection verification failed\n${NC}"
    printf "  This might be a certificate issue.\n"

    # Get more details
    printf "\n${BLUE}Certificate details:\n${NC}"
    openssl s_client -connect platform.loggamera.se:443 -servername platform.loggamera.se </dev/null 2>/dev/null | grep -E "subject=|issuer="

    # Check if the CA certificates are installed
    printf "\n${BLUE}Checking CA certificates...\n${NC}"
    if [ -d /etc/ssl/certs ]; then
        printf "${GREEN}✓ CA certificates directory exists\n${NC}"
        ca_count=$(ls -1 /etc/ssl/certs/ | wc -l)
        printf "  Found %s CA certificates in /etc/ssl/certs/\n" "$ca_count"
    else
        printf "${RED}✗ CA certificates directory missing\n${NC}"
        printf "  Installing CA certificates...\n"
        if command -v apt-get > /dev/null 2>&1; then
            apt-get update && apt-get install -y ca-certificates
            if [ $? -eq 0 ]; then
                printf "${GREEN}✓ CA certificates installed\n${NC}"
            else
                printf "${RED}Failed to install CA certificates\n${NC}"
            fi
        else
            printf "${RED}Cannot install CA certificates (apt-get not found)\n${NC}"
        fi
    fi
fi

# Check if certifi's CA certificates are valid for the connection
printf "\n${BLUE}Testing connection using certifi's CA bundle...\n${NC}"
if [ -n "$certifi_path" ]; then
    if curl -s --cacert "$certifi_path" https://platform.loggamera.se > /dev/null 2>&1; then
        printf "${GREEN}✓ Connection using certifi successful\n${NC}"
    else
        printf "${RED}✗ Connection using certifi failed\n${NC}"
        printf "  The certifi bundle may be missing the required CA certificate.\n"

        # Copy system CA certificates to a custom location
        printf "\n${BLUE}Creating a custom CA bundle...\n${NC}"
        if [ -d /etc/ssl/certs ]; then
            mkdir -p /etc/ssl/certs/custom
            if [ -f /etc/ssl/certs/ca-certificates.crt ]; then
                cp -f /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/custom/cacert.pem
                printf "  Custom CA bundle created at /etc/ssl/certs/custom/cacert.pem\n"

                # Test with the custom bundle
                if curl -s --cacert /etc/ssl/certs/custom/cacert.pem https://platform.loggamera.se > /dev/null 2>&1; then
                    printf "${GREEN}✓ Connection using custom CA bundle successful\n${NC}"
                    printf "  You can modify the api.py file to use this custom bundle:\n"
                    printf "  Add at the top: CERT_PATH = \"/etc/ssl/certs/custom/cacert.pem\"\n"
                    printf "  And use: session.verify = CERT_PATH\n"
                else
                    printf "${RED}✗ Connection using custom CA bundle also failed\n${NC}"
                fi
            else
                printf "${RED}✗ Cannot find system CA certificates\n${NC}"
            fi
        else
            printf "${RED}✗ Cannot create custom bundle\n${NC}"
        fi
    fi
else
    printf "${YELLOW}! Skipping certifi test as certifi path could not be determined\n${NC}"
fi

# Summary and recommendations
printf "\n${BLUE}=========================================================\n${NC}"
printf "${BLUE}                   Summary & Fixes\n${NC}"
printf "${BLUE}=========================================================\n${NC}"

printf "\n${YELLOW}If you're still having certificate issues, try these solutions:\n${NC}"
printf "\n${GREEN}1. Ensure CA certificates are up-to-date:\n${NC}"
printf "   docker exec -it homeassistant bash -c 'apt-get update && apt-get install -y ca-certificates'\n"

printf "\n${GREEN}2. Upgrade certifi:\n${NC}"
printf "   docker exec -it homeassistant bash -c 'pip install --upgrade certifi'\n"

printf "\n${GREEN}3. Use the custom CA bundle:\n${NC}"
printf "   - Create the bundle:\n"
printf "     docker exec -it homeassistant bash -c 'mkdir -p /etc/ssl/certs/custom && cp /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/custom/cacert.pem'\n"
printf "   - Modify the integration's api.py to use this bundle\n"

printf "\n${GREEN}4. Test with our connection diagnostic tool:\n${NC}"
printf "   python3 test_connection.py YOUR_API_KEY\n"

printf "\n${YELLOW}For more detailed troubleshooting, see our documentation:\n${NC}"
printf "https://github.com/delize/ha-loggamera-integration/blob/main/docs/TROUBLESHOOTING.md\n"

printf "\n${BLUE}=========================================================\n${NC}"
printf "${BLUE}               Diagnosis Complete\n${NC}"
printf "${BLUE}=========================================================\n${NC}"
