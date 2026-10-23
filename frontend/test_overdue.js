import assert from 'node:assert';
import { isIssueOverdue, formatLocalTime } from './src/utils.js';

// Base time anchor: 2026-10-23T12:00:00.000Z
const now = new Date('2026-10-23T12:00:00.000Z').getTime();

const hoursAgo = (h) => new Date(now - h * 60 * 60 * 1000).toISOString();

console.log('Running Overdue Behavior Verification Suite...');

// Case 1: High, Open, 25 hours old: highlighted (TRUE)
const case1 = {
  id: 101,
  priority: 'High',
  status: 'Open',
  reported_at: hoursAgo(25),
};
assert.strictEqual(
  isIssueOverdue(case1, now),
  true,
  'Case 1 failed: High, Open, 25h old must be overdue'
);
console.log('✓ Case 1 passed: High, Open, 25h old is highlighted');

// Case 2: High, In Progress, 25 hours old: highlighted (TRUE)
const case2 = {
  id: 102,
  priority: 'High',
  status: 'In Progress',
  reported_at: hoursAgo(25),
};
assert.strictEqual(
  isIssueOverdue(case2, now),
  true,
  'Case 2 failed: High, In Progress, 25h old must be overdue'
);
console.log('✓ Case 2 passed: High, In Progress, 25h old is highlighted');

// Case 3: High, Resolved, 25 hours old: not highlighted (FALSE)
const case3 = {
  id: 103,
  priority: 'High',
  status: 'Resolved',
  reported_at: hoursAgo(25),
};
assert.strictEqual(
  isIssueOverdue(case3, now),
  false,
  'Case 3 failed: High, Resolved, 25h old must NOT be overdue'
);
console.log('✓ Case 3 passed: High, Resolved, 25h old is NOT highlighted');

// Case 4: Medium, Open, 25 hours old: not highlighted (FALSE)
const case4 = {
  id: 104,
  priority: 'Medium',
  status: 'Open',
  reported_at: hoursAgo(25),
};
assert.strictEqual(
  isIssueOverdue(case4, now),
  false,
  'Case 4 failed: Medium, Open, 25h old must NOT be overdue'
);
console.log('✓ Case 4 passed: Medium, Open, 25h old is NOT highlighted');

// Case 5: High, Open, 23 hours old: not highlighted (FALSE)
const case5 = {
  id: 105,
  priority: 'High',
  status: 'Open',
  reported_at: hoursAgo(23),
};
assert.strictEqual(
  isIssueOverdue(case5, now),
  false,
  'Case 5 failed: High, Open, 23h old must NOT be overdue'
);
console.log('✓ Case 5 passed: High, Open, 23h old is NOT highlighted');

// Verify strictly greater than 24 hours:
// At exactly 24.0 hours (1440 minutes): false
const exactly24h = {
  id: 106,
  priority: 'High',
  status: 'Open',
  reported_at: hoursAgo(24),
};
assert.strictEqual(
  isIssueOverdue(exactly24h, now),
  false,
  'Strictly greater than 24h failed: Exactly 24h old must NOT be overdue'
);
console.log('✓ Boundary check passed: Exactly 24h old is NOT overdue');

// At 24 hours + 1 second: true
const justOver24h = {
  id: 107,
  priority: 'High',
  status: 'Open',
  reported_at: new Date(now - (24 * 60 * 60 * 1000 + 1000)).toISOString(),
};
assert.strictEqual(
  isIssueOverdue(justOver24h, now),
  true,
  'Strictly greater than 24h failed: 24h + 1s must be overdue'
);
console.log('✓ Boundary check passed: 24h + 1s IS overdue (strictly greater than 24h)');

// Verify resolving an overdue issue removes its highlight
const overdueBefore = {
  id: 108,
  priority: 'High',
  status: 'Open',
  reported_at: hoursAgo(30),
};
assert.strictEqual(isIssueOverdue(overdueBefore, now), true);
const resolvedAfter = { ...overdueBefore, status: 'Resolved' };
assert.strictEqual(
  isIssueOverdue(resolvedAfter, now),
  false,
  'Resolving issue must remove overdue highlight'
);
console.log('✓ Transition check passed: Resolving an overdue issue removes its highlight');

// Verify formatLocalTime
const sampleIso = '2026-10-23T07:22:28.000Z';
const formatted = formatLocalTime(sampleIso);
assert.ok(formatted && formatted.length > 5, 'formatLocalTime should produce non-empty string');
console.log(`✓ Timestamp formatting check passed: "${sampleIso}" -> "${formatted}"`);

console.log('\nAll 8 overdue behavior checks passed successfully!');
