# Support Issue Tracker

A support issue tracking application built with a FastAPI + SQLite backend and a React (Vite) frontend.

## Backend Architecture

- **Framework**: FastAPI
- **Database**: SQLite via Python's built-in `sqlite3` module
- **Validation**: Pydantic v2
- **CORS**: Configured for `http://localhost:5173` and `http://127.0.0.1:5173`

### Data Schema (`issues` table)

| Field | Type | Description |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique identifier |
| `client_name` | TEXT | Client or organization name (trimmed, non-empty) |
| `title` | TEXT | Issue summary (trimmed, non-empty) |
| `description` | TEXT | Detailed description (trimmed, non-empty) |
| `priority` | TEXT | `Low`, `Medium`, or `High` |
| `status` | TEXT | `Open`, `In Progress`, or `Resolved` |
| `reported_at` | TEXT | Timezone-aware UTC timestamp (ISO 8601) |

### API Endpoints

- `GET /` — API health check and index
- `GET /issues` — List all support issues
- `GET /issues/{id}` — Retrieve a single issue by ID (404 if not found)
- `POST /issues` — Create a new issue (returns 201 with auto-generated ID and UTC timestamp)
- `PUT /issues/{id}` — Update editable fields (`client_name`, `title`, `description`, `priority`, `status`) while preserving `id` and `reported_at`
- `DELETE /issues/{id}` — Delete an issue by ID (404 if not found)

### Interactive Documentation

Once the server is running, explore the Swagger UI documentation at:
- **Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Setup & Running the Backend

### 1. Create and Activate Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Automated Checks

```bash
pytest test_main.py -v
```

### 4. Start the Development Server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
