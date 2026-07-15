// ===== Discovery Store =====

import { writable } from 'svelte/store';
import * as discoveryApi from '$lib/api/discovery';
import type { DiscoveryCard, DiscoveryBatch } from '$lib/types';

/** Current batch of discovery cards being displayed */
export const discoveries = writable<DiscoveryCard[]>([]);

/** Full history of discovery batches */
export const history = writable<DiscoveryBatch[]>([]);

/** Whether a generation/fetch is in progress */
export const loading = writable<boolean>(false);

/** Error message from the last operation */
export const error = writable<string | null>(null);

/** Generate a new batch of AI-powered recommendations */
export async function generateBatch(): Promise<void> {
	loading.set(true);
	error.set(null);
	try {
		const batch = await discoveryApi.generateBatch();
		discoveries.set(batch.cards);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to generate discoveries';
		error.set(message);
	} finally {
		loading.set(false);
	}
}

/** Explore artists similar to the given artist */
export async function exploreSimilar(artistName: string): Promise<DiscoveryCard[]> {
	loading.set(true);
	error.set(null);
	try {
		const cards = await discoveryApi.exploreSimilar(artistName);
		discoveries.set(cards);
		return cards;
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to explore similar artists';
		error.set(message);
		return [];
	} finally {
		loading.set(false);
	}
}

/** Load the history of past discovery batches */
export async function loadHistory(): Promise<void> {
	loading.set(true);
	error.set(null);
	try {
		const data = await discoveryApi.getHistory();
		history.set(data);
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Failed to load history';
		error.set(message);
	} finally {
		loading.set(false);
	}
}
