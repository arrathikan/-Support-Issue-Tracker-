/**
 * Evaluates whether an issue is overdue.
 * An issue is overdue ONLY when:
 * 1. priority is High
 * 2. status is not Resolved
 * 3. reported_at is strictly more than 24 hours ago
 *
 * @param {Object} issue
 * @param {number} [currentTime=Date.now()] Optional timestamp for testing
 * @returns {boolean}
 */
export const isIssueOverdue = (issue, currentTime = Date.now()) => {
  if (!issue || issue.priority !== 'High' || issue.status === 'Resolved') {
    return false;
  }
  if (!issue.reported_at) {
    return false;
  }
  const reportedTime = new Date(issue.reported_at).getTime();
  if (isNaN(reportedTime)) {
    return false;
  }
  const differenceInMs = currentTime - reportedTime;
  const twentyFourHoursInMs = 24 * 60 * 60 * 1000;
  return differenceInMs > twentyFourHoursInMs;
};

/**
 * Formats a UTC ISO timestamp string into the user's local date and time string.
 *
 * @param {string} isoString
 * @returns {string}
 */
export const formatLocalTime = (isoString) => {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
};
