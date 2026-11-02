"""
Application Configuration and Environment Settings
Handles environment variables, AWS metadata detection (IMDSv2),
Git repository information, Jenkins build metadata, and system resource inspection.
"""

import os
import sys
import platform
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
START_TIME = time.time()


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-secret-key-change-in-prod')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    PORT = int(os.environ.get('PORT', 5000))
    APP_NAME = os.environ.get('APP_NAME', 'AWS Cloud Deployment Portal')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')

    # AWS Settings
    AWS_REGION = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')

    # Jenkins CI/CD Settings
    JENKINS_URL = os.environ.get('JENKINS_URL', '')
    JENKINS_JOB_NAME = os.environ.get('JENKINS_JOB_NAME', 'aws-cloud-deployment-pipeline')
    BUILD_NUMBER = os.environ.get('BUILD_NUMBER', '')
    BUILD_ID = os.environ.get('BUILD_ID', '')
    BUILD_URL = os.environ.get('BUILD_URL', '')

    # Git metadata
    GITHUB_REPO_URL = os.environ.get('GITHUB_REPO_URL', 'https://github.com/DURAI227/AWS-Cloud-.git')
    GIT_BRANCH = os.environ.get('GIT_BRANCH', 'main')

    # Paths
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'
    DEPLOYMENTS_FILE = DATA_DIR / 'deployments.json'
    BACKUPS_DIR = BASE_DIR / 'backups'


def get_git_info():
    """Extract Git metadata from git command, files, or environment."""
    git_info = {
        'commit_hash': os.environ.get('GIT_COMMIT', 'unknown')[:7] if os.environ.get('GIT_COMMIT') else 'unknown',
        'full_commit_hash': os.environ.get('GIT_COMMIT', 'unknown'),
        'branch': os.environ.get('GIT_BRANCH', 'main'),
        'commit_message': os.environ.get('GIT_COMMIT_MESSAGE', 'Initial production setup'),
        'author': os.environ.get('GIT_AUTHOR', 'DevOps Team'),
        'repo_url': Config.GITHUB_REPO_URL,
        'is_live_git': False
    }

    try:
        # Check if .git directory exists and try git command
        git_dir = BASE_DIR / '.git'
        if git_dir.exists():
            # Get short hash
            rev = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=str(BASE_DIR), stderr=subprocess.DEVNULL, timeout=2
            ).decode('utf-8').strip()

            # Get full hash
            full_rev = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(BASE_DIR), stderr=subprocess.DEVNULL, timeout=2
            ).decode('utf-8').strip()

            # Get branch
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=str(BASE_DIR), stderr=subprocess.DEVNULL, timeout=2
            ).decode('utf-8').strip()

            # Get commit message
            msg = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%B'],
                cwd=str(BASE_DIR), stderr=subprocess.DEVNULL, timeout=2
            ).decode('utf-8').strip()

            # Get author
            author = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%an'],
                cwd=str(BASE_DIR), stderr=subprocess.DEVNULL, timeout=2
            ).decode('utf-8').strip()

            git_info.update({
                'commit_hash': rev,
                'full_commit_hash': full_rev,
                'branch': branch if branch != 'HEAD' else git_info['branch'],
                'commit_message': msg,
                'author': author,
                'is_live_git': True
            })
    except Exception:
        # Graceful fallback to env vars or default
        pass

    return git_info


def get_ec2_metadata():
    """
    Attempt to read real AWS EC2 IMDSv2 metadata.
    Returns structured data with clear indication if running on EC2 or local.
    """
    ec2_info = {
        'is_ec2': False,
        'status': 'UNCONFIGURED (Local Host)',
        'instance_id': None,
        'instance_type': None,
        'availability_zone': None,
        'region': Config.AWS_REGION,
        'private_ip': socket.gethostbyname(socket.gethostname()) if socket.gethostname() else '127.0.0.1',
        'public_ip': None,
        'ami_id': None,
        'security_groups': ['sg-default-app (Target: Port 80, 443, 22)'],
        'detection_mode': 'Local / Development'
    }

    try:
        import requests
        # IMDSv2 token request
        token_url = "http://169.254.169.254/latest/api/token"
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": "60"}
        token_resp = requests.put(token_url, headers=headers, timeout=1.0)

        if token_resp.status_code == 200:
            token = token_resp.text
            meta_headers = {"X-aws-ec2-metadata-token": token}
            base_meta = "http://169.254.169.254/latest/meta-data"

            instance_id = requests.get(f"{base_meta}/instance-id", headers=meta_headers, timeout=1.0).text
            instance_type = requests.get(f"{base_meta}/instance-type", headers=meta_headers, timeout=1.0).text
            az = requests.get(f"{base_meta}/placement/availability-zone", headers=meta_headers, timeout=1.0).text
            local_ip = requests.get(f"{base_meta}/local-ipv4", headers=meta_headers, timeout=1.0).text
            ami_id = requests.get(f"{base_meta}/ami-id", headers=meta_headers, timeout=1.0).text

            try:
                public_ip = requests.get(f"{base_meta}/public-ipv4", headers=meta_headers, timeout=1.0).text
            except Exception:
                public_ip = 'No Public IP'

            ec2_info.update({
                'is_ec2': True,
                'status': 'LIVE (AWS EC2 Instance Active)',
                'instance_id': instance_id,
                'instance_type': instance_type,
                'availability_zone': az,
                'region': az[:-1] if az else Config.AWS_REGION,
                'private_ip': local_ip,
                'public_ip': public_ip,
                'ami_id': ami_id,
                'detection_mode': 'AWS IMDSv2 Verified'
            })
    except Exception:
        # Not on AWS EC2 or IMDS disabled
        pass

    return ec2_info


def get_jenkins_status():
    """
    Detect Jenkins pipeline status from environment variables or active build triggers.
    Distinguishes live Jenkins agent environment from unconfigured local states.
    """
    is_live = bool(Config.BUILD_NUMBER or Config.BUILD_ID)
    status = 'CONNECTED / PIPELINE TRIGGERED' if is_live else 'STANDBY / NOT IN JENKINS RUNNER'

    return {
        'is_live': is_live,
        'status': status,
        'build_number': Config.BUILD_NUMBER if Config.BUILD_NUMBER else 'N/A (Local Dev)',
        'build_id': Config.BUILD_ID if Config.BUILD_ID else 'None',
        'build_url': Config.BUILD_URL if Config.BUILD_URL else 'Not Connected',
        'job_name': Config.JENKINS_JOB_NAME,
        'jenkins_server_url': Config.JENKINS_URL if Config.JENKINS_URL else 'http://jenkins-server:8080 (Configurable)',
        'pipeline_stages': [
            {'name': 'Checkout', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'GitHub clone'},
            {'name': 'Build', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'Virtualenv & Dependencies'},
            {'name': 'Test', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'Pytest & Health Check'},
            {'name': 'Backup', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'S3 Snapshot Archive'},
            {'name': 'Deploy', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'EC2 Gunicorn Reload'},
            {'name': 'Verify', 'status': 'SUCCESS' if is_live else 'PENDING', 'description': 'Smoke & Health Check'}
        ]
    }


def get_s3_status():
    """
    Inspect S3 backup configuration and connectivity.
    Attempts to list objects using boto3 if configured, or gracefully reports unconfigured.
    """
    bucket_name = Config.S3_BUCKET_NAME
    result = {
        'bucket_name': bucket_name or 'Not Configured (Set S3_BUCKET_NAME)',
        'region': Config.AWS_REGION,
        'is_configured': bool(bucket_name),
        'is_connected': False,
        'status': 'UNCONFIGURED' if not bucket_name else 'READY',
        'backups': [],
        'backup_count': 0,
        'latest_backup': 'None',
        'error': None
    }

    if not bucket_name:
        result['status'] = 'UNCONFIGURED (Set S3_BUCKET_NAME in environment)'
        return result

    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError

        s3 = boto3.client('s3', region_name=Config.AWS_REGION)
        # Attempt listing objects under backups/
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='backups/', MaxKeys=20)
        backups = []
        if 'Contents' in response:
            for item in sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True):
                backups.append({
                    'key': item['Key'],
                    'filename': item['Key'].split('/')[-1],
                    'size_bytes': item['Size'],
                    'size_kb': round(item['Size'] / 1024, 2),
                    'last_modified': item['LastModified'].strftime('%Y-%m-%d %H:%M:%S UTC')
                })

        result.update({
            'is_connected': True,
            'status': 'LIVE (S3 Bucket Connected)',
            'backups': backups,
            'backup_count': len(backups),
            'latest_backup': backups[0]['last_modified'] if backups else 'No backups found yet'
        })
    except NoCredentialsError:
        result.update({
            'status': 'CREDENTIALS_MISSING (Attach EC2 IAM Role or AWS keys)',
            'error': 'AWS credentials not discovered in environment or IAM instance profile.'
        })
    except Exception as e:
        result.update({
            'status': 'CONNECTION_ERROR',
            'error': str(e)
        })

    return result


def get_system_metrics():
    """
    Get detailed host system resources (CPU, Memory, Disk, Uptime, OS).
    Uses psutil if available, otherwise falls back to standard library.
    """
    uptime_sec = int(time.time() - START_TIME)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    minutes = (uptime_sec % 3600) // 60
    seconds = uptime_sec % 60
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

    metrics = {
        'os': f"{platform.system()} {platform.release()}",
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'hostname': socket.gethostname(),
        'uptime_seconds': uptime_sec,
        'uptime_formatted': uptime_str,
        'cpu_count': os.cpu_count() or 1,
        'cpu_percent': 0.0,
        'memory_total_gb': 0.0,
        'memory_used_gb': 0.0,
        'memory_percent': 0.0,
        'disk_total_gb': 0.0,
        'disk_used_gb': 0.0,
        'disk_percent': 0.0,
        'metrics_source': 'standard_library'
    }

    try:
        import psutil
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/') if platform.system() != 'Windows' else psutil.disk_usage('C:\\')
        cpu = psutil.cpu_percent(interval=None)

        metrics.update({
            'cpu_percent': round(cpu, 1),
            'memory_total_gb': round(mem.total / (1024 ** 3), 2),
            'memory_used_gb': round(mem.used / (1024 ** 3), 2),
            'memory_percent': mem.percent,
            'disk_total_gb': round(disk.total / (1024 ** 3), 2),
            'disk_used_gb': round(disk.used / (1024 ** 3), 2),
            'disk_percent': disk.percent,
            'metrics_source': 'psutil'
        })
    except ImportError:
        pass
    except Exception:
        pass

    return metrics

