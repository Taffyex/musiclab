<script lang="ts">
	import type { ReleaseDetail } from '$lib/types';
	import ReleaseRow from './ReleaseRow.svelte';
	
	interface Props {
		releases: ReleaseDetail[];
	}
	
	let { releases }: Props = $props();
	let filterType = $state('All');
	
	let filteredReleases = $derived(
		filterType === 'All' 
			? releases 
			: releases.filter(r => r.release_type === filterType)
	);
</script>

<div class="discography mt-lg">
	<div class="flex-between items-center mb-md">
		<h3 class="font-bold text-lg">Discography</h3>
		<select class="type-filter" bind:value={filterType}>
			<option value="All">All</option>
			<option value="Album">Albums</option>
			<option value="Single">Singles</option>
			<option value="EP">EPs</option>
		</select>
	</div>
	
	<div class="release-list flex-col gap-sm">
		{#if filteredReleases.length === 0}
			<p class="text-secondary">No releases found.</p>
		{:else}
			{#each filteredReleases as release}
				<ReleaseRow {release} />
			{/each}
		{/if}
	</div>
</div>

<style>
	.discography {
		background: var(--bg-surface, #1e1e2e);
		padding: 1.5rem;
		border-radius: var(--radius-md, 8px);
		border: 1px solid var(--border-color, #333);
	}
	
	.type-filter {
		background: var(--bg-input, #2a2a3e);
		color: var(--text-primary, #eee);
		border: 1px solid var(--border-color, #444);
		border-radius: var(--radius-sm, 4px);
		padding: 0.25rem 0.5rem;
	}
</style>
