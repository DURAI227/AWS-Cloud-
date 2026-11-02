"""
AWS Cloud Deployment Portal - Flask Web Application
Senior DevOps & Cloud Engineering Architecture

Exposes monitoring endpoints, DevOps dashboard, infrastructure metrics,
Jenkins CI/CD integration, and S3 backup verification.
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, jsonify, request, abort

from config.settings import (
    Config,
    BASE_DIR,
    get_git_info,
    get_ec2_metadata,
    get_jenkins_status,
    get_s3_status,
    get_system_metrics
)

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('aws_deployment_app')
logger.setLevel(logging.INFO)

# Formatter
log_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s:%(lineno)d): %(message)s'
)

# File Handler (5 MB max, 3 backups)
log_file = Config.LOGS_DIR / 'app.log'
file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# ---------------------------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION} in {Config.FLASK_ENV} mode")


def load_deployments():
    """Load deployment records from data/deployments.json."""
    if not Config.DEPLOYMENTS_FILE.exists():
        return []
    try:
        with open(Config.DEPLOYMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read deployments file: {e}")
        return []


def save_deployments(deployments_list):
    """Save deployment records to data/deployments.json."""
    try:
        with open(Config.DEPLOYMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(deployments_list, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save deployments file: {e}")
        return False


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Server-Version'] = f"Gunicorn/Flask-v{Config.APP_VERSION}"
    return response


# ---------------------------------------------------------------------------
# Frontend Views
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    """Home Dashboard."""
    logger.info("Serving Home Dashboard")
    ec2_info = get_ec2_metadata()
    jenkins_info = get_jenkins_status()
    git_info = get_git_info()
    s3_info = get_s3_status()
    deployments = load_deployments()
    system_metrics = get_system_metrics()

    latest_deployment = deployments[0] if deployments else None

    return render_template(
        'index.html',
        app_name=Config.APP_NAME,
        app_version=Config.APP_VERSION,
        environment=Config.FLASK_ENV,
        ec2=ec2_info,
        jenkins=jenkins_info,
        git=git_info,
        s3=s3_info,
        deployments=deployments[:5],
        latest_deployment=latest_deployment,
        metrics=system_metrics
    )


@app.route('/deployments')
def deployments_view():
    """Dedicated Deployments Page."""
    logger.info("Serving Deployments View")
    deployments = load_deployments()
    jenkins_info = get_jenkins_status()
    git_info = get_git_info()
    return render_template(
        'deployments.html',
        app_name=Config.APP_NAME,
        app_version=Config.APP_VERSION,
        deployments=deployments,
        jenkins=jenkins_info,
        git=git_info
    )


@app.route('/infrastructure')
def infrastructure_view():
    """Dedicated AWS Infrastructure Page."""
    logger.info("Serving Infrastructure View")
    ec2_info = get_ec2_metadata()
    s3_info = get_s3_status()
    metrics = get_system_metrics()
    return render_template(
        'infrastructure.html',
        app_name=Config.APP_NAME,
        app_version=Config.APP_VERSION,
        ec2=ec2_info,
        s3=s3_info,
        metrics=metrics
    )


@app.route('/documentation')
def documentation_view():
    """Project Architecture and Operations Documentation."""
    logger.info("Serving Documentation View")
    return render_template(
        'documentation.html',
        app_name=Config.APP_NAME,
        app_version=Config.APP_VERSION,
        github_repo=Config.GITHUB_REPO_URL
    )


# ---------------------------------------------------------------------------
# Required REST API Endpoints
# ---------------------------------------------------------------------------
@app.route('/health')
def health_check():
    """
    Health check endpoint for Jenkins CI/CD verification, AWS ALB/Target Group,
    and automated monitoring.
    """
    metrics = get_system_metrics()
    ec2_info = get_ec2_metadata()

    is_healthy = True
    status_label = "healthy"

    # Memory/disk threshold warning check
    if metrics.get('disk_percent', 0) > 95 or metrics.get('memory_percent', 0) > 95:
        status_label = "warning_resource_high"

    response = {
        "status": status_label,
        "application": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "environment": Config.FLASK_ENV,
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        "uptime_seconds": metrics['uptime_seconds'],
        "uptime": metrics['uptime_formatted'],
        "python_version": metrics['python_version'],
        "system_metrics": {
            "cpu_percent": metrics['cpu_percent'],
            "memory_percent": metrics['memory_percent'],
            "disk_percent": metrics['disk_percent']
        },
        "ec2_instance": {
            "is_ec2": ec2_info['is_ec2'],
            "instance_id": ec2_info['instance_id'],
            "status": ec2_info['status']
        }
    }
    return jsonify(response), 200


@app.route('/api/status')
def api_status():
    """Comprehensive deployment, infrastructure, and CI/CD status payload."""
    return jsonify({
        "status": "healthy",
        "app_name": Config.APP_NAME,
        "app_version": Config.APP_VERSION,
        "environment": Config.FLASK_ENV,
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        "ec2": get_ec2_metadata(),
        "jenkins": get_jenkins_status(),
        "git": get_git_info(),
        "s3": get_s3_status(),
        "system": get_system_metrics()
    }), 200


@app.route('/api/deployments', methods=['GET', 'POST'])
def api_deployments():
    """
    GET: Retrieve deployment history.
    POST: Record a new deployment (invoked by Jenkins deploy stage or deploy.sh).
    """
    if request.method == 'GET':
        deployments = load_deployments()
        return jsonify({
            "status": "success",
            "count": len(deployments),
            "deployments": deployments
        }), 200

    # POST - Create new deployment record
    try:
        data = request.get_json(force=True, silent=True) or {}
        deployments = load_deployments()

        git_info = get_git_info()
        new_id = f"DEP-{1000 + len(deployments) + 1}"

        record = {
            "id": data.get("id", new_id),
            "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            "commit_hash": data.get("commit_hash", git_info['commit_hash']),
            "author": data.get("author", git_info['author']),
            "branch": data.get("branch", git_info['branch']),
            "status": data.get("status", "SUCCESS"),
            "duration": data.get("duration", "40s"),
            "environment": data.get("environment", f"AWS EC2 ({Config.FLASK_ENV})"),
            "backup_file": data.get("backup_file", f"flaskapp-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.tar.gz"),
            "details": data.get("details", "Deployment executed via automation script")
        }

        # Prepend to list
        deployments.insert(0, record)
        save_deployments(deployments)

        logger.info(f"Recorded deployment {record['id']} status: {record['status']}")
        return jsonify({"status": "success", "record": record}), 201

    except Exception as e:
        logger.error(f"Error recording deployment: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/system-info')
def api_system_info():
    """Detailed host hardware and runtime information."""
    return jsonify({
        "status": "success",
        "system_info": get_system_metrics(),
        "ec2_metadata": get_ec2_metadata(),
        "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    }), 200


@app.route('/api/backups')
def api_backups():
    """AWS S3 and local backup records."""
    s3_data = get_s3_status()

    # Also list local backup files if present
    local_backups = []
    if Config.BACKUPS_DIR.exists():
        for f in Config.BACKUPS_DIR.glob('*.tar.gz'):
            stat = f.stat()
            local_backups.append({
                "filename": f.name,
                "size_kb": round(stat.st_size / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S UTC')
            })

    return jsonify({
        "status": "success",
        "s3_status": s3_data,
        "local_backups": local_backups
    }), 200


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/') or request.path == '/health':
        return jsonify({"error": "Resource Not Found", "status_code": 404, "path": request.path}), 404
    return render_template('index.html', error_message="Page Not Found (404)"), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    if request.path.startswith('/api/') or request.path == '/health':
        return jsonify({"error": "Internal Server Error", "status_code": 500}), 500
    return render_template('index.html', error_message="Internal Server Error (500)"), 500


# ---------------------------------------------------------------------------
# Main Entry Point (Local Development / Gunicorn Entry)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port = Config.PORT
    debug = Config.DEBUG
    logger.info(f"Starting server on 0.0.0.0:{port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
