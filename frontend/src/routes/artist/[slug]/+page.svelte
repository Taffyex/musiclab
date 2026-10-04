<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { requireAuth } from '$lib/utils/auth-guard';
	import { apiClient } from '$lib/api';
	import type { ArtistDetail } from '$lib/types';
	
	import ArtistHeader from '$lib/components/ArtistHeader.svelte';
	import ArtistBio from '$lib/components/ArtistBio.svelte';
	import Discography from '$lib/components/Discography.svelte';
	import SimilarArtists from '$lib/components/SimilarArtists.svelte';
	import ArtistRelations from '$lib/components/ArtistRelations.svelte';
	import TopTracks from '$lib/components/TopTracks.svelte';
	import ExternalLinks from '$lib/components/ExternalLinks.svelte';
	
	let slug = $derived($page.params.slug);
	
	let loading = $state(true);
	let error = $state<string | null>(null);
	let artist = $state<ArtistDetail | null>(null);
	
	$effect(() => {
		if (slug) {
			loadArtist(slug);
		}
	});
	
	function saveToRecent(artistData: ArtistDetail) {
		if (typeof window === 'undefined') return;
		const STORAGE_KEY = 'musiclab_recent';
		const MAX_ITEMS = 20;
		try {
			const existing = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
			const filtered = existing.filter((a: any) => a.slug !== artistData.slug);
			filtered.unshift({ slug: artistData.slug, name: artistData.name, image_url: artistData.image_url, timestamp: Date.now() });
			localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered.slice(0, MAX_ITEMS)));
		} catch { /* localStorage unavailable */ }
	}

	async function loadArtist(artistSlug: string) {
		loading = true;
		error = null;
		try {
			await requireAuth();
			artist = await apiClient.explore.getArtist(artistSlug);
			if (artist) {
				saveToRecent(artist);
				
				// If releases or similar_artists are empty, load them in background as fallback
				if (!artist.releases || artist.releases.length === 0) {
					apiClient.explore.getReleases(artistSlug).then((rels) => {
						if (artist && rels && rels.length > 0) {
							artist.releases = rels;
						}
					}).catch(() => {});
				}
				
				if (!artist.similar_artists || artist.similar_artists.length === 0) {
					apiClient.explore.getSimilar(artistSlug).then((sim) => {
						if (artist && sim && sim.length > 0) {
							artist.similar_artists = sim;
						}
					}).catch(() => {});
				}
			}
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'An unexpected error occurred';
			error = message;
		} finally {
			loading = false;
		}
	}
</script>

<div class="artist-page">
	{#if loading && !artist}
		<div class="artist-skeleton">
			<div class="skeleton-header card">
				<div class="skeleton skeleton-avatar"></div>
				<div class="skeleton-info">
					<div class="skeleton skeleton-title"></div>
					<div class="skeleton skeleton-meta"></div>
					<div class="skeleton skeleton-tags"></div>
					<div class="skeleton skeleton-stats"></div>
				</div>
			</div>
			<div class="skeleton card skeleton-bio"></div>
			<div class="skeleton card skeleton-tracks"></div>
		</div>
	{:else if error}
		<div class="error-msg">{error}</div>
	{:else if artist}
		<ArtistHeader {artist} />
		<ExternalLinks artistName={artist.name} discogsId={artist.discogs_id} mbid={artist.mbid} />
		<ArtistBio bio={artist.bio} />
		<TopTracks slug={artist.slug} artistName={artist.name} />
		<Discography releases={artist.releases} />
		<SimilarArtists artists={artist.similar_artists} />
		<ArtistRelations relations={artist.mb_relations} />
	{/if}
</div>

<style>
	.artist-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		display: flex;
		flex-direction: column;
		gap: var(--space-xl, 2rem);
	}

	/* Skeleton Loader */
	.artist-skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--space-xl);
	}
	.skeleton-header {
		display: flex;
		gap: var(--space-lg);
		align-items: center;
		flex-wrap: wrap;
	}
	.skeleton-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		min-width: 200px;
	}
	@keyframes shimmer {
		0% { background-position: -200% 0; }
		100% { background-position: 200% 0; }
	}
	.skeleton {
		background: linear-gradient(90deg, var(--border) 25%, var(--card-bg) 50%, var(--border) 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite linear;
		border-radius: var(--radius-md);
	}
	.skeleton-avatar { width: 200px; height: 200px; border-radius: 50%; flex-shrink: 0; }
	.skeleton-title { height: 2rem; width: 60%; }
	.skeleton-meta { height: 1rem; width: 80%; }
	.skeleton-tags { height: 1.5rem; width: 50%; }
	.skeleton-stats { height: 1rem; width: 70%; }
	.skeleton-bio { height: 120px; padding: 0; border: none; }
	.skeleton-tracks { height: 300px; padding: 0; border: none; }
</style>
