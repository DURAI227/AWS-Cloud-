#!/usr/bin/env bash
# ==============================================================================
# scripts/deploy.sh
# Production Application Deployment Script for AWS EC2
# Performs Git pull, backup creation, dependency sync, service restart & health verification.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_DIR="${APP_DIR:-/var/www/flaskapp}"
BRANCH="${1:-main}"
DEPLOY_START_TIME=$(date +%s)

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Starting Application Deployment on AWS EC2                       ${NC}"
echo -e "${BLUE}   Target Directory: ${APP_DIR} | Branch: ${BRANCH}                 ${NC}"
echo -e "${BLUE}====================================================================${NC}"

if [[ ! -d "${APP_DIR}" ]]; then
    echo -e "${RED}[ERROR] Target directory ${APP_DIR} does not exist. Run setup_ec2.sh first.${NC}"
    exit 1
fi

cd "${APP_DIR}"

# 1. Create Pre-Deployment Backup
echo -e "${YELLOW}[1/6] Generating pre-deployment backup...${NC}"
if [[ -f "${APP_DIR}/scripts/backup.sh" ]]; then
    chmod +x "${APP_DIR}/scripts/backup.sh"
    "${APP_DIR}/scripts/backup.sh" || echo -e "${YELLOW}[WARN] S3 backup script returned non-zero code. Proceeding with deployment.${NC}"
else
    echo -e "${YELLOW}[WARN] backup.sh script not found. Skipping backup step.${NC}"
fi

# 2. Fetch Latest Source Code
echo -e "${YELLOW}[2/6] Pulling latest code changes from Git repository (${BRANCH})...${NC}"
if [[ -d "${APP_DIR}/.git" ]]; then
    git fetch origin "${BRANCH}"
    git reset --hard "origin/${BRANCH}"
    COMMIT_HASH=$(git rev-parse --short HEAD)
    COMMIT_AUTHOR=$(git log -1 --pretty=%an)
    COMMIT_MSG=$(git log -1 --pretty=%s)
else
    echo -e "${YELLOW}[INFO] Standalone deployment mode (not a live git clone). Skipping git pull.${NC}"
    COMMIT_HASH="manual"
    COMMIT_AUTHOR="DevOps Engineer"
    COMMIT_MSG="Manual release deployment"
fi

# 3. Synchronize Dependencies
echo -e "${YELLOW}[3/6] Installing/Updating Python virtual environment dependencies...${NC}"
if [[ -f "${APP_DIR}/requirements.txt" && -d "${APP_DIR}/venv" ]]; then
    "${APP_DIR}/venv/bin/pip" install --upgrade pip
    "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/requirements.txt"
fi

# Ensure permissions
chown -R ubuntu:ubuntu "${APP_DIR}" || true

# 4. Restart Gunicorn Application Service
echo -e "${YELLOW}[4/6] Restarting Linux systemd service (flaskapp.service)...${NC}"
sudo systemctl restart flaskapp.service
sleep 3

# 5. Run Health Check Validation
echo -e "${YELLOW}[5/6] Validating application health...${NC}"
HEALTH_SUCCESS=false

for attempt in {1..6}; do
    echo -e "Attempt ${attempt}/6: Probing http://127.0.0.1:5000/health..."
    if curl -s -f -m 3 http://127.0.0.1:5000/health | grep -q '"status"'; then
        HEALTH_SUCCESS=true
        break
    fi
    sleep 2
done

if [[ "${HEALTH_SUCCESS}" != "true" ]]; then
    echo -e "${RED}[FATAL ERROR] Application health check failed after restart!${NC}"
    echo -e "${RED}Fetching last 30 lines of service log:${NC}"
    sudo journalctl -u flaskapp.service -n 30 --no-pager || true
    exit 1
fi

# 6. Record Deployment Metrics
DEPLOY_END_TIME=$(date +%s)
DURATION=$((DEPLOY_END_TIME - DEPLOY_START_TIME))

echo -e "${YELLOW}[6/6] Registering deployment in application audit history...${NC}"
curl -s -X POST http://127.0.0.1:5000/api/deployments \
    -H "Content-Type: application/json" \
    -d "{\"commit_hash\": \"${COMMIT_HASH}\", \"author\": \"${COMMIT_AUTHOR}\", \"branch\": \"${BRANCH}\", \"duration\": \"${DURATION}s\", \"details\": \"${COMMIT_MSG}\", \"status\": \"SUCCESS\"}" \
    || true

echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}   Deployment Succeeded in ${DURATION} seconds!                     ${NC}"
echo -e "${GREEN}   Commit: ${COMMIT_HASH} | Author: ${COMMIT_AUTHOR}                ${NC}"
echo -e "${GREEN}====================================================================${NC}"

