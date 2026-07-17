<script lang="ts">
	import type { GenreTree } from '$lib/types';
	import FavoriteToggle from './FavoriteToggle.svelte';
	
	interface Props {
		trees: GenreTree[];
		selectedSlug: string | null;
		selectedType: 'genre' | 'style' | null;
		onSelect: (type: 'genre' | 'style', slug: string) => void;
	}
	
	let { trees, selectedSlug, selectedType, onSelect }: Props = $props();
	
	let expandedGenres = $state<Record<number, boolean>>({});
	
	function toggleExpand(genreId: number) {
		expandedGenres[genreId] = !expandedGenres[genreId];
	}
</script>

<div class="genre-tree">
	<h3 class="mb-md font-bold text-lg">Browse Genres</h3>
	<ul class="genre-list">
		{#each trees as tree (tree.genre.id)}
			<li class="mb-sm">
				<div class="flex items-center gap-sm">
					{#if tree.styles.length > 0}
						<button 
							class="expand-btn" 
							onclick={() => toggleExpand(tree.genre.id)}
							aria-label="Toggle styles"
						>
							{expandedGenres[tree.genre.id] ? '▼' : '▶'}
						</button>
					{:else}
						<span class="spacer"></span>
					{/if}
					
					<FavoriteToggle 
						entity_type="genre"
						entity_id={tree.genre.id}
						name={tree.genre.name}
						slug={tree.genre.slug}
					/>
					<button 
						class="genre-btn"
						class:selected={selectedType === 'genre' && selectedSlug === tree.genre.slug}
						onclick={() => onSelect('genre', tree.genre.slug)}
					>
						{tree.genre.name} <span class="text-sm text-secondary">({tree.genre.style_count})</span>
					</button>
				</div>
				
				{#if expandedGenres[tree.genre.id] && tree.styles.length > 0}
					<ul class="style-list mt-xs">
						{#each tree.styles as style (style.id)}
							<li>
								<div class="flex items-center gap-sm">
									<FavoriteToggle 
										entity_type="style"
										entity_id={style.id}
										name={style.name}
										slug={style.slug}
									/>
									<button 
										class="style-btn"
										class:selected={selectedType === 'style' && selectedSlug === style.slug}
										onclick={() => onSelect('style', style.slug)}
									>
										{style.name}
									</button>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</li>
		{/each}
	</ul>
</div>

<style>
	.genre-tree {
		background: var(--card-bg, #1e1e2e);
		border-radius: var(--radius-md, 8px);
		padding: 1rem;
		border: 1px solid var(--border, #333);
	}
	
	.genre-list, .style-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.style-list {
		padding-left: 1.5rem;
	}
	
	.expand-btn {
		background: none;
		border: none;
		color: var(--text-secondary, #aaa);
		cursor: pointer;
		font-size: 0.8rem;
		width: 1rem;
		padding: 0;
	}
	
	.spacer {
		width: 1rem;
		display: inline-block;
	}
	
	.genre-btn, .style-btn {
		background: none;
		border: none;
		color: var(--text-primary, #eee);
		cursor: pointer;
		text-align: left;
		padding: 0.25rem 0.5rem;
		border-radius: var(--radius-sm, 4px);
		width: 100%;
		transition: background 0.2s;
	}
	
	.genre-btn:hover, .style-btn:hover {
		background: var(--bg-hover, #2a2a3e);
	}
	
	.selected {
		background: var(--accent-alpha, rgba(108, 92, 231, 0.2));
		color: var(--accent, #6c5ce7);
		font-weight: bold;
	}
</style>
