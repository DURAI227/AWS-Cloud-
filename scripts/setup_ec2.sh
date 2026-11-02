#!/usr/bin/env bash
# ==============================================================================
# scripts/setup_ec2.sh
# AWS EC2 Ubuntu 24.04 LTS Server Provisioning & Configuration Script
# Installs Python, Git, Nginx, Gunicorn, systemd service, and UFW firewall.
# ==============================================================================

set -euo pipefail

# Text formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APP_DIR="/var/www/flaskapp"
LOG_DIR="/var/log/flaskapp"
NGINX_LOG_DIR="/var/log/nginx"
APP_USER="ubuntu"
APP_GROUP="ubuntu"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Starting Automated AWS EC2 Server Setup (Ubuntu 24.04 LTS)       ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Check for root / sudo privileges
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This setup script must be run as root or with sudo.${NC}"
   exit 1
fi

echo -e "${YELLOW}[1/8] Updating Ubuntu system package repositories...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

echo -e "${YELLOW}[2/8] Installing core system packages and dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    nginx \
    curl \
    tar \
    gzip \
    unzip \
    jq \
    ufw

# Install AWS CLI v2 if not present
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}Installing AWS CLI v2...${NC}"
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q -o /tmp/awscliv2.zip -d /tmp
    /tmp/aws/install --update || true
    rm -rf /tmp/aws /tmp/awscliv2.zip
fi

echo -e "${YELLOW}[3/8] Creating directory structure and setting ownership...${NC}"
mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/backups"
mkdir -p "${APP_DIR}/logs"
mkdir -p "${APP_DIR}/data"
mkdir -p "${LOG_DIR}"
mkdir -p "${NGINX_LOG_DIR}"

chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
chown -R "${APP_USER}:${APP_GROUP}" "${LOG_DIR}"
chmod 755 "${APP_DIR}"
chmod 755 "${LOG_DIR}"

echo -e "${YELLOW}[4/8] Initializing Python virtual environment...${NC}"
if [[ ! -d "${APP_DIR}/venv" ]]; then
    sudo -u "${APP_USER}" python3 -m venv "${APP_DIR}/venv"
fi

# Upgrade pip inside venv and install requirements
echo -e "${YELLOW}Installing Python packages via pip...${NC}"
sudo -u "${APP_USER}" "${APP_DIR}/venv/bin/pip" install --upgrade pip setuptools wheel
if [[ -f "${APP_DIR}/requirements.txt" ]]; then
    sudo -u "${APP_USER}" "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
fi

echo -e "${YELLOW}[5/8] Configuring systemd service: flaskapp.service...${NC}"
if [[ -f "${APP_DIR}/deployment/flaskapp.service" ]]; then
    cp "${APP_DIR}/deployment/flaskapp.service" /etc/systemd/system/flaskapp.service
    systemctl daemon-reload
    systemctl enable flaskapp.service
else
    echo -e "${RED}[WARN] deployment/flaskapp.service not found in ${APP_DIR}. Skipping systemd copy.${NC}"
fi

echo -e "${YELLOW}[6/8] Configuring Nginx reverse proxy...${NC}"
if [[ -f "${APP_DIR}/deployment/nginx.conf" ]]; then
    cp "${APP_DIR}/deployment/nginx.conf" /etc/nginx/sites-available/flaskapp
    # Remove default site if exists
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/flaskapp

    # Test Nginx configuration
    nginx -t
    systemctl enable nginx
else
    echo -e "${RED}[WARN] deployment/nginx.conf not found. Skipping Nginx config.${NC}"
fi

echo -e "${YELLOW}[7/8] Configuring UFW Firewall...${NC}"
ufw status | grep -q "Status: active" || {
    ufw allow 22/tcp comment 'OpenSSH'
    ufw allow 80/tcp comment 'Nginx HTTP'
    ufw allow 443/tcp comment 'Nginx HTTPS'
    ufw --force enable
}

echo -e "${YELLOW}[8/8] Starting Application and Web Server Services...${NC}"
systemctl restart flaskapp.service
systemctl restart nginx

# Allow 3 seconds for service startup
sleep 3

# Run Health Check
echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Validating Service Health via scripts/health_check.sh           ${NC}"
echo -e "${BLUE}====================================================================${NC}"
if [[ -f "${APP_DIR}/scripts/health_check.sh" ]]; then
    chmod +x "${APP_DIR}/scripts/health_check.sh"
    "${APP_DIR}/scripts/health_check.sh"
else
    curl -f http://127.0.0.1:5000/health && echo -e "\n${GREEN}[SUCCESS] Health check endpoint responded OK!${NC}"
fi

echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}   AWS EC2 Server Setup Completed Successfully!                     ${NC}"
echo -e "${GREEN}====================================================================${NC}"
