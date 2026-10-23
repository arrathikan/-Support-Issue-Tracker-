import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import main as app_main


@pytest.fixture
def isolated_db(tmp_path):
    """Sets up an isolated temporary database for safe testing without touching user data."""
    test_db = tmp_path / "e2e_isolated.db"
    orig_path = app_main.DB_PATH
    app_main.DB_PATH = str(test_db)
    app_main.init_db(str(test_db))
    yield str(test_db)
    app_main.DB_PATH = orig_path


def test_core_lifecycle_and_persistence(isolated_db):
    """
    Tests:
    1. Create an issue and verify generated ID and UTC reported timestamp.
    2. Refresh/get and verify issue remains.
    3. Restart backend and verify issue remains.
    4. Edit issue and verify ID and original timestamp remain unchanged.
    5. Change between Open, In Progress and Resolved.
    6. Deletion: issue removed after DELETE request.
    """
    client = TestClient(app_main.app)

    # 1. Create issue
    payload = {
        "client_name": "Stark Industries",
        "title": "Arc reactor power fluctuation",
        "description": "Output dipped below 95% efficiency",
        "priority": "High",
        "status": "Open",
    }
    create_res = client.post("/issues", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    issue_id = created["id"]
    original_reported_at = created["reported_at"]

    assert issue_id > 0
    assert "+00:00" in original_reported_at or "Z" in original_reported_at

    # 2. Get issue (simulate page refresh / data reload)
    get_res = client.get(f"/issues/{issue_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Arc reactor power fluctuation"

    # 3. Simulate backend restart
    app_main.init_db(isolated_db)
    client_restarted = TestClient(app_main.app)
    restart_res = client_restarted.get(f"/issues/{issue_id}")
    assert restart_res.status_code == 200
    assert restart_res.json()["id"] == issue_id
    assert restart_res.json()["reported_at"] == original_reported_at

    # 4. Edit issue: ID and original reported_at must remain unchanged
    update_res = client_restarted.put(f"/issues/{issue_id}", json={
        "client_name": "Stark Industries Global",
        "title": "Arc reactor stabilized",
        "description": "Firmware patch applied successfully",
        "priority": "Medium",
        "status": "In Progress",
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["id"] == issue_id
    assert updated["reported_at"] == original_reported_at  # UNCHANGED!
    assert updated["status"] == "In Progress"

    # 5. Status transitions: In Progress -> Resolved
    resolve_res = client_restarted.put(f"/issues/{issue_id}", json={"status": "Resolved"})
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "Resolved"
    assert resolve_res.json()["reported_at"] == original_reported_at

    # 6. Deletion
    del_res = client_restarted.delete(f"/issues/{issue_id}")
    assert del_res.status_code == 200

    # Verify issue is removed
    get_del_res = client_restarted.get(f"/issues/{issue_id}")
    assert get_del_res.status_code == 404


def test_blank_fields_and_invalid_inputs(isolated_db):
    """
    Tests rejection of blank required fields and invalid status/priority values.
    """
    client = TestClient(app_main.app)

    # Blank client_name
    r1 = client.post("/issues", json={"client_name": "  ", "title": "Valid", "description": "Valid"})
    assert r1.status_code == 422

    # Blank title
    r2 = client.post("/issues", json={"client_name": "Valid", "title": "   ", "description": "Valid"})
    assert r2.status_code == 422

    # Blank description
    r3 = client.post("/issues", json={"client_name": "Valid", "title": "Valid", "description": "   "})
    assert r3.status_code == 422

    # Invalid priority
    r4 = client.post("/issues", json={"client_name": "Valid", "title": "Valid", "description": "Valid", "priority": "Extreme"})
    assert r4.status_code == 422

    # Invalid status
    r5 = client.post("/issues", json={"client_name": "Valid", "title": "Valid", "description": "Valid", "status": "Abandoned"})
    assert r5.status_code == 422
