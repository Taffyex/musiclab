import { writable, derived } from 'svelte/store';

// Types (simplified for stores)
export interface User {
	id: number;
	username: string;
	lastfm_username: string | null;
}

export interface LastfmProfile {
	username: string;
	playcount: number;
	top_artists: Array<{ name: string; playcount: number; url: string }>;
	top_genres: Array<{ name: string; count: number }>;
	recent_tracks: Array<{ name: string; artist: string; date: string }>;
}

export interface DiscoveryCardItem {
	artist_name: string;
	reason: string;
	tags: string[];
	similarity_score: number;
	listen_links: Record<string, string>;
}

export interface DiscoveryBatch {
	id: number;
	created_at: string;
	recommendations: DiscoveryCardItem[];
}

// User Store
function createUserStore() {
	const { subscribe, set, update } = writable<User | null>(null);

	return {
		subscribe,
		set,
		login: (userData: User) => set(userData),
		logout: () => set(null)
	};
}
export const userStore = createUserStore();
export const isAuthenticated = derived(userStore, ($user) => $user !== null);

// Profile Store
export const profileStore = writable<LastfmProfile | null>(null);

// Discovery Store
export const discoveryStore = writable<DiscoveryBatch | null>(null);

// Theme Store
function createThemeStore() {
	// Initialize theme based on localStorage or system preference if in browser
	const initialTheme = typeof window !== 'undefined' 
		? localStorage.getItem('theme') || 'dark'
		: 'dark';

	const { subscribe, set, update } = writable<string>(initialTheme);

	return {
		subscribe,
		toggle: () => update(theme => {
			const newTheme = theme === 'light' ? 'dark' : 'light';
			if (typeof window !== 'undefined') {
				localStorage.setItem('theme', newTheme);
				document.documentElement.setAttribute('data-theme', newTheme);
			}
			return newTheme;
		}),
		init: () => {
			if (typeof window !== 'undefined') {
				const theme = localStorage.getItem('theme') || 'dark';
				document.documentElement.setAttribute('data-theme', theme);
				set(theme);
			}
		}
	};
}
export const themeStore = createThemeStore();
