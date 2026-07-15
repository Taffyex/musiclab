// ===== Last.fm API =====

import { apiGet, apiPost } from './client';
import type { LastfmProfile } from '$lib/types';

/** Fetch the cached Last.fm profile for the current user */
export function fetchProfile(): Promise<LastfmProfile> {
	return apiGet<LastfmProfile>('/lastfm/profile');
}

/** Trigger a fresh scrape of the user's Last.fm data */
export function refreshProfile(): Promise<LastfmProfile> {
	return apiPost<LastfmProfile>('/lastfm/profile/refresh');
}
