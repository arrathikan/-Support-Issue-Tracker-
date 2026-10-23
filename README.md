# Support Issue Tracker

A support issue tracking application built with a **FastAPI + SQLite** backend and a **React (Vite) + Plain CSS** frontend.

## Architecture

- **Backend**: FastAPI with Python's built-in `sqlite3` module.
- **Frontend**: React 18+ with Vite, Vanilla CSS, and native `fetch()`.
- **Database**: Persistent SQLite (`backend/issues.db`).
- **CORS**: Configured for `http://localhost:5173`.

---

## Data Schema (`issues` table)

| Field | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Automatically generated unique ID |
| `client_name` | TEXT | Client or organization name (trimmed, non-empty) |
| `title` | TEXT | Issue summary (trimmed, non-empty) |
| `description` | TEXT | Detailed description (trimmed, non-empty) |
| `priority` | TEXT | `Low`, `Medium`, or `High` |
| `status` | TEXT | `Open`, `In Progress`, or `Resolved` |
| `reported_at` | TEXT | Timezone-aware UTC timestamp (ISO 8601) |
| `assigned_engineer` | TEXT, nullable | Selected fictional engineer, or null for Unassigned |

---

## Features

1. **Issue Creation & Validation**:
   - Form fields: Client Name, Issue Title, Description, Priority (`Low`, `Medium`, `High`), and Status (`Open`, `In Progress`, `Resolved`).
   - Client-side and server-side validation rejecting empty or whitespace-only inputs.
   - Disables submit button with loading state while saving.
2. **Issue Management (Edit & Delete)**:
   - Edit issues through the form while strictly preserving the original `id` and `reported_at` timestamp.
   - Confirmation dialog before deletion (`window.confirm()`).
   - Visual success and error banners with dismiss controls.
3. **Search & Multi-Filter**:
   - Case-insensitive search across Client Name **OR** Issue Title.
   - Priority filter dropdown (`All`, `Low`, `Medium`, `High`).
   - Status filter dropdown (`All`, `Open`, `In Progress`, `Resolved`).
   - Assigned Engineer filter (`All Engineers`, `Unassigned`, or a named engineer).
   - Search and all three filters work simultaneously; Reset Filters clears them all.
4. **Overdue Highlighting**:
   - Automatically highlights tickets with a red accent and an `Overdue` badge when:
     - `priority === 'High'`
     - `status !== 'Resolved'`
     - `reported_at` is strictly more than 24 hours ago.
5. **Local Timezone Display**:
   - Formats UTC ISO timestamps into the user's local date and time string, with the exact UTC timestamp accessible in tooltips.
6. **Engineer Assignment**:
   - Select an engineer when creating or editing an issue; the list displays the selection.
   - Open and In Progress issues may remain Unassigned.
   - Resolved requires an Assigned Engineer. Both the form and backend enforce this rule.
   - Clearing assignment from a Resolved issue is rejected unless the same update reopens it.
   - `GET /engineers` supplies the fictional roster: Alex Morgan, Sam Patel and Jordan Lee. Edit `ENGINEERS` in `backend/main.py` to change the demo choices.

### Existing databases

Backend startup automatically adds the nullable assignment column to older databases without deleting or changing issue IDs, timestamps or other fields. Restart the backend after updating the code. Existing records appear as Unassigned. Historical Resolved records retain their status; the next edit must assign an engineer or reopen the issue. Repeated startup is safe.

---

## Getting Started

### 1. Start the Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Run tests: `pytest test_main.py -v`

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```
- Open in browser: [http://localhost:5173](http://localhost:5173)

## Testing the assignment change

From the project root, using the installed backend virtual environment:

```bash
backend/venv/bin/python -m pytest backend/ -v
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend run lint
```

The backend tests cover CRUD, input validation, stable IDs/timestamps, assignment persistence, invalid engineer choices, resolution without assignment, rejected assignment removal, reopening, and migration from the previous database schema. All tests use temporary databases.

Browser regression checklist:

1. Create an Open issue without an engineer; verify Unassigned in its row.
2. Edit it, select an engineer, select Resolved and save; verify both values after refresh.
3. Clear the engineer while leaving status Resolved; verify the error and unchanged saved issue. Reopen it and then verify clearing assignment succeeds.
4. Combine engineer, priority and status filters with a client/title search; verify Reset Filters restores all issues. Check the Unassigned filter too.
5. Verify overdue highlighting still requires High priority, unresolved status and an age strictly greater than 24 hours.
6. Verify required-field errors, editing, delete cancellation/confirmation, loading/error/retry states and small-screen layout.

SQLite remains the persistent source of data. No engineer accounts or login are required for this fictional demonstration.

### Verification results for the assignment change

- Backend: 29 tests passed across `test_main.py` and `test_e2e_core.py`, including lifecycle persistence, validation, and engineer assignment.
- Frontend test suite: 8 tests passed for overdue calculations and local timestamp formatting (`test_overdue.js`).
- Frontend production build: passed.
- Browser: passed checks for creation, assignment, resolution, blocked assignment removal, reopening, combined filters/search, reset, refresh persistence, unchanged timestamp, overdue highlighting, required fields, delete cancellation/confirmation, narrow-screen layout, and backend failure/retry.
- Lint: completed with clean status (oxlint). No new lint warnings were introduced.
