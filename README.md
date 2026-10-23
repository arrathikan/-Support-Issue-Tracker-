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
   - Search and both filters work simultaneously.
4. **Overdue Highlighting**:
   - Automatically highlights tickets with a red accent and an `Overdue` badge when:
     - `priority === 'High'`
     - `status !== 'Resolved'`
     - `reported_at` is strictly more than 24 hours ago.
5. **Local Timezone Display**:
   - Formats UTC ISO timestamps into the user's local date and time string, with the exact UTC timestamp accessible in tooltips.

---

## Getting Started

### 1. Start the Backend

```bash
cd backend
source venv/bin/activate
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
