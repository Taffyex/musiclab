<script lang="ts">
	import type { ExploreFilters } from '$lib/types';
	
	interface Props {
		filters: ExploreFilters;
		onChange: (filters: ExploreFilters) => void;
	}
	
	let { filters, onChange }: Props = $props();
	
	const decades = ["All", "2020s", "2010s", "2000s", "1990s", "1980s", "1970s", "1960s"];
	
	function handleChange(e: Event) {
		onChange(filters);
	}
</script>

<div class="filters-panel flex wrap items-center gap-md py-md">
	<div class="filter-group">
		<label for="sort_by" class="text-sm font-medium">Sort By:</label>
		<select id="sort_by" bind:value={filters.sort_by} onchange={handleChange}>
			<option value="listeners">Listeners</option>
			<option value="scrobbles">Scrobbles</option>
			<option value="name">Name</option>
		</select>
	</div>
	
	<div class="filter-group">
		<label for="sort_order" class="text-sm font-medium">Order:</label>
		<select id="sort_order" bind:value={filters.sort_order} onchange={handleChange}>
			<option value="desc">Descending</option>
			<option value="asc">Ascending</option>
		</select>
	</div>
	
	<div class="filter-group">
		<label for="decade" class="text-sm font-medium">Decade:</label>
		<select id="decade" bind:value={filters.decade} onchange={handleChange}>
			{#each decades as decade}
				<option value={decade === "All" ? null : decade}>{decade}</option>
			{/each}
		</select>
	</div>
</div>

<style>
	.filters-panel {
		background: var(--bg-surface, #1e1e2e);
		border-radius: var(--radius-md, 8px);
		padding: 1rem;
		border: 1px solid var(--border-color, #333);
	}
	
	.filter-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	select {
		background: var(--bg-input, #2a2a3e);
		color: var(--text-primary, #eee);
		border: 1px solid var(--border-color, #444);
		border-radius: var(--radius-sm, 4px);
		padding: 0.25rem 0.5rem;
		outline: none;
	}
	
	select:focus {
		border-color: var(--accent, #6c5ce7);
	}
</style>
