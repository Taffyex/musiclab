<script lang="ts">
	import { onMount } from 'svelte';
	import { requireAuth } from '$lib/utils/auth-guard';
	import { apiClient } from '$lib/api';
	import type { GenreTree, ArtistSummary, ExploreFilters } from '$lib/types';
	
	import GenreTreeComp from '$lib/components/GenreTree.svelte';
	import ExploreFiltersComp from '$lib/components/ExploreFilters.svelte';
	import ArtistCard from '$lib/components/ArtistCard.svelte';
	
	let loading = $state(true);
	let error = $state<string | null>(null);
	
	let genreTrees = $state<GenreTree[]>([]);
	let artists = $state<ArtistSummary[]>([]);
	let totalArtists = $state(0);
	
	let selectedType = $state<'genre' | 'style' | null>(null);
	let selectedSlug = $state<string | null>(null);
	
	let filters = $state<ExploreFilters>({
		sort_by: 'listeners',
		sort_order: 'desc',
		page: 1,
		per_page: 20
	});
	
	onMount(async () => {
		try {
			await requireAuth();
			const trees = await apiClient.explore.getGenres();
			genreTrees = trees;
			
			// Select first genre by default if available
			if (trees.length > 0) {
				handleSelect('genre', trees[0].genre.slug);
			}
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'An unexpected error occurred';
			error = message;
		} finally {
			loading = false;
		}
	});
	
	async function loadArtists() {
		if (!selectedType || !selectedSlug) return;
		
		loading = true;
		error = null;
		try {
			let res;
			if (selectedType === 'genre') {
				res = await apiClient.explore.getGenreArtists(selectedSlug, filters);
			} else {
				res = await apiClient.explore.getStyleArtists(selectedSlug, filters);
			}
			artists = res.artists;
			totalArtists = res.total;
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'An unexpected error occurred';
			error = message;
			artists = [];
			totalArtists = 0;
		} finally {
			loading = false;
		}
	}
	
	function handleSelect(type: 'genre' | 'style', slug: string) {
		selectedType = type;
		selectedSlug = slug;
		filters.page = 1;
		loadArtists();
	}
	
	function handleFiltersChange(newFilters: ExploreFilters) {
		filters = { ...newFilters, page: 1 };
		loadArtists();
	}
	
	function loadMore() {
		filters.page += 1;
		// Normally we'd append, but for simplicity here we just re-fetch page 1..N 
		// Actually let's just fetch the next page and append
		loadNextPage();
	}
	
	async function loadNextPage() {
		if (!selectedType || !selectedSlug) return;
		
		try {
			let res;
			if (selectedType === 'genre') {
				res = await apiClient.explore.getGenreArtists(selectedSlug, filters);
			} else {
				res = await apiClient.explore.getStyleArtists(selectedSlug, filters);
			}
			artists = [...artists, ...res.artists];
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Failed to load more';
			error = message;
		}
	}
</script>

<div class="explore-page">
	<div class="sidebar">
		<GenreTreeComp 
			trees={genreTrees} 
			{selectedType} 
			{selectedSlug} 
			onSelect={handleSelect} 
		/>
	</div>
	
	<div class="main-content">
		<ExploreFiltersComp {filters} onChange={handleFiltersChange} />
		
		{#if error}
			<div class="error-msg mt-md">{error}</div>
		{/if}
		
		<div class="grid-container mt-md">
			{#if loading && artists.length === 0}
				<p>Loading artists...</p>
			{:else if artists.length === 0}
				<p>No artists found.</p>
			{:else}
				<div class="artist-grid">
					{#each artists as artist (artist.id)}
						<ArtistCard {artist} />
					{/each}
				</div>
				
				{#if artists.length < totalArtists}
					<div class="flex-center mt-xl">
						<button class="load-more-btn" onclick={loadMore}>
							Load More
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<style>
	.explore-page {
		display: flex;
		gap: 2rem;
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
	}
	
	.sidebar {
		width: 300px;
		flex-shrink: 0;
	}
	
	.main-content {
		flex: 1;
		min-width: 0;
	}
	
	.artist-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1.5rem;
	}
	
	.load-more-btn {
		background: var(--accent, #6c5ce7);
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: var(--radius-md, 8px);
		cursor: pointer;
		font-weight: bold;
		transition: background 0.2s;
	}
	
	.load-more-btn:hover {
		background: var(--accent-hover, #5a4bcf);
	}
	
	@media (max-width: 1024px) {
		.explore-page {
			flex-direction: column;
		}
		
		.sidebar {
			width: 100%;
		}
	}
</style>
