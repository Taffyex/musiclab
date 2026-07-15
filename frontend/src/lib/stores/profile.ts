// ===== Profile Store =====

import { writable } from 'svelte/store';
import * as lastfmApi from '$lib/api/lastfm';
import type { LastfmProfile } from '$lib/types';

/** The user's Last.fm profile data */
export const profile = writable<LastfmProfile | null>(null);

/** Whether a profile fetch/refresh is in progress */
export const loading = writable<boolean>(false);

/** Error message if the last operation failed */
export const error = writable<string | null>(null);

/** Fetch the cached profile from the backend */
export async function fetchProfile(): Promise<void> {
	loading.set(true);
	error.set(null);
	try {
		const data = await lastfmApi.fetchProfile();
		profile.set(data);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to fetch profile';
		error.set(message);
	} finally {
		loading.set(false);
	}
}

/** Trigger a full re-scrape of the Last.fm profile */
export async function refreshProfile(): Promise<void> {
	loading.set(true);
	error.set(null);
	try {
		const data = await lastfmApi.refreshProfile();
		profile.set(data);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to refresh profile';
		error.set(message);
	} finally {
		loading.set(false);
	}
}
