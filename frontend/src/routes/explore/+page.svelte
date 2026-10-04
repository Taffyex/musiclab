<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { requireAuth } from '$lib/utils/auth-guard';
	import { apiClient } from '$lib/api';
	import type { GenreTree, ArtistSummary, ExploreFilters } from '$lib/types';
	
	import GenreTreeComp from '$lib/components/GenreTree.svelte';
	import ExploreFiltersComp from '$lib/components/ExploreFilters.svelte';
	import ArtistCard from '$lib/components/ArtistCard.svelte';
	
	let loading = $state(true);
	let loadingMore = $state(false);
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
		per_page: 24
	});

	let activeTitle = $derived.by(() => {
		if (!selectedSlug) return 'Explore All Music';
		if (selectedType === 'genre') {
			const g = genreTrees.find(t => t.genre.slug === selectedSlug);
			return g ? g.genre.name : selectedSlug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
		}
		for (const t of genreTrees) {
			const s = t.styles.find(st => st.slug === selectedSlug);
			if (s) return s.name;
		}
		return selectedSlug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
	});

	let activeParentGenre = $derived.by(() => {
		if (selectedType !== 'style' || !selectedSlug) return null;
		for (const t of genreTrees) {
			if (t.styles.some(st => st.slug === selectedSlug)) {
				return t.genre;
			}
		}
		return null;
	});
	
	onMount(async () => {
		try {
			await requireAuth();
			const trees = await apiClient.explore.getGenres();
			genreTrees = trees;
			
			// Honor deep links from tag/favorite cards: /explore?tag={slug}, /explore?genre={slug}, /explore?style={slug}
			const params = $page.url.searchParams;
			const tagSlug = params.get('tag');
			const styleSlug = params.get('style');
			const genreSlug = params.get('genre');
			
			let initialType: 'genre' | 'style' | null = null;
			let initialSlug: string | null = null;
			
			const targetSlug = tagSlug || styleSlug || genreSlug;
			if (targetSlug) {
				// 1. Check if targetSlug matches any style
				let foundStyle = false;
				for (const tree of trees) {
					const matched = tree.styles.find((s: { slug: string }) => s.slug === targetSlug);
					if (matched) {
						initialType = 'style';
						initialSlug = matched.slug;
						foundStyle = true;
						break;
					}
				}
				
				// 2. If not a style, check if it matches any top-level genre
				if (!foundStyle) {
					const matchedGenre = trees.find((t: { genre: { slug: string } }) => t.genre.slug === targetSlug);
					if (matchedGenre) {
						initialType = 'genre';
						initialSlug = matchedGenre.genre.slug;
					} else {
						// Fallback if not found in tree
						if (styleSlug) {
							initialType = 'style';
							initialSlug = styleSlug;
						} else if (genreSlug) {
							initialType = 'genre';
							initialSlug = genreSlug;
						} else {
							initialType = 'style';
							initialSlug = targetSlug;
						}
					}
				}
			}
			
			if (initialType && initialSlug) {
				selectedType = initialType;
				selectedSlug = initialSlug;
				loadArtists();
			} else if (trees.length > 0) {
				// Select Electronic or Rock by default
				const defaultTree = trees.find((t: GenreTree) => t.genre.slug === 'electronic') || trees.find((t: GenreTree) => t.genre.slug === 'rock') || trees[0];
				handleSelect('genre', defaultTree.genre.slug);
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
			artists = res.artists || [];
			totalArtists = res.total || 0;
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
	
	async function loadMore() {
		if (!selectedType || !selectedSlug || loadingMore) return;
		loadingMore = true;
		filters.page += 1;
		
		try {
			let res;
			if (selectedType === 'genre') {
				res = await apiClient.explore.getGenreArtists(selectedSlug, filters);
			} else {
				res = await apiClient.explore.getStyleArtists(selectedSlug, filters);
			}
			artists = [...artists, ...(res.artists || [])];
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Failed to load more';
			error = message;
		} finally {
			loadingMore = false;
		}
	}
</script>

<div class="explore-page">
	<aside class="sidebar">
		<GenreTreeComp 
			trees={genreTrees} 
			{selectedType} 
			{selectedSlug} 
			onSelect={handleSelect} 
		/>
	</aside>
	
	<main class="main-content">
		<!-- Header Banner -->
		<header class="explore-header card">
			<div class="header-main">
				{#if activeParentGenre}
					<nav class="breadcrumbs" aria-label="Breadcrumb">
						<button class="breadcrumb-link" onclick={() => handleSelect('genre', activeParentGenre.slug)}>
							{activeParentGenre.name}
						</button>
						<span class="breadcrumb-sep">/</span>
						<span class="breadcrumb-current">{activeTitle}</span>
					</nav>
				{/if}
				<div class="title-row">
					<h1 class="explore-title">{activeTitle}</h1>
					{#if totalArtists > 0}
						<span class="total-badge">{totalArtists.toLocaleString()} artists</span>
					{/if}
				</div>
				<p class="explore-subtitle">
					{#if selectedType === 'genre'}
						Explore popular and underground artists across {activeTitle} sub-styles and records.
					{:else if selectedType === 'style'}
						Discover curated {activeTitle} records, producers, and artist catalogs.
					{:else}
						Browse our catalog of over 400,000 artists organized by genre taxonomy.
					{/if}
				</p>
			</div>

			<ExploreFiltersComp {filters} onChange={handleFiltersChange} />
		</header>
		
		{#if error}
			<div class="error-banner card">
				<span class="error-icon">⚠️</span>
				<div class="error-content">
					<strong>Something went wrong:</strong> {error}
				</div>
			</div>
		{/if}
		
		<div class="content-container">
			{#if loading && artists.length === 0}
				<div class="artist-grid">
					{#each Array(12) as _, i (i)}
						<div class="skeleton-card card">
							<div class="skeleton skeleton-img"></div>
							<div class="skeleton skeleton-title"></div>
							<div class="skeleton skeleton-text"></div>
							<div class="skeleton skeleton-tags"></div>
						</div>
					{/each}
				</div>
			{:else if artists.length === 0}
				<div class="empty-state card">
					<span class="empty-icon">🎧</span>
					<h3>No artists found</h3>
					<p class="text-secondary">Try selecting a different genre, style, or adjusting your filter parameters.</p>
					{#if genreTrees.length > 0}
						<button class="btn btn-primary mt-md" onclick={() => handleSelect('genre', genreTrees[0].genre.slug)}>
							Browse {genreTrees[0].genre.name}
						</button>
					{/if}
				</div>
			{:else}
				<div class="artist-grid">
					{#each artists as artist (artist.id + '-' + artist.slug)}
						<ArtistCard {artist} />
					{/each}
				</div>
				
				{#if artists.length < totalArtists}
					<div class="pagination-footer">
						<span class="progress-text">Showing {artists.length.toLocaleString()} of {totalArtists.toLocaleString()} artists</span>
						<button class="btn btn-primary load-more-btn" onclick={loadMore} disabled={loadingMore}>
							{#if loadingMore}
								<span class="spinner"></span> Loading more...
							{:else}
								Load More ({Math.min(24, totalArtists - artists.length).toLocaleString()})
							{/if}
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</main>
</div>

<style>
	.explore-page {
		display: flex;
		gap: 1.75rem;
		max-width: 1540px;
		margin: 0 auto;
		padding: 1.5rem 1.5rem 3rem;
		align-items: flex-start;
	}
	
	.sidebar {
		width: 320px;
		flex-shrink: 0;
	}
	
	.main-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.explore-header {
		padding: 1.5rem;
		border-radius: var(--radius-lg);
		background: linear-gradient(135deg, var(--card-bg) 0%, var(--bg-secondary) 100%);
		border: 1px solid var(--border);
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.breadcrumbs {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.8rem;
		margin-bottom: 0.25rem;
	}

	.breadcrumb-link {
		background: none;
		border: none;
		color: var(--accent);
		cursor: pointer;
		padding: 0;
		font-size: inherit;
		font-weight: 500;
	}

	.breadcrumb-link:hover {
		text-decoration: underline;
	}

	.breadcrumb-sep {
		color: var(--text-secondary);
	}

	.breadcrumb-current {
		color: var(--text);
		font-weight: 600;
	}

	.title-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.explore-title {
		font-size: 1.75rem;
		font-weight: 800;
		margin: 0;
		color: var(--text);
		letter-spacing: -0.02em;
	}

	.total-badge {
		background: rgba(108, 92, 231, 0.15);
		color: var(--accent);
		border: 1px solid rgba(108, 92, 231, 0.3);
		padding: 0.2rem 0.65rem;
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		font-weight: 600;
	}

	.explore-subtitle {
		margin: 0.25rem 0 0;
		color: var(--text-secondary);
		font-size: 0.9rem;
		line-height: 1.4;
	}

	.error-banner {
		padding: 1rem;
		background: rgba(235, 77, 75, 0.1);
		border: 1px solid rgba(235, 77, 75, 0.3);
		display: flex;
		align-items: center;
		gap: 0.75rem;
		color: #ff7675;
	}
	
	.artist-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
		gap: 1.25rem;
	}

	.pagination-footer {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		margin-top: 2.5rem;
		padding: 1.5rem;
		background: var(--card-bg);
		border-radius: var(--radius-lg);
		border: 1px solid var(--border);
	}

	.progress-text {
		color: var(--text-secondary);
		font-size: 0.85rem;
	}
	
	.load-more-btn {
		min-width: 220px;
		padding: 0.75rem 2rem;
		font-weight: 700;
	}

	.empty-state {
		padding: 3.5rem 1.5rem;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-lg);
		border: 1px dashed var(--border);
	}

	.empty-icon {
		font-size: 3rem;
		margin-bottom: 0.75rem;
	}

	/* Skeletons */
	.skeleton-card {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.skeleton {
		background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border) 50%, var(--bg-secondary) 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
	}

	.skeleton-img { width: 100%; aspect-ratio: 1; border-radius: var(--radius-md); }
	.skeleton-title { height: 1.25rem; width: 75%; }
	.skeleton-text { height: 0.85rem; width: 50%; }
	.skeleton-tags { height: 1.1rem; width: 60%; }

	@keyframes shimmer {
		0% { background-position: 200% 0; }
		100% { background-position: -200% 0; }
	}
	
	@media (max-width: 1024px) {
		.explore-page {
			flex-direction: column;
			padding: 1rem;
		}
		
		.sidebar {
			width: 100%;
		}
	}
</style>
