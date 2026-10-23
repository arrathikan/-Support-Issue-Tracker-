import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory and project root are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# We will test using an isolated temporary SQLite database file
@pytest.fixture(autouse=True)
def test_db_setup(monkeypatch, tmp_path):
    test_db_file = tmp_path / "test_issues.db"
    monkeypatch.setenv("DATABASE_PATH", str(test_db_file))
    
    # Import app and ensure DB is initialized
    import main as main_mod
    main_mod.DB_PATH = str(test_db_file)
    main_mod.init_db(str(test_db_file))
    
    yield test_db_file


def get_client():
    import main as main_mod
    return TestClient(main_mod.app)



def test_create_issue_success():
    client = get_client()
    payload = {
        "client_name": "  Acme Corp  ",
        "title": "  Login button unresponsive  ",
        "description": "  Clicking submit does nothing on Safari  ",
        "priority": "High",
        "status": "Open",
    }
    response = client.post("/issues", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["client_name"] == "Acme Corp"  # trimmed
    assert data["title"] == "Login button unresponsive"  # trimmed
    assert data["description"] == "Clicking submit does nothing on Safari"  # trimmed
    assert data["priority"] == "High"
    assert data["status"] == "Open"
    assert "reported_at" in data
    # Verify reported_at contains UTC timezone info (+00:00 or Z)
    assert "+00:00" in data["reported_at"] or "Z" in data["reported_at"]


def test_list_issues():
    client = get_client()
    # Initially empty or with created
    res1 = client.get("/issues")
    assert res1.status_code == 200
    initial_count = len(res1.json())

    # Create two fictional issues
    client.post("/issues", json={
        "client_name": "Globex Corp",
        "title": "Invoice generation error",
        "description": "PDF generation timed out after 30 seconds",
        "priority": "Medium",
        "status": "Open",
    })
    client.post("/issues", json={
        "client_name": "Initech LLC",
        "title": "Printer connectivity failure",
        "description": "Office printer paper jam notification incorrect",
        "priority": "Low",
        "status": "In Progress",
    })

    res2 = client.get("/issues")
    assert res2.status_code == 200
    issues = res2.json()
    assert len(issues) == initial_count + 2
    assert issues[-2]["client_name"] == "Globex Corp"
    assert issues[-1]["client_name"] == "Initech LLC"


def test_get_issue_by_id_and_missing_id():
    client = get_client()
    # Missing ID returns 404
    missing_res = client.get("/issues/99999")
    assert missing_res.status_code == 404
    assert "not found" in missing_res.json()["detail"].lower()

    # Create issue and retrieve it
    create_res = client.post("/issues", json={
        "client_name": "Soylent Corp",
        "title": "Data export CSV missing headers",
        "description": "Column names are blank in exported CSV",
        "priority": "Low",
        "status": "Open",
    })
    issue_id = create_res.json()["id"]

    get_res = client.get(f"/issues/{issue_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == issue_id
    assert get_res.json()["client_name"] == "Soylent Corp"


def test_update_issue_and_preserve_id_and_reported_at():
    client = get_client()
    create_res = client.post("/issues", json={
        "client_name": "Wayne Enterprises",
        "title": "Server fan warning",
        "description": "High temperature alert in rack 4",
        "priority": "Medium",
        "status": "Open",
    })
    created = create_res.json()
    issue_id = created["id"]
    original_reported_at = created["reported_at"]

    update_payload = {
        "client_name": "Wayne Enterprises Ltd",
        "title": "Server fan warning resolved",
        "description": "Replaced fan unit; temperatures normalized",
        "priority": "Low",
        "status": "Resolved",
    }
    update_res = client.put(f"/issues/{issue_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.json()

    assert updated["id"] == issue_id
    assert updated["client_name"] == "Wayne Enterprises Ltd"
    assert updated["title"] == "Server fan warning resolved"
    assert updated["description"] == "Replaced fan unit; temperatures normalized"
    assert updated["priority"] == "Low"
    assert updated["status"] == "Resolved"
    # Preserved reported_at!
    assert updated["reported_at"] == original_reported_at


def test_status_changes():
    client = get_client()
    create_res = client.post("/issues", json={
        "client_name": "Stark Industries",
        "title": "Telemetry latency spike",
        "description": "Telemetry ping increased to 250ms",
        "priority": "High",
        "status": "Open",
    })
    issue_id = create_res.json()["id"]

    # Change to In Progress
    res_in_progress = client.put(f"/issues/{issue_id}", json={"status": "In Progress"})
    assert res_in_progress.status_code == 200
    assert res_in_progress.json()["status"] == "In Progress"

    # Change to Resolved
    res_resolved = client.put(f"/issues/{issue_id}", json={"status": "Resolved"})
    assert res_resolved.status_code == 200
    assert res_resolved.json()["status"] == "Resolved"


def test_delete_issue():
    client = get_client()
    create_res = client.post("/issues", json={
        "client_name": "Cyberdyne Systems",
        "title": "Deprecation warning in build",
        "description": "Build log has obsolete API flag",
        "priority": "Low",
        "status": "Resolved",
    })
    issue_id = create_res.json()["id"]

    del_res = client.delete(f"/issues/{issue_id}")
    assert del_res.status_code == 200
    assert del_res.json()["id"] == issue_id

    # Verify subsequent GET returns 404
    get_res = client.get(f"/issues/{issue_id}")
    assert get_res.status_code == 404

    # Verify subsequent DELETE returns 404
    del_again_res = client.delete(f"/issues/{issue_id}")
    assert del_again_res.status_code == 404


def test_validation_errors():
    client = get_client()

    # Empty / whitespace client_name
    r1 = client.post("/issues", json={
        "client_name": "   ",
        "title": "Valid Title",
        "description": "Valid Description",
        "priority": "Low",
    })
    assert r1.status_code == 422

    # Empty / whitespace title
    r2 = client.post("/issues", json={
        "client_name": "Valid Client",
        "title": "   ",
        "description": "Valid Description",
        "priority": "Low",
    })
    assert r2.status_code == 422

    # Empty / whitespace description
    r3 = client.post("/issues", json={
        "client_name": "Valid Client",
        "title": "Valid Title",
        "description": "\n\t  ",
        "priority": "Low",
    })
    assert r3.status_code == 422

    # Invalid priority
    r4 = client.post("/issues", json={
        "client_name": "Valid Client",
        "title": "Valid Title",
        "description": "Valid Description",
        "priority": "Urgent",  # Invalid
    })
    assert r4.status_code == 422

    # Invalid status
    r5 = client.post("/issues", json={
        "client_name": "Valid Client",
        "title": "Valid Title",
        "description": "Valid Description",
        "priority": "High",
        "status": "Closed",  # Invalid (must be Open, In Progress, Resolved)
    })
    assert r5.status_code == 422


def test_update_missing_id():
    client = get_client()
    res = client.put("/issues/88888", json={"title": "New Title"})
    assert res.status_code == 404


def test_persistence_across_backend_restart(tmp_path):
    import main as main_mod

    db_file = tmp_path / "persistent_restart_test.db"
    main_mod.DB_PATH = str(db_file)
    main_mod.init_db(str(db_file))

    # Phase 1: create issue
    client1 = TestClient(main_mod.app)
    create_res = client1.post("/issues", json={
        "client_name": "Hooli Corp",
        "title": "Video compression artifact",
        "description": "Middle-out algorithm dropped keyframe 42",
        "priority": "High",
        "status": "In Progress",
    })
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]
    created_timestamp = create_res.json()["reported_at"]

    # Phase 2: Simulate complete backend shutdown & restart
    # Reset app context and re-initialize pointing to the exact same persistent file
    main_mod.DB_PATH = str(db_file)
    main_mod.init_db(str(db_file))
    client2 = TestClient(main_mod.app)

    # Phase 3: Verify data survived
    get_res = client2.get(f"/issues/{created_id}")
    assert get_res.status_code == 200
    issue_data = get_res.json()
    assert issue_data["id"] == created_id
    assert issue_data["client_name"] == "Hooli Corp"
    assert issue_data["title"] == "Video compression artifact"
    assert issue_data["description"] == "Middle-out algorithm dropped keyframe 42"
    assert issue_data["priority"] == "High"
    assert issue_data["status"] == "In Progress"
    assert issue_data["reported_at"] == created_timestamp
