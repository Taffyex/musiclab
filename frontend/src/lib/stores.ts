import { writable, derived } from 'svelte/store';
import type { DiscoveryBatch, User, LastfmProfile, UserFavorites, FavoriteItem } from '$lib/types';
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

function createFavoritesStore() {
	const { subscribe, set, update } = writable<UserFavorites>({ artists: [], genres: [], styles: [] });

	return {
		subscribe,
		set,
		/** Check if an entity is favorited. */
		isFavorited(entity_type: string, entity_id: number): boolean {
			let result = false;
			subscribe(value => {
				const list = value[entity_type + 's' as keyof UserFavorites] ?? [];
				result = list.some((f: FavoriteItem) => f.entity_id === entity_id);
			})();
			return result;
		},
		/** Optimistically add a favorite. */
		add(item: FavoriteItem) {
			update(favs => {
				const key = (item.entity_type + 's') as keyof UserFavorites;
				if (!favs[key].some(f => f.entity_id === item.entity_id)) {
					favs[key] = [...favs[key], item];
				}
				return { ...favs };
			});
		},
		/** Optimistically remove a favorite. */
		remove(entity_type: string, entity_id: number) {
			update(favs => {
				const key = (entity_type + 's') as keyof UserFavorites;
				favs[key] = (favs[key] as FavoriteItem[]).filter(f => f.entity_id !== entity_id);
				return { ...favs };
			});
		}
	};
}
export const favoritesStore = createFavoritesStore();
