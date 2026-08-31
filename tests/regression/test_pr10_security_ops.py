import subprocess
import sys

from fastapi.testclient import TestClient

from apps.api.main import app


def test_health_check_endpoint_defaults():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert "timestamp" in data
    assert data["live_purchase_enabled"] is False


def test_secret_scan_script_clean():
    # Run the secret scan script directly and ensure it returns 0 findings
    cmd = [sys.executable, "scripts/scan_secrets.py"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "0 credentials or leaked tokens detected" in result.stdout or "[PASS]" in result.stdout

