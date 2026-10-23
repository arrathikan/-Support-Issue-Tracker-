import { useState, useEffect, useMemo } from 'react';
import './App.css';
import { isIssueOverdue, formatLocalTime } from './utils';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [formError, setFormError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Form state
  const [editingId, setEditingId] = useState(null);
  const [clientName, setClientName] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('Medium');
  const [status, setStatus] = useState('Open');

  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  // Load issues when component mounts
  useEffect(() => {
    loadIssues();
  }, []);

  const loadIssues = async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/issues`);
      if (!response.ok) {
        throw new Error(`Failed to load issues (HTTP ${response.status})`);
      }
      const data = await response.json();
      setIssues(data);
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch' || err.name === 'TypeError'
          ? 'Unable to connect to backend server. Please verify that FastAPI is running on http://localhost:8000.'
          : err.message || 'Unable to connect to backend server';
      setFetchError(msg);
    } finally {
      setLoading(false);
    }

  };

  const handleStartEdit = (issue) => {
    setEditingId(issue.id);
    setClientName(issue.client_name);
    setTitle(issue.title);
    setDescription(issue.description);
    setPriority(issue.priority);
    setStatus(issue.status);
    setFormError(null);
    setSuccessMessage(null);
    setActionError(null);

    // Smooth scroll to form
    const formEl = document.getElementById('issue-form-section');
    if (formEl) {
      formEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setClientName('');
    setTitle('');
    setDescription('');
    setPriority('Medium');
    setStatus('Open');
    setFormError(null);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMessage(null);
    setActionError(null);

    // Validate required fields (trimmed)
    const trimmedClientName = clientName.trim();
    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();

    if (!trimmedClientName) {
      setFormError('Client Name is required');
      return;
    }
    if (!trimmedTitle) {
      setFormError('Issue Title is required');
      return;
    }
    if (!trimmedDescription) {
      setFormError('Description is required');
      return;
    }

    setSaving(true);
    try {
      const isEditing = editingId !== null;
      const url = isEditing
        ? `${API_BASE_URL}/issues/${editingId}`
        : `${API_BASE_URL}/issues`;
      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_name: trimmedClientName,
          title: trimmedTitle,
          description: trimmedDescription,
          priority,
          status,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detailMsg =
          typeof errorData.detail === 'string'
            ? errorData.detail
            : Array.isArray(errorData.detail)
            ? errorData.detail.map((d) => d.msg).join(', ')
            : `Failed to ${isEditing ? 'update' : 'create'} issue (HTTP ${response.status})`;
        throw new Error(detailMsg);
      }

      setSuccessMessage(
        isEditing
          ? `Issue #${editingId} updated successfully!`
          : 'Issue created successfully!'
      );

      // Reset form
      handleCancelEdit();

      // Reload issues from backend
      await loadIssues();
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch' || err.name === 'TypeError'
          ? 'Unable to connect to backend server. Please verify that FastAPI is running.'
          : err.message || 'Operation failed';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteIssue = async (issue) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete issue #${issue.id} ("${issue.title}")?`
    );
    if (!confirmed) return;

    setDeletingId(issue.id);
    setActionError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/issues/${issue.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detailMsg =
          typeof errorData.detail === 'string'
            ? errorData.detail
            : `Failed to delete issue #${issue.id} (HTTP ${response.status})`;
        throw new Error(detailMsg);
      }

      setSuccessMessage(`Issue #${issue.id} deleted successfully.`);

      // If user was editing this issue, reset form
      if (editingId === issue.id) {
        handleCancelEdit();
      }

      // Refresh data
      await loadIssues();
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch' || err.name === 'TypeError'
          ? 'Unable to connect to backend server. Please verify that FastAPI is running.'
          : err.message || 'Failed to delete issue';
      setActionError(msg);
    } finally {
      setDeletingId(null);
    }

  };

  // Filter issues based on search, priority, and status
  const filteredIssues = useMemo(() => {
    const searchLower = searchTerm.trim().toLowerCase();

    return issues.filter((issue) => {
      // Search: case-insensitive match for client_name OR title
      const matchesSearch =
        !searchLower ||
        issue.client_name.toLowerCase().includes(searchLower) ||
        issue.title.toLowerCase().includes(searchLower);

      // Priority filter with "All" option
      const matchesPriority =
        priorityFilter === 'All' || issue.priority === priorityFilter;

      // Status filter with "All" option
      const matchesStatus =
        statusFilter === 'All' || issue.status === statusFilter;

      return matchesSearch && matchesPriority && matchesStatus;
    });
  }, [issues, searchTerm, priorityFilter, statusFilter]);

  const handleResetFilters = () => {
    setSearchTerm('');
    setPriorityFilter('All');
    setStatusFilter('All');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Support Issue Tracker</h1>
        <p>Log, monitor, and resolve client support tickets</p>
      </header>

      <main className="main-layout">
        {/* Issue Form Card */}
        <section id="issue-form-section" className="card" aria-labelledby="form-heading">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 id="form-heading" className="card-title" style={{ margin: 0 }}>
              {editingId !== null ? `Edit Issue #${editingId}` : 'Log New Support Issue'}
            </h2>
            {editingId !== null && (
              <span className="badge badge-medium">Editing Mode</span>
            )}
          </div>

          {formError && (
            <div className="alert alert-error" role="alert">
              <span>{formError}</span>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                onClick={() => setFormError(null)}
              >
                Dismiss
              </button>
            </div>
          )}

          {successMessage && (
            <div className="alert alert-success" role="status">
              <span>{successMessage}</span>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                onClick={() => setSuccessMessage(null)}
              >
                Dismiss
              </button>
            </div>
          )}

          <form onSubmit={handleFormSubmit} className="issue-form" noValidate>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="client-name-input">Client Name *</label>
                <input
                  id="client-name-input"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Acme Corp"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="issue-title-input">Issue Title *</label>
                <input
                  id="issue-title-input"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Database connection timeout"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={saving}
                />
              </div>

              <div className="form-group">
                <label htmlFor="priority-select">Priority</label>
                <select
                  id="priority-select"
                  className="form-control"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  disabled={saving}
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="status-select">Status</label>
                <select
                  id="status-select"
                  className="form-control"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  disabled={saving}
                >
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div className="form-group full-width">
                <label htmlFor="description-input">Description *</label>
                <textarea
                  id="description-input"
                  className="form-control"
                  rows={3}
                  placeholder="Detailed description of the issue..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={saving}
                />
              </div>
            </div>

            <div className="form-actions">
              <button
                id="submit-issue-btn"
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving
                  ? 'Saving Issue...'
                  : editingId !== null
                  ? 'Update Issue'
                  : 'Create Issue'}
              </button>

              {editingId !== null && (
                <button
                  id="cancel-edit-btn"
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleCancelEdit}
                  disabled={saving}
                >
                  Cancel Edit
                </button>
              )}
            </div>
          </form>
        </section>

        {/* Issue List Card */}
        <section className="card" aria-labelledby="list-heading">
          <h2 id="list-heading" className="card-title">Support Issues</h2>

          {actionError && (
            <div className="alert alert-error" role="alert">
              <span>{actionError}</span>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                onClick={() => setActionError(null)}
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Search and Filters Bar */}
          <div className="filter-card">
            <div className="filter-grid">
              <div className="filter-group">
                <label htmlFor="search-input">Search Client or Title</label>
                <input
                  id="search-input"
                  type="text"
                  className="form-control"
                  placeholder="Search by client name or title..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="filter-group">
                <label htmlFor="filter-priority-select">Filter by Priority</label>
                <select
                  id="filter-priority-select"
                  className="form-control"
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                >
                  <option value="All">All Priorities</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>

              <div className="filter-group">
                <label htmlFor="filter-status-select">Filter by Status</label>
                <select
                  id="filter-status-select"
                  className="form-control"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="All">All Statuses</option>
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div className="filter-group">
                <button
                  id="reset-filters-btn"
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleResetFilters}
                >
                  Reset Filters
                </button>
              </div>
            </div>

            <div className="filter-info">
              <span>
                Showing {filteredIssues.length} of {issues.length} total issues
              </span>
              {(searchTerm || priorityFilter !== 'All' || statusFilter !== 'All') && (
                <span>Filters Active</span>
              )}
            </div>
          </div>

          {loading && (
            <div className="state-message">
              <p>Loading issues from backend...</p>
            </div>
          )}

          {fetchError && !loading && (
            <div className="alert alert-error" role="alert">
              <div>
                <strong>Error: </strong> {fetchError}
              </div>
              <button
                id="retry-fetch-btn"
                type="button"
                className="btn btn-secondary"
                onClick={loadIssues}
              >
                Retry
              </button>
            </div>
          )}

          {!loading && !fetchError && issues.length === 0 && (
            <div className="state-message">
              <p>No issues found. Create a new issue to get started.</p>
            </div>
          )}

          {!loading && !fetchError && issues.length > 0 && filteredIssues.length === 0 && (
            <div className="state-message">
              <p>No issues match the search and filter criteria.</p>
            </div>
          )}

          {!loading && !fetchError && filteredIssues.length > 0 && (
            <div className="table-wrapper">
              <table className="issue-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Client Name</th>
                    <th>Title</th>
                    <th>Description</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Reported Time</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIssues.map((issue) => {
                    const overdue = isIssueOverdue(issue);

                    return (
                      <tr
                        key={issue.id}
                        className={overdue ? 'row-overdue' : ''}
                      >
                        <td>#{issue.id}</td>
                        <td><strong>{issue.client_name}</strong></td>
                        <td>{issue.title}</td>
                        <td>{issue.description}</td>
                        <td>
                          <span className={`badge badge-${issue.priority.toLowerCase()}`}>
                            {issue.priority}
                          </span>
                        </td>
                        <td>
                          <div className="status-badges">
                            <span
                              className={`badge badge-${issue.status.toLowerCase().replace(/\s+/g, '-')}`}
                            >
                              {issue.status}
                            </span>
                            {overdue && (
                              <span className="badge badge-overdue">
                                Overdue
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="time-cell" title={`UTC: ${issue.reported_at}`}>
                          <div>{formatLocalTime(issue.reported_at)}</div>
                          <span className="time-utc-tooltip">UTC: {issue.reported_at.slice(0, 19).replace('T', ' ')}</span>
                        </td>
                        <td>
                          <div className="actions-cell">
                            <button
                              id={`edit-issue-${issue.id}-btn`}
                              type="button"
                              className="btn btn-edit"
                              onClick={() => handleStartEdit(issue)}
                              disabled={saving || deletingId === issue.id}
                            >
                              Edit
                            </button>
                            <button
                              id={`delete-issue-${issue.id}-btn`}
                              type="button"
                              className="btn btn-danger"
                              onClick={() => handleDeleteIssue(issue)}
                              disabled={saving || deletingId === issue.id}
                            >
                              {deletingId === issue.id ? 'Deleting...' : 'Delete'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
