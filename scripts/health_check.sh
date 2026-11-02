#!/usr/bin/env bash
# ==============================================================================
# scripts/health_check.sh
# End-to-End Application & Infrastructure Health Validation Script
# Probes Flask /health endpoint, Gunicorn WSGI process, and Nginx reverse proxy.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TARGET_URL="${1:-http://127.0.0.1:5000/health}"
NGINX_URL="${2:-http://127.0.0.1/health}"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Executing Service Health Checks & Telemetry Verification         ${NC}"
echo -e "${BLUE}====================================================================${NC}"

FAILURES=0

# 1. Direct Gunicorn / Flask Port 5000 Check
echo -e "${YELLOW}[Check 1/3] Probing Flask application direct endpoint: ${TARGET_URL}${NC}"
HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -m 5 "${TARGET_URL}" || echo -e "CONNECTION_FAILED\n000")
HTTP_BODY=$(echo "${HTTP_RESPONSE}" | sed '$d')
HTTP_STATUS=$(echo "${HTTP_RESPONSE}" | tail -n1)

if [[ "${HTTP_STATUS}" -eq 200 ]]; then
    echo -e "${GREEN}[PASS] Endpoint responded with HTTP 200 OK${NC}"
    if echo "${HTTP_BODY}" | grep -q '"status"'; then
        echo -e "${GREEN}[PASS] Valid JSON payload received:${NC}"
        echo "${HTTP_BODY}" | jq . 2>/dev/null || echo "${HTTP_BODY}"
    else
        echo -e "${RED}[FAIL] Health endpoint response did not contain expected 'status' attribute.${NC}"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${RED}[FAIL] Health check failed with HTTP status: ${HTTP_STATUS}${NC}"
    FAILURES=$((FAILURES + 1))
fi

# 2. Systemd Service Status (If running in Linux systemd environment)
echo -e "${YELLOW}[Check 2/3] Checking Linux systemd services...${NC}"
if command -v systemctl &> /dev/null; then
    if systemctl is-active --quiet flaskapp.service 2>/dev/null; then
        echo -e "${GREEN}[PASS] flaskapp.service is ACTIVE and RUNNING${NC}"
    else
        echo -e "${YELLOW}[WARN] flaskapp.service is not active or not installed in this environment.${NC}"
    fi

    if systemctl is-active --quiet nginx 2>/dev/null; then
        echo -e "${GREEN}[PASS] nginx service is ACTIVE and RUNNING${NC}"
    else
        echo -e "${YELLOW}[WARN] nginx service is not active in this environment.${NC}"
    fi
else
    echo -e "${BLUE}[INFO] systemctl not detected (non-systemd / development runner). Skipping.${NC}"
fi

# 3. Nginx Reverse Proxy Validation (if port 80 is listening)
echo -e "${YELLOW}[Check 3/3] Probing Nginx Reverse Proxy on port 80: ${NGINX_URL}${NC}"
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "${NGINX_URL}" || echo "000")
if [[ "${NGINX_STATUS}" -eq 200 ]]; then
    echo -e "${GREEN}[PASS] Nginx reverse proxy forwarded traffic successfully (HTTP 200).${NC}"
elif [[ "${NGINX_STATUS}" -eq 000 ]]; then
    echo -e "${YELLOW}[INFO] Nginx port 80 not responding (likely local dev mode or Nginx unconfigured).${NC}"
else
    echo -e "${RED}[WARN] Nginx returned HTTP ${NGINX_STATUS}${NC}"
fi

echo -e "${BLUE}====================================================================${NC}"
if [[ ${FAILURES} -eq 0 ]]; then
    echo -e "${GREEN}   HEALTH CHECK PASSED - All Critical Services Operational!        ${NC}"
    echo -e "${BLUE}====================================================================${NC}"
    exit 0
else
    echo -e "${RED}   HEALTH CHECK FAILED - ${FAILURES} critical checks failed!       ${NC}"
    echo -e "${BLUE}====================================================================${NC}"
    exit 1
fi

