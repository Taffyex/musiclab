<script lang="ts">
	import type { ExploreFilters } from '$lib/types';
	
	interface Props {
		filters: ExploreFilters;
		onChange: (filters: ExploreFilters) => void;
	}
	
	let { filters, onChange }: Props = $props();
	
	const decades = ["All", "2020s", "2010s", "2000s", "1990s", "1980s", "1970s", "1960s"];
	
	function handleDecadeChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const val = target.value;
		filters.decade = (!val || val === 'All' || val === 'null') ? undefined : val;
		onChange(filters);
	}
</script>

<div class="filters-panel">
	<div class="filter-controls">
		<div class="filter-group">
			<span class="filter-label">Sort by:</span>
			<div class="select-wrapper">
				<select id="sort_by" bind:value={filters.sort_by} onchange={() => onChange(filters)}>
					<option value="listeners">👥 Listeners</option>
					<option value="scrobbles">▶ Playcount</option>
					<option value="name">🔤 Name (A-Z)</option>
				</select>
			</div>
		</div>
		
		<div class="filter-group">
			<span class="filter-label">Order:</span>
			<div class="select-wrapper">
				<select id="sort_order" bind:value={filters.sort_order} onchange={() => onChange(filters)}>
					<option value="desc">High to Low ↓</option>
					<option value="asc">Low to High ↑</option>
				</select>
			</div>
		</div>
		
		<div class="filter-group">
			<span class="filter-label">Decade:</span>
			<div class="select-wrapper">
				<select id="decade" value={filters.decade ?? 'All'} onchange={handleDecadeChange}>
					{#each decades as decade (decade)}
						<option value={decade}>{decade === 'All' ? 'All Eras' : decade}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>
</div>

<style>
	.filters-panel {
		display: flex;
		align-items: center;
		justify-content: flex-start;
	}

	.filter-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 1rem;
	}
	
	.filter-group {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}

	.filter-label {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-secondary);
	}

	.select-wrapper {
		position: relative;
	}
	
	select {
		background: var(--bg-secondary);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.35rem 0.65rem;
		font-size: 0.825rem;
		font-weight: 500;
		outline: none;
		cursor: pointer;
		transition: all 0.15s ease;
	}
	
	select:hover {
		border-color: var(--accent);
	}

	select:focus {
		border-color: var(--accent);
		box-shadow: 0 0 0 2px rgba(108, 92, 231, 0.2);
	}
</style>
