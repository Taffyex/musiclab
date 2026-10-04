// ===== Slugify Utility =====

/**
 * Convert text to a URL-friendly slug, matching the backend's
 * `app.common.utils.slugify` exactly so frontend-generated links
 * resolve to the same artist/genre/style records.
 *
 * - Normalizes Unicode (NFKD) and strips diacritics
 * - Removes all non-word characters except spaces and hyphens
 * - Lowercases, trims, and collapses whitespace/hyphens into single hyphens
 *
 * @example slugify("Godspeed You! Black Emperor") -> "godspeed-you-black-emperor"
 * @example slugify("AC/DC") -> "acdc"
 */
export function slugify(text: string): string {
	return text
		.normalize('NFKD')
		.replace(/[\u0300-\u036f]/g, '')
		.replace(/[^\w\s-]/g, '')
		.trim()
		.toLowerCase()
		.replace(/[-\s]+/g, '-');
}