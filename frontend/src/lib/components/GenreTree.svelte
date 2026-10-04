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
	let filterQuery = $state('');
	
	$effect(() => {
		if (selectedType === 'style' && selectedSlug && trees.length > 0) {
			for (const tree of trees) {
				if (tree.styles.some((s) => s.slug === selectedSlug)) {
					expandedGenres[tree.genre.id] = true;
					break;
				}
			}
		}
	});
	
	function toggleExpand(genreId: number) {
		expandedGenres[genreId] = !expandedGenres[genreId];
	}

	function expandAll() {
		const next: Record<number, boolean> = {};
		for (const t of trees) {
			next[t.genre.id] = true;
		}
		expandedGenres = next;
	}

	function collapseAll() {
		expandedGenres = {};
	}

	// Filtered trees based on search
	let filteredTrees = $derived.by(() => {
		const q = filterQuery.trim().toLowerCase();
		if (!q) return trees;

		return trees
			.map(t => {
				const genreMatches = t.genre.name.toLowerCase().includes(q);
				const matchingStyles = t.styles.filter(s => s.name.toLowerCase().includes(q));
				if (genreMatches || matchingStyles.length > 0) {
					return {
						...t,
						styles: genreMatches ? t.styles : matchingStyles
					};
				}
				return null;
			})
			.filter((t): t is GenreTree => t !== null);
	});
</script>

<div class="genre-tree">
	<div class="tree-header">
		<h3 class="tree-title">
			<span class="tree-icon">📂</span> Genres & Styles
		</h3>
		<div class="tree-actions">
			<button class="action-btn" onclick={expandAll} title="Expand all">Expand</button>
			<span class="sep">•</span>
			<button class="action-btn" onclick={collapseAll} title="Collapse all">Collapse</button>
		</div>
	</div>

	<div class="search-box">
		<input 
			type="text"
			placeholder="Filter genres or styles..."
			bind:value={filterQuery}
			class="tree-search-input"
		/>
		{#if filterQuery}
			<button class="clear-search-btn" onclick={() => filterQuery = ''}>✕</button>
		{/if}
	</div>
	
	<ul class="genre-list">
		{#if filteredTrees.length === 0}
			<li class="empty-filter">No genres matching "{filterQuery}"</li>
		{/if}
		{#each filteredTrees as tree (tree.genre.id)}
			{@const isExpanded = expandedGenres[tree.genre.id] || Boolean(filterQuery)}
			<li class="genre-item">
				<div class="genre-row" class:is-active={selectedType === 'genre' && selectedSlug === tree.genre.slug}>
					{#if tree.styles.length > 0}
						<button 
							class="expand-btn" 
							onclick={() => toggleExpand(tree.genre.id)}
							aria-label="Toggle styles"
						>
							<span class="arrow-icon" class:rotated={isExpanded}>▶</span>
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
						<span class="genre-name">{tree.genre.name}</span>
						{#if tree.genre.style_count > 0}
							<span class="count-badge">{tree.genre.style_count}</span>
						{/if}
					</button>
				</div>
				
				{#if isExpanded && tree.styles.length > 0}
					<ul class="style-list">
						{#each tree.styles as style (style.id)}
							<li class="style-item">
								<div class="style-row" class:is-active={selectedType === 'style' && selectedSlug === style.slug}>
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
										<span class="style-bullet">•</span>
										<span class="style-name">{style.name}</span>
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
		background: var(--card-bg);
		border-radius: var(--radius-lg);
		padding: 1.25rem;
		border: 1px solid var(--border);
		box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - 120px);
		position: sticky;
		top: 80px;
	}
	
	.tree-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}

	.tree-title {
		font-size: 1rem;
		font-weight: 700;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin: 0;
		color: var(--text);
	}

	.tree-icon {
		font-size: 1.1rem;
	}

	.tree-actions {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
	}

	.action-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		font-size: 0.75rem;
		padding: 2px 4px;
		border-radius: var(--radius-sm);
		transition: color 0.15s ease;
	}

	.action-btn:hover {
		color: var(--accent);
	}

	.sep {
		color: var(--border);
	}

	.search-box {
		position: relative;
		margin-bottom: 0.75rem;
	}

	.tree-search-input {
		width: 100%;
		padding: 0.45rem 1.75rem 0.45rem 0.65rem;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text);
		font-size: 0.8rem;
		outline: none;
		transition: border-color 0.2s ease;
	}

	.tree-search-input:focus {
		border-color: var(--accent);
	}

	.clear-search-btn {
		position: absolute;
		right: 6px;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		font-size: 0.75rem;
		padding: 2px 4px;
	}

	.genre-list {
		list-style: none;
		padding: 0;
		margin: 0;
		overflow-y: auto;
		flex: 1;
		padding-right: 4px;
	}

	.genre-list::-webkit-scrollbar {
		width: 4px;
	}

	.genre-list::-webkit-scrollbar-thumb {
		background: var(--border);
		border-radius: 4px;
	}

	.empty-filter {
		padding: 1rem;
		color: var(--text-secondary);
		font-size: 0.85rem;
		text-align: center;
	}
	
	.genre-item {
		margin-bottom: 0.25rem;
	}

	.genre-row {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		border-radius: var(--radius-sm);
		padding: 0.15rem 0.25rem;
		transition: background 0.15s ease;
	}

	.genre-row:hover {
		background: rgba(255, 255, 255, 0.03);
	}

	.genre-row.is-active {
		background: rgba(108, 92, 231, 0.12);
	}

	.expand-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		font-size: 0.7rem;
		width: 1.25rem;
		height: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		border-radius: var(--radius-sm);
		transition: color 0.15s ease;
	}

	.expand-btn:hover {
		color: var(--accent);
	}

	.arrow-icon {
		display: inline-block;
		transition: transform 0.2s ease;
		font-size: 0.65rem;
	}

	.arrow-icon.rotated {
		transform: rotate(90deg);
	}
	
	.spacer {
		width: 1.25rem;
		display: inline-block;
	}
	
	.genre-btn {
		background: none;
		border: none;
		color: var(--text);
		cursor: pointer;
		text-align: left;
		padding: 0.35rem 0.5rem;
		border-radius: var(--radius-sm);
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.15s ease;
	}
	
	.genre-btn:hover {
		color: var(--accent);
	}
	
	.genre-btn.selected {
		color: var(--accent);
		font-weight: 700;
	}

	.count-badge {
		font-size: 0.7rem;
		background: var(--bg-secondary);
		color: var(--text-secondary);
		padding: 1px 6px;
		border-radius: var(--radius-full);
		font-weight: 600;
	}

	.style-list {
		list-style: none;
		padding: 0.15rem 0 0.25rem 1.65rem;
		margin: 0;
		border-left: 1px solid var(--border);
		margin-left: 0.65rem;
	}

	.style-item {
		margin-bottom: 0.1rem;
	}

	.style-row {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		border-radius: var(--radius-sm);
		padding: 0.1rem 0.25rem;
		transition: background 0.15s ease;
	}

	.style-row:hover {
		background: rgba(255, 255, 255, 0.03);
	}

	.style-row.is-active {
		background: rgba(108, 92, 231, 0.12);
	}

	.style-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		text-align: left;
		padding: 0.25rem 0.4rem;
		border-radius: var(--radius-sm);
		flex: 1;
		font-size: 0.8rem;
		display: flex;
		align-items: center;
		gap: 0.35rem;
		transition: all 0.15s ease;
	}

	.style-bullet {
		color: var(--border);
		font-size: 0.7rem;
	}

	.style-btn:hover {
		color: var(--text);
	}

	.style-btn.selected {
		color: var(--accent);
		font-weight: 600;
	}

	.style-btn.selected .style-bullet {
		color: var(--accent);
	}
</style>
