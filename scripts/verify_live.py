"""
Live Server Smoke Test Script
Starts Flask app in a background thread and probes all required endpoints.
"""

import sys
import time
import requests
from threading import Thread
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app
from config.settings import Config

def run_server():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def test_endpoints():
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server a moment to start

    base_url = "http://127.0.0.1:5000"
    endpoints = [
        ("/", 200, "text/html"),
        ("/health", 200, "application/json"),
        ("/api/status", 200, "application/json"),
        ("/api/deployments", 200, "application/json"),
        ("/api/system-info", 200, "application/json"),
        ("/api/backups", 200, "application/json"),
        ("/deployments", 200, "text/html"),
        ("/infrastructure", 200, "text/html"),
        ("/documentation", 200, "text/html"),
    ]

    print("=" * 60)
    print("STARTING LIVE SERVER SMOKE VERIFICATION")
    print("=" * 60)

    all_passed = True
    for path, expected_status, expected_content_type in endpoints:
        url = f"{base_url}{path}"
        try:
            resp = requests.get(url, timeout=3)
            status_match = (resp.status_code == expected_status)
            content_type_match = expected_content_type in resp.headers.get("Content-Type", "")
            
            if status_match and content_type_match:
                print(f"[PASS] {path:<20} -> HTTP {resp.status_code} ({resp.headers.get('Content-Type')})")
            else:
                print(f"[FAIL] {path:<20} -> Got HTTP {resp.status_code}, expected {expected_status}")
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {path:<20} -> {e}")
            all_passed = False

    # Also test POST to /api/deployments
    try:
        post_resp = requests.post(
            f"{base_url}/api/deployments",
            json={"details": "Live Smoke Test Verification", "branch": "main", "status": "SUCCESS"},
            timeout=3
        )
        if post_resp.status_code == 201 and "record" in post_resp.json():
            print(f"[PASS] {'POST /api/deployments':<20} -> HTTP 201 Created (Audit recorded)")
        else:
            print(f"[FAIL] POST /api/deployments -> HTTP {post_resp.status_code}")
            all_passed = False
    except Exception as e:
        print(f"[ERROR] POST /api/deployments -> {e}")
        all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL ENDPOINTS LIVE AND VERIFIED SUCCESSFULLY!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("SOME ENDPOINTS FAILED VERIFICATION.")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    test_endpoints()
