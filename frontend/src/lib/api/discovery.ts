// ===== Discovery API =====

import { apiGet, apiPost } from './client';
import type { DiscoveryBatch, DiscoveryCard } from '$lib/types';

/** Generate a new batch of AI-powered artist recommendations */
export function generateBatch(): Promise<DiscoveryBatch> {
	return apiPost<DiscoveryBatch>('/discovery/generate');
}

/** Get artists similar to the given artist */
export function exploreSimilar(artistName: string): Promise<DiscoveryCard[]> {
	return apiGet<DiscoveryCard[]>(`/discovery/similar?artist=${encodeURIComponent(artistName)}`);
}

/** Get all past discovery batches */
export function getHistory(): Promise<DiscoveryBatch[]> {
	return apiGet<DiscoveryBatch[]>('/discovery/history');
}
