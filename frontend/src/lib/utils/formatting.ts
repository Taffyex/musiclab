// ===== Formatting Utilities =====

/**
 * Format a number into a human-readable abbreviated string.
 * e.g., 1234 -> '1.2K', 1500000 -> '1.5M'
 */
export function formatNumber(n: number): string {
	if (n >= 1_000_000) {
		return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
	}
	if (n >= 1_000) {
		return `${(n / 1_000).toFixed(1).replace(/\.0$/, '')}K`;
	}
	return n.toString();
}

/**
 * Format an ISO date string into a user-friendly representation.
 * e.g., '2024-03-15T10:30:00Z' -> 'Mar 15, 2024'
 */
export function formatDate(date: string): string {
	try {
		return new Intl.DateTimeFormat('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(new Date(date));
	} catch {
		return date;
	}
}

/**
 * Truncate text to a maximum length, adding ellipsis if truncated.
 */
export function truncateText(text: string, maxLength: number): string {
	if (text.length <= maxLength) return text;
	return text.slice(0, maxLength).trimEnd() + '…';
}
