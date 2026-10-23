import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "issues.db"))

VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Open", "In Progress", "Resolved"}
ENGINEERS = ("Alex Morgan", "Sam Patel", "Jordan Lee")


def normalize_engineer(value: Optional[str]) -> Optional[str]:
    value = value.strip() if value is not None else None
    if not value:
        return None
    if value not in ENGINEERS:
        raise ValueError("Select an engineer from the available engineers")
    return value


def validate_resolution(issue_status: str, engineer: Optional[str]):
    if issue_status == "Resolved" and not engineer:
        raise HTTPException(
            status_code=422,
            detail="Select an Assigned Engineer before marking an issue Resolved",
        )


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    """Create the table and add assignment to existing databases without losing records."""
    db_path = db_path or DB_PATH
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                reported_at TEXT NOT NULL,
                assigned_engineer TEXT
            );
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(issues)")}
        if "assigned_engineer" not in columns:
            conn.execute("ALTER TABLE issues ADD COLUMN assigned_engineer TEXT")
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Support Issue Tracker API",
    description="Backend API for managing support issues with SQLite",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_utc_timestamp() -> str:
    """Generate timezone-aware UTC ISO-formatted timestamp."""
    return datetime.now(timezone.utc).isoformat()


# Pydantic validation models
class IssueCreate(BaseModel):
    client_name: str
    title: str
    description: str
    priority: str = "Medium"
    status: str = "Open"
    assigned_engineer: Optional[str] = None

    @field_validator("assigned_engineer")
    @classmethod
    def validate_engineer(cls, value: Optional[str]) -> Optional[str]:
        return normalize_engineer(value)

    @field_validator("client_name", "title", "description")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty or whitespace only")
        return v.strip()

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        trimmed = v.strip() if isinstance(v, str) else ""
        match = {p.lower(): p for p in VALID_PRIORITIES}.get(trimmed.lower())
        if not match:
            raise ValueError("Priority must be one of: Low, Medium, High")
        return match

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        trimmed = v.strip() if isinstance(v, str) else ""
        match = {s.lower(): s for s in VALID_STATUSES}.get(trimmed.lower())
        if not match:
            raise ValueError("Status must be one of: Open, In Progress, Resolved")
        return match


class IssueUpdate(BaseModel):
    client_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_engineer: Optional[str] = None

    @field_validator("assigned_engineer")
    @classmethod
    def validate_engineer(cls, value: Optional[str]) -> Optional[str]:
        return normalize_engineer(value)

    @field_validator("client_name", "title", "description")
    @classmethod
    def validate_optional_non_empty(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"{info.field_name} must not be empty or whitespace only")
            return v.strip()
        return v

    @field_validator("priority")
    @classmethod
    def validate_optional_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip() if isinstance(v, str) else ""
            match = {p.lower(): p for p in VALID_PRIORITIES}.get(trimmed.lower())
            if not match:
                raise ValueError("Priority must be one of: Low, Medium, High")
            return match
        return v

    @field_validator("status")
    @classmethod
    def validate_optional_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip() if isinstance(v, str) else ""
            match = {s.lower(): s for s in VALID_STATUSES}.get(trimmed.lower())
            if not match:
                raise ValueError("Status must be one of: Open, In Progress, Resolved")
            return match
        return v


class IssueResponse(BaseModel):
    id: int
    client_name: str
    title: str
    description: str
    priority: str
    status: str
    reported_at: str
    assigned_engineer: Optional[str] = None


@app.get("/engineers", response_model=List[str])
def list_engineers():
    """Fictional engineer choices shared by the API and frontend."""
    return list(ENGINEERS)


@app.get("/")
def read_root():
    return {
        "message": "Support Issue Tracker API is running",
        "docs": "/docs",
        "endpoints": ["/issues"],
    }


@app.get("/issues", response_model=List[IssueResponse])
def list_issues():
    """List all support issues ordered by id ascending."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, client_name, title, description, priority, status, reported_at, assigned_engineer
            FROM issues
            ORDER BY id ASC
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.get("/issues/{id}", response_model=IssueResponse)
def get_issue(id: int):
    """Retrieve a single issue by its unique ID."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, client_name, title, description, priority, status, reported_at, assigned_engineer
            FROM issues
            WHERE id = ?
            """,
            (id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {id} not found",
            )
        return dict(row)
    finally:
        conn.close()


@app.post("/issues", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(issue: IssueCreate):
    """Create a new issue with auto-generated ID and timezone-aware UTC reported_at timestamp."""
    validate_resolution(issue.status, issue.assigned_engineer)
    reported_at = get_current_utc_timestamp()
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO issues (client_name, title, description, priority, status, reported_at, assigned_engineer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue.client_name,
                issue.title,
                issue.description,
                issue.priority,
                issue.status,
                reported_at,
                issue.assigned_engineer,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {
            "id": new_id,
            "client_name": issue.client_name,
            "title": issue.title,
            "description": issue.description,
            "priority": issue.priority,
            "status": issue.status,
            "reported_at": reported_at,
            "assigned_engineer": issue.assigned_engineer,
        }
    finally:
        conn.close()


@app.put("/issues/{id}", response_model=IssueResponse)
def update_issue(id: int, issue: IssueUpdate):
    """
    Update editable fields of an issue (client_name, title, description, priority, status).
    Preserves original id and reported_at.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, client_name, title, description, priority, status, reported_at, assigned_engineer
            FROM issues
            WHERE id = ?
            """,
            (id,),
        )
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {id} not found",
            )

        # Merge existing values with updated fields
        updated_client_name = (
            issue.client_name if issue.client_name is not None else existing["client_name"]
        )
        updated_title = (
            issue.title if issue.title is not None else existing["title"]
        )
        updated_description = (
            issue.description if issue.description is not None else existing["description"]
        )
        updated_priority = (
            issue.priority if issue.priority is not None else existing["priority"]
        )
        updated_status = (
            issue.status if issue.status is not None else existing["status"]
        )
        updated_engineer = (
            issue.assigned_engineer
            if "assigned_engineer" in issue.model_fields_set
            else existing["assigned_engineer"]
        )
        # Validate the merged record: omitted assignment keeps its existing value,
        # while explicit null clears it only when the result is not Resolved.
        validate_resolution(updated_status, updated_engineer)

        cursor.execute(
            """
            UPDATE issues
            SET client_name = ?, title = ?, description = ?, priority = ?, status = ?, assigned_engineer = ?
            WHERE id = ?
            """,
            (
                updated_client_name,
                updated_title,
                updated_description,
                updated_priority,
                updated_status,
                updated_engineer,
                id,
            ),
        )
        conn.commit()

        return {
            "id": id,
            "client_name": updated_client_name,
            "title": updated_title,
            "description": updated_description,
            "priority": updated_priority,
            "status": updated_status,
            "reported_at": existing["reported_at"],
            "assigned_engineer": updated_engineer,
        }
    finally:
        conn.close()


@app.delete("/issues/{id}")
def delete_issue(id: int):
    """Delete an issue by ID. Returns 404 if not found."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM issues WHERE id = ?", (id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue with ID {id} not found",
            )

        cursor.execute("DELETE FROM issues WHERE id = ?", (id,))
        conn.commit()
        return {"message": f"Issue {id} deleted successfully", "id": id}
    finally:
        conn.close()
