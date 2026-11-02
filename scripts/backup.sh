#!/usr/bin/env bash
# ==============================================================================
# scripts/backup.sh
# Automated Application Backup & AWS S3 Archival Script
# Creates a compressed snapshot and uploads it to an encrypted S3 bucket.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_DIR="${APP_DIR:-/var/www/flaskapp}"
BACKUP_DIR="${APP_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILENAME="flaskapp-backup-${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

# Load environment variables if .env exists
if [[ -f "${APP_DIR}/.env" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "${APP_DIR}/.env"
    set +a
fi

S3_BUCKET="${1:-${S3_BUCKET_NAME:-}}"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   Starting Pre-Deployment Application Backup                       ${NC}"
echo -e "${BLUE}   Archive: ${BACKUP_FILENAME}                                      ${NC}"
echo -e "${BLUE}====================================================================${NC}"

mkdir -p "${BACKUP_DIR}"

# 1. Create compressed tarball excluding ephemeral & virtual environment data
echo -e "${YELLOW}[1/3] Compressing application code and data...${NC}"
tar --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='backups' \
    --exclude='logs/*.log' \
    -czf "${BACKUP_PATH}" \
    -C "${APP_DIR}" .

BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
echo -e "${GREEN}[SUCCESS] Local backup created: ${BACKUP_PATH} (${BACKUP_SIZE})${NC}"

# 2. Local Backup Retention Management (Keep latest 5 backups)
echo -e "${YELLOW}[2/3] Applying local backup retention policy (retaining latest 5)...${NC}"
cd "${BACKUP_DIR}"
ls -t flaskapp-backup-*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f || true

# 3. AWS S3 Upload Integration
echo -e "${YELLOW}[3/3] Uploading backup snapshot to AWS S3...${NC}"
if [[ -z "${S3_BUCKET}" ]]; then
    echo -e "${YELLOW}[INFO] S3_BUCKET_NAME is not configured. Local backup saved only.${NC}"
    echo -e "${YELLOW}To enable S3 upload, export S3_BUCKET_NAME=<your-bucket> in .env${NC}"
    exit 0
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}[WARN] AWS CLI is not installed. Unable to push backup to S3 bucket '${S3_BUCKET}'.${NC}"
    exit 0
fi

echo -e "Target S3 URI: s3://${S3_BUCKET}/backups/${BACKUP_FILENAME}"

if aws s3 cp "${BACKUP_PATH}" "s3://${S3_BUCKET}/backups/${BACKUP_FILENAME}" --sse AES256; then
    echo -e "${GREEN}[SUCCESS] Backup successfully uploaded to S3: s3://${S3_BUCKET}/backups/${BACKUP_FILENAME}${NC}"
else
    echo -e "${RED}[ERROR] S3 upload failed. Verify IAM permissions or AWS credentials.${NC}"
    exit 1
fi

echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}   Application Backup Workflow Completed Successfully!              ${NC}"
echo -e "${GREEN}====================================================================${NC}"
