# Support Issue Tracker

A full-stack support issue tracking application built for a 60-minute technical assessment.

- **Frontend**: React 19, Vite, Plain CSS, and native `fetch()`.
- **Backend**: Python 3, FastAPI, and Pydantic v2.
- **Database**: SQLite via Python's built-in `sqlite3` module.
- **Repository**: [https://github.com/arrathikan/-Support-Issue-Tracker-.git](https://github.com/arrathikan/-Support-Issue-Tracker-.git)

---

## 1. Project Purpose & Architecture

The **Support Issue Tracker** enables support engineering teams to create, view, edit, search, filter, and resolve client support issues.

```
┌─────────────────────────────────┐
│     React 19 Frontend (Vite)    │
│    http://localhost:5173        │
└────────────────┬────────────────┘
                 │ HTTP / JSON (fetch) + CORS
┌────────────────▼────────────────┐
│      FastAPI Backend API        │
│     http://127.0.0.1:8000       │
└────────────────┬────────────────┘
                 │ Parameterized SQL queries
┌────────────────▼────────────────┐
│     SQLite Persistent Storage   │
│       backend/issues.db         │
└─────────────────────────────────┘
```

### Why SQLite Suits this Local Assessment
1. **Zero External Daemon Dependencies**: Runs in-process via Python's standard `sqlite3` library without configuring external server processes (e.g., PostgreSQL or MySQL).
2. **True File-Based Persistence**: Issues survive backend process restarts and shutdown events because records are committed to `backend/issues.db`.
3. **Automated Schema Provisioning**: The `issues` table is created automatically on backend initialization if it does not already exist.
4. **ACID Compliance & Parameterized SQL**: Guarantees transaction safety and full injection protection using standard SQL parameterized queries.

---

## 2. Prerequisites

- **Python**: 3.10+ (tested on Python 3.13)
- **Node.js**: 18+ (tested on Node v22.15)
- **npm**: 9+ (tested on npm 10.9)

---

## 3. Installation & Startup Commands

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start the FastAPI development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Backend Base URL**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Frontend Setup

In a new terminal window:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Start the Vite development server
npm run dev
```

- **Frontend Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 4. API Endpoints

| Method | Endpoint | Description | Request Body / Params | Status Codes |
|---|---|---|---|---|
| `GET` | `/` | API health check & index | None | `200` |
| `GET` | `/issues` | List all issues (ordered by ID ascending) | None | `200` |
| `GET` | `/issues/{id}` | Retrieve a single issue by unique ID | None | `200`, `404` |
| `POST` | `/issues` | Create a new issue | `client_name`, `title`, `description`, `priority`, `status` | `201`, `422` |
| `PUT` | `/issues/{id}` | Update editable fields (preserves ID & timestamp) | `client_name`, `title`, `description`, `priority`, `status` | `200`, `404`, `422` |
| `DELETE` | `/issues/{id}` | Delete an issue | None | `200`, `404` |

---

## 5. Database Schema & Persistence

- **Database File Location**: `backend/issues.db` (auto-created on startup, excluded from git).
- **Auto-Initialization**: Handled through FastAPI `lifespan` executing `CREATE TABLE IF NOT EXISTS issues (...)`.

```sql
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,       -- 'Low' | 'Medium' | 'High'
    status TEXT NOT NULL,         -- 'Open' | 'In Progress' | 'Resolved'
    reported_at TEXT NOT NULL     -- ISO-8601 UTC timestamp
);
```

- **Immutability on Edit**: When updating an issue via `PUT /issues/{id}`, the original `id` and `reported_at` values are strictly preserved.

---

## 6. Overdue Highlighting Rules

An issue is highlighted with a red accent and an **Overdue** label strictly when all three criteria are met:
1. `priority === 'High'`
2. `status !== 'Resolved'` (i.e. `Open` or `In Progress`)
3. `reported_at` is strictly greater than 24 hours ago: `(Date.now() - reportedDate) > 24 * 60 * 60 * 1000`.

Resolving the ticket (`status === 'Resolved'`) immediately clears the overdue flag.

---

## 7. Running the Automated Tests

### Backend Test Suite

The backend test suite uses `pytest` and FastAPI `TestClient` to test all CRUD operations, data validation, status changes, 404 responses, and restart persistence across isolated SQLite database instances:

```bash
cd backend
source venv/bin/activate
pytest -v
```

### Frontend Overdue & Utility Test Suite

The frontend test suite tests boundary conditions, timestamp conversions, status transitions, and overdue calculations:

```bash
cd frontend
npm test
```

### Production Build Validation

```bash
cd frontend
npm run build
```

---

## 8. Test Results & Verification Summary

### Automated Test Runs
- **Backend Tests (`backend/test_main.py` + `backend/test_e2e_core.py`)**:
  - `test_create_issue_success`: PASSED
  - `test_list_issues`: PASSED
  - `test_get_issue_by_id_and_missing_id`: PASSED
  - `test_update_issue_and_preserve_id_and_reported_at`: PASSED
  - `test_status_changes`: PASSED
  - `test_delete_issue`: PASSED
  - `test_validation_errors`: PASSED
  - `test_update_missing_id`: PASSED
  - `test_persistence_across_backend_restart`: PASSED
  - `test_core_lifecycle_and_persistence`: PASSED
  - `test_blank_fields_and_invalid_inputs`: PASSED
  - **Result**: `11 passed in 0.80s`

- **Frontend Tests (`frontend/test_overdue.js`)**:
  - Case 1: High, Open, 25h old is highlighted: PASSED
  - Case 2: High, In Progress, 25h old is highlighted: PASSED
  - Case 3: High, Resolved, 25h old is NOT highlighted: PASSED
  - Case 4: Medium, Open, 25h old is NOT highlighted: PASSED
  - Case 5: High, Open, 23h old is NOT highlighted: PASSED
  - Boundary: Exactly 24.0h old is NOT highlighted: PASSED
  - Boundary: 24h + 1s IS highlighted (strictly > 24h): PASSED
  - Transition: Resolving overdue issue removes highlight: PASSED
  - Formatting: ISO UTC to local timezone string: PASSED
  - **Result**: `All 8 checks passed`

### Browser Verification
- Tested with browser agent against live FastAPI and Vite instances:
  - Error recovery on backend disconnect and reconnection via Retry button.
  - Case-insensitive search (`acme`, `ACME`, `gateway`).
  - Single and multi-filters (Priority + Status).
  - Client-side validation prevents submission of blank/whitespace fields.
  - Interactive editing and status transitions (`Open` -> `In Progress` -> `Resolved`).
  - Deletion with browser confirmation dialog.

### Known Limitations
- The application is optimized for single-node / local assessment deployment.
- Authentication and role-based access control are omitted as specified by assessment guidelines.
