// ===== Lidarr API =====

import { apiGet, apiPost } from './client';
import type { LidarrArtist, AddArtistRequest, QualityProfile, RootFolder } from '$lib/types';

/** Get all artists currently in the Lidarr library */
export function getLibrary(): Promise<LidarrArtist[]> {
	return apiGet<LidarrArtist[]>('/lidarr/library');
}

/** Add a new artist to the Lidarr library */
export function addArtist(data: AddArtistRequest): Promise<LidarrArtist> {
	return apiPost<LidarrArtist>('/lidarr/artist', data);
}

/** Get available quality profiles from Lidarr */
export function getProfiles(): Promise<QualityProfile[]> {
	return apiGet<QualityProfile[]>('/lidarr/profiles');
}

/** Get available root folders from Lidarr */
export function getRootFolders(): Promise<RootFolder[]> {
	return apiGet<RootFolder[]>('/lidarr/rootfolders');
}
