/**
 * KaushalTwin — Date and Timestamp Formatting Utility
 * Provides consistent, unambiguous date and timestamp formatting across all views.
 */

export function formatDate(dateVal) {
  if (!dateVal) return 'N/A';
  try {
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) return 'N/A';

    // Format with explicit short month name to eliminate MM/DD vs DD/MM ambiguity
    const formatted = d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });

    // Check if timestamp is in the future compared to current client time (with 1-day tolerance)
    const isFuture = d.getTime() > Date.now() + 86400000;
    if (isFuture) {
      return `${formatted} (Scheduled)`;
    }

    return formatted;
  } catch {
    return 'N/A';
  }
}

export function formatDateTime(dateVal) {
  if (!dateVal) return 'N/A';
  try {
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) return 'N/A';

    return d.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return 'N/A';
  }
}

export default { formatDate, formatDateTime };
