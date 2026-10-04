<script lang="ts">
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';
	import type { ArtistSummary } from '$lib/types';
	import { onMount } from 'svelte';
	import { slugify } from '$lib/utils/slugify';

	let query = $state('');
	let results = $state<ArtistSummary[]>([]);
	let isLoading = $state(false);
	let isDropdownOpen = $state(false);
	let selectedIndex = $state(-1);
	
	let debounceTimeout: ReturnType<typeof setTimeout>;
	let searchContainer: HTMLElement;

	function formatNumber(n: number | null | undefined): string {
		if (n == null) return '';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K';
		return n.toLocaleString();
	}

	async function performSearch(searchQuery: string) {
		if (searchQuery.length < 2) {
			results = [];
			isDropdownOpen = false;
			return;
		}

		isLoading = true;
		isDropdownOpen = true;
		selectedIndex = -1;

		try {
			results = await apiClient.explore.search(searchQuery);
		} catch (err: unknown) {
			console.error('Search error:', err);
			results = [];
		} finally {
			isLoading = false;
		}
	}

	function handleInput() {
		clearTimeout(debounceTimeout);
		debounceTimeout = setTimeout(() => {
			performSearch(query.trim());
		}, 300);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (!isDropdownOpen) return;

		const showExternalOption = results.length === 0 && query.trim().length >= 2;
		const maxIndex = showExternalOption ? 0 : results.length - 1;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			selectedIndex = selectedIndex < maxIndex ? selectedIndex + 1 : 0;
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			selectedIndex = selectedIndex > 0 ? selectedIndex - 1 : maxIndex;
		} else if (event.key === 'Enter') {
			event.preventDefault();
			if (selectedIndex >= 0) {
				if (showExternalOption) {
					handleExternalSearch();
				} else if (results[selectedIndex]) {
					navigateToArtist(results[selectedIndex].slug);
				}
			} else if (results.length > 0) {
				navigateToArtist(results[0].slug);
			} else if (showExternalOption) {
				handleExternalSearch();
			}
		} else if (event.key === 'Escape') {
			isDropdownOpen = false;
		}
	}

	function navigateToArtist(slug: string) {
		isDropdownOpen = false;
		query = '';
		goto(`/artist/${slug}`);
	}

	function handleExternalSearch() {
		const slug = slugify(query.trim());
		isDropdownOpen = false;
		query = '';
		goto(`/artist/${slug}`);
	}

	function handleClickOutside(event: MouseEvent) {
		if (searchContainer && !searchContainer.contains(event.target as Node)) {
			isDropdownOpen = false;
		}
	}
	
	onMount(() => {
		window.addEventListener('click', handleClickOutside);
		return () => {
			window.removeEventListener('click', handleClickOutside);
			clearTimeout(debounceTimeout);
		};
	});
</script>

<div class="search-container" bind:this={searchContainer}>
	<div class="input-wrapper">
		<span class="search-icon">⌕</span>
		<input
			type="text"
			bind:value={query}
			oninput={handleInput}
			onkeydown={handleKeydown}
			onfocus={() => {
				if (query.length >= 2) isDropdownOpen = true;
			}}
			placeholder="Search artists..."
			class="search-input"
		/>
		{#if isLoading}
			<span class="spinner"></span>
		{/if}
	</div>

	{#if isDropdownOpen && query.trim().length >= 2}
		<div class="dropdown-overlay">
			{#if isLoading && results.length === 0}
				<div class="dropdown-msg">Searching...</div>
			{:else if results.length > 0}
				<ul class="results-list">
					{#each results as artist, index (artist.id)}
						<li>
							<!-- svelte-ignore a11y_click_events_have_key_events -->
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div
								class="result-item {index === selectedIndex ? 'selected' : ''}"
								onclick={() => navigateToArtist(artist.slug)}
							>
								<div class="artist-image">
									{#if artist.image_url}
										<img src={artist.image_url} alt={artist.name} />
									{:else}
										<div class="placeholder-img">{artist.name.charAt(0).toUpperCase()}</div>
									{/if}
								</div>
								<div class="artist-info">
									<div class="artist-name font-bold">{artist.name}</div>
									<div class="artist-meta flex gap-sm text-sm text-secondary">
										{#if artist.lastfm_listeners != null}
											<span class="listeners">👥 {formatNumber(artist.lastfm_listeners)}</span>
										{/if}
										{#if artist.genres && artist.genres.length > 0}
											<div class="genres flex gap-sm">
												{#each artist.genres.slice(0, 2) as genre (genre)}
													<span class="tag">{genre}</span>
												{/each}
											</div>
										{/if}
									</div>
								</div>
							</div>
						</li>
					{/each}
				</ul>
			{:else}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div 
					class="external-search {0 === selectedIndex ? 'selected' : ''}"
					onclick={handleExternalSearch}
				>
					Search for "{query.trim()}" externally?
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.search-container {
		position: relative;
		width: 100%;
		max-width: 500px;
	}

	.input-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: 0 var(--space-md);
		transition: border-color var(--transition-fast);
	}

	.input-wrapper:focus-within {
		border-color: var(--accent);
	}

	.search-icon {
		color: var(--text-secondary);
		margin-right: var(--space-sm);
		font-size: 1.1rem;
		flex-shrink: 0;
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
		flex-shrink: 0;
		margin-left: var(--space-sm);
	}

	@keyframes spin {
		100% { transform: rotate(360deg); }
	}

	.search-input {
		flex: 1;
		background: transparent;
		border: none;
		color: var(--text);
		padding: var(--space-sm) 0;
		outline: none;
		font-size: 1rem;
	}

	.dropdown-overlay {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		margin-top: var(--space-xs);
		background: var(--card-bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-lg);
		z-index: 1000;
		max-height: 400px;
		overflow-y: auto;
		animation: dropdownFadeIn var(--transition-normal) ease-out;
	}

	@keyframes dropdownFadeIn {
		from {
			opacity: 0;
			transform: translateY(-5px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.results-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.result-item {
		display: flex;
		align-items: center;
		padding: var(--space-sm) var(--space-md);
		gap: var(--space-md);
		cursor: pointer;
		transition: background var(--transition-fast);
	}

	.result-item:hover, .result-item.selected {
		background: var(--bg);
	}

	.artist-image {
		width: 64px;
		height: 64px;
		flex-shrink: 0;
		border-radius: var(--radius-sm);
		overflow: hidden;
		background: var(--bg);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.artist-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.placeholder-img {
		font-size: 1.5rem;
		font-weight: bold;
		color: var(--text-secondary);
	}

	.artist-info {
		flex: 1;
		min-width: 0;
	}

	.artist-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		color: var(--text);
	}

	.artist-meta {
		margin-top: 4px;
		align-items: center;
	}

	.tag {
		background: var(--bg);
		border: 1px solid var(--border);
		padding: 2px 6px;
		border-radius: var(--radius-sm);
		font-size: 0.75rem;
	}

	.dropdown-msg {
		padding: var(--space-md);
		text-align: center;
		color: var(--text-secondary);
	}

	.external-search {
		padding: var(--space-md);
		text-align: center;
		cursor: pointer;
		color: var(--accent);
		transition: background var(--transition-fast);
	}

	.external-search:hover, .external-search.selected {
		background: var(--bg);
	}
</style>
