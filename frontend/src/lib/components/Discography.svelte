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
			: filterType === 'Appears On'
				? releases.filter(r => r.artist_role && r.artist_role !== 'primary')
				: releases.filter(r => r.release_type === filterType && (!r.artist_role || r.artist_role === 'primary'))
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
			<option value="Compilation">Compilations</option>
			<option value="Soundtrack">Soundtracks</option>
			<option value="Appears On">Appears On</option>
		</select>
	</div>

	
	<div class="release-list flex-col gap-sm">
		{#if filteredReleases.length === 0}
			<p class="text-secondary">No releases found.</p>
		{:else}
			{#each filteredReleases as release (release.id)}
				<ReleaseRow {release} />
			{/each}
		{/if}
	</div>
</div>

<style>
	.discography {
		background: var(--card-bg);
		padding: 1.5rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--border);
	}
	
	.type-filter {
		background: var(--bg-secondary);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.25rem 0.5rem;
	}
</style>
