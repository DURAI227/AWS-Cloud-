"""
Automated Test Suite for AWS Cloud Deployment Portal
Tests all routes, REST API endpoints, security headers, deployment audit recording,
and infrastructure status reporting using pytest.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import pytest
from app import app
from config.settings import (
    get_git_info,
    get_ec2_metadata,
    get_jenkins_status,
    get_s3_status,
    get_system_metrics
)


@pytest.fixture
def client():
    """Create Flask test client with test configuration."""
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    with app.test_client() as client:
        yield client


# ==============================================================================
# 1. Frontend Route Tests
# ==============================================================================

def test_home_page(client):
    """Test GET / returns HTTP 200 and loads DevOps dashboard."""
    response = client.get('/')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "DevOps" in content or "AWS" in content
    assert "Jenkins" in content
    assert "Infrastructure" in content


def test_deployments_page(client):
    """Test GET /deployments returns HTTP 200 and renders deployments log."""
    response = client.get('/deployments')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "Deployments" in content
    assert "Pipeline" in content


def test_infrastructure_page(client):
    """Test GET /infrastructure returns HTTP 200 and details cloud components."""
    response = client.get('/infrastructure')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "AWS EC2" in content
    assert "S3" in content
    assert "Gunicorn" in content


def test_documentation_page(client):
    """Test GET /documentation returns HTTP 200 and runbook guidelines."""
    response = client.get('/documentation')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert "System Architecture" in content
    assert "REST API" in content


# ==============================================================================
# 2. Required REST API Endpoint Tests
# ==============================================================================

def test_health_check_endpoint(client):
    """Test GET /health returns HTTP 200 with JSON status healthy."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert "status" in data
    assert data["status"] in ["healthy", "warning_resource_high"]
    assert "uptime_seconds" in data
    assert "python_version" in data
    assert "system_metrics" in data
    assert "cpu_percent" in data["system_metrics"]
    assert "memory_percent" in data["system_metrics"]
    assert "disk_percent" in data["system_metrics"]


def test_api_status_endpoint(client):
    """Test GET /api/status returns full telemetry payload."""
    response = client.get('/api/status')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert data["status"] == "healthy"
    assert "ec2" in data
    assert "jenkins" in data
    assert "git" in data
    assert "s3" in data
    assert "system" in data


def test_api_system_info_endpoint(client):
    """Test GET /api/system-info returns hardware and OS metrics."""
    response = client.get('/api/system-info')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert data["status"] == "success"
    assert "system_info" in data
    assert "os" in data["system_info"]
    assert "cpu_count" in data["system_info"]
    assert "memory_total_gb" in data["system_info"]


def test_api_deployments_get(client):
    """Test GET /api/deployments returns history list."""
    response = client.get('/api/deployments')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert data["status"] == "success"
    assert "count" in data
    assert isinstance(data["deployments"], list)
    assert data["count"] >= 1


def test_api_deployments_post(client):
    """Test POST /api/deployments records a new deployment."""
    payload = {
        "branch": "feature/jenkins-test",
        "commit_hash": "c9a72b1",
        "author": "Jenkins Test Runner",
        "duration": "25s",
        "details": "Automated pytest validation event"
    }

    response = client.post(
        '/api/deployments',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "record" in data
    assert data["record"]["branch"] == "feature/jenkins-test"
    assert data["record"]["author"] == "Jenkins Test Runner"


def test_api_backups_endpoint(client):
    """Test GET /api/backups returns backup registry."""
    response = client.get('/api/backups')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.get_json()
    assert data["status"] == "success"
    assert "s3_status" in data
    assert "local_backups" in data


# ==============================================================================
# 3. Security Headers and Error Handling Tests
# ==============================================================================

def test_security_headers_present(client):
    """Test response contains modern security headers."""
    response = client.get('/')
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('X-XSS-Protection') == '1; mode=block'


def test_api_404_json_error(client):
    """Test 404 on API route returns structured JSON error."""
    response = client.get('/api/unknown-route')
    assert response.status_code == 404
    data = response.get_json()
    assert data["status_code"] == 404
    assert "Resource Not Found" in data["error"]


# ==============================================================================
# 4. Settings & Helper Function Unit Tests
# ==============================================================================

def test_get_git_info_returns_structure():
    """Verify git info dictionary keys."""
    info = get_git_info()
    assert "commit_hash" in info
    assert "branch" in info
    assert "repo_url" in info
    assert "author" in info


def test_get_ec2_metadata_returns_structure():
    """Verify EC2 metadata structure handles both EC2 and local environments."""
    metadata = get_ec2_metadata()
    assert "is_ec2" in metadata
    assert "status" in metadata
    assert "region" in metadata
    assert "private_ip" in metadata


def test_get_jenkins_status_returns_structure():
    """Verify Jenkins status dictionary structure."""
    status = get_jenkins_status()
    assert "is_live" in status
    assert "status" in status
    assert "pipeline_stages" in status
    assert len(status["pipeline_stages"]) == 6


def test_get_s3_status_returns_structure():
    """Verify S3 status dictionary structure."""
    s3_status = get_s3_status()
    assert "bucket_name" in s3_status
    assert "is_configured" in s3_status
    assert "status" in s3_status


def test_get_system_metrics_returns_valid_data():
    """Verify system hardware metrics calculation."""
    metrics = get_system_metrics()
    assert "os" in metrics
    assert "uptime_seconds" in metrics
    assert "cpu_count" in metrics
    assert metrics["cpu_count"] >= 1
    assert "python_version" in metrics
