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
	
	let slug = $derived($page.params.slug);
	
	let loading = $state(true);
	let error = $state<string | null>(null);
	let artist = $state<ArtistDetail | null>(null);
	
	$effect(() => {
		if (slug) {
			loadArtist(slug);
		}
	});
	
	async function loadArtist(artistSlug: string) {
		loading = true;
		error = null;
		try {
			await requireAuth();
			artist = await apiClient.explore.getArtist(artistSlug);
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
		<div class="flex-center py-xl">
			<p>Loading artist details...</p>
		</div>
	{:else if error}
		<div class="error-msg">{error}</div>
	{:else if artist}
		<ArtistHeader {artist} />
		<ArtistBio bio={artist.bio} />
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
	}
</style>
