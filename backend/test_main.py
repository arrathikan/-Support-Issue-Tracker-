import os
import sqlite3
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
        "assigned_engineer": "Alex Morgan",
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
    res_resolved = client.put(f"/issues/{issue_id}", json={
        "status": "Resolved", "assigned_engineer": "Sam Patel"
    })
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
        "assigned_engineer": "Jordan Lee",
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
        "assigned_engineer": "Sam Patel",
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
    assert issue_data["assigned_engineer"] == "Sam Patel"


def assignment_payload(**overrides):
    return {
        "client_name": "Fictional Demo Client",
        "title": "Assignment regression",
        "description": "Fictional issue for assignment checks",
        "priority": "High",
        "status": "Open",
        **overrides,
    }


def test_engineer_choices_and_assigned_issue_round_trip():
    client = get_client()
    engineers = client.get("/engineers")
    assert engineers.status_code == 200
    assert engineers.json() == ["Alex Morgan", "Sam Patel", "Jordan Lee"]
    response = client.post("/issues", json=assignment_payload(assigned_engineer="  Alex Morgan  "))
    assert response.status_code == 201
    created = response.json()
    assert created["assigned_engineer"] == "Alex Morgan"
    assert client.get(f"/issues/{created['id']}").json() == created
    assert client.get("/issues").json() == [created]


@pytest.mark.parametrize("engineer", [None, "", "   "])
@pytest.mark.parametrize("issue_status", ["Open", "In Progress", "Resolved"])
def test_unassigned_create_rules(engineer, issue_status):
    client = get_client()
    response = client.post("/issues", json=assignment_payload(
        assigned_engineer=engineer, status=issue_status
    ))
    assert response.status_code == (422 if issue_status == "Resolved" else 201)
    if issue_status == "Resolved":
        assert client.get("/issues").json() == []
    else:
        assert response.json()["assigned_engineer"] is None


def test_direct_api_cannot_resolve_without_engineer():
    client = get_client()
    assert client.post("/issues", json=assignment_payload(status="Resolved")).status_code == 422
    created = client.post("/issues", json=assignment_payload()).json()
    response = client.put(f"/issues/{created['id']}", json={"status": "resolved"})
    assert response.status_code == 422
    assert "Assigned Engineer" in response.json()["detail"]
    assert client.get(f"/issues/{created['id']}").json() == created


def test_assign_resolve_preserve_and_reassign():
    client = get_client()
    created = client.post("/issues", json=assignment_payload()).json()
    url = f"/issues/{created['id']}"
    assigned = client.put(url, json={"assigned_engineer": "Sam Patel"})
    assert assigned.status_code == 200
    resolved = client.put(url, json={"status": "Resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["assigned_engineer"] == "Sam Patel"
    assert resolved.json()["reported_at"] == created["reported_at"]
    assert resolved.json()["id"] == created["id"]
    reassigned = client.put(url, json={"assigned_engineer": "Jordan Lee", "title": "Updated"})
    assert reassigned.status_code == 200
    assert reassigned.json()["status"] == "Resolved"
    assert reassigned.json()["assigned_engineer"] == "Jordan Lee"


@pytest.mark.parametrize("empty_engineer", [None, "", "  "])
def test_cannot_clear_assignment_while_resolved(empty_engineer):
    client = get_client()
    created = client.post("/issues", json=assignment_payload(
        status="Resolved", assigned_engineer="Alex Morgan"
    )).json()
    url = f"/issues/{created['id']}"
    response = client.put(url, json={"assigned_engineer": empty_engineer, "title": "Must not save"})
    assert response.status_code == 422
    assert client.get(url).json() == created
    reopened = client.put(url, json={"status": "Open", "assigned_engineer": empty_engineer})
    assert reopened.status_code == 200
    assert reopened.json()["assigned_engineer"] is None


@pytest.mark.parametrize("invalid_engineer", ["Unknown Person", 42])
def test_invalid_engineer_is_rejected(invalid_engineer):
    client = get_client()
    assert client.post("/issues", json=assignment_payload(
        assigned_engineer=invalid_engineer
    )).status_code == 422
    created = client.post("/issues", json=assignment_payload()).json()
    assert client.put(f"/issues/{created['id']}", json={
        "assigned_engineer": invalid_engineer
    }).status_code == 422


def test_legacy_database_migration_preserves_records_and_is_repeatable(tmp_path, monkeypatch):
    import main as main_mod

    legacy_db = tmp_path / "legacy.db"
    timestamp = "2026-10-20T12:00:00+00:00"
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("""CREATE TABLE issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT NOT NULL,
            title TEXT NOT NULL, description TEXT NOT NULL, priority TEXT NOT NULL,
            status TEXT NOT NULL, reported_at TEXT NOT NULL
        )""")
        conn.execute("INSERT INTO issues VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (17, "Legacy Demo", "Old issue", "Keep this record", "High", "Open", timestamp))
    monkeypatch.setattr(main_mod, "DB_PATH", str(legacy_db))
    # Starting the application migrates the old table; starting again is safe.
    with TestClient(main_mod.app) as client:
        record = client.get("/issues/17").json()
        assert record["id"] == 17
        assert record["reported_at"] == timestamp
        assert record["description"] == "Keep this record"
        assert record["assigned_engineer"] is None
        response = client.put("/issues/17", json={
            "status": "Resolved", "assigned_engineer": "Alex Morgan"
        })
        assert response.status_code == 200
    with TestClient(main_mod.app) as client:
        assert client.get("/issues/17").json() == response.json()
