// ===== Theme Store =====

import { writable } from 'svelte/store';

export type Theme = 'light' | 'dark';

/**
 * Determine the initial theme:
 *  1. Check localStorage for a saved preference
 *  2. Fall back to system preference via prefers-color-scheme
 *  3. Default to 'light'
 */
function getInitialTheme(): Theme {
	if (typeof window === 'undefined') return 'light';

	const saved = localStorage.getItem('musiclab-theme');
	if (saved === 'light' || saved === 'dark') return saved;

	if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';

	return 'light';
}

/** The current theme */
export const theme = writable<Theme>(getInitialTheme());

/** Apply the theme to the document and persist to localStorage */
function applyTheme(value: Theme): void {
	if (typeof document === 'undefined') return;
	document.documentElement.setAttribute('data-theme', value);
	localStorage.setItem('musiclab-theme', value);
}

// Subscribe to keep DOM and localStorage in sync
theme.subscribe(applyTheme);

/** Toggle between light and dark mode */
export function toggleTheme(): void {
	theme.update((current) => (current === 'light' ? 'dark' : 'light'));
}
