<script lang="ts">
	import { page } from '$app/stores';
	import { discoveryStore } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import ArtistDetail from '$lib/components/ArtistDetail.svelte';
	import type { DiscoveryCard } from '$lib/types';

	let artist = $state<DiscoveryCard | null>(null);

	onMount(() => {
		const id = $page.params.id;
		
		if (!$discoveryStore || !$discoveryStore.cards) {
			goto('/discover');
			return;
		}

		const found = $discoveryStore.cards.find(c => c.id === id);
		if (found) {
			const slug = found.artist_name.toLowerCase().replace(/ /g, '-').replace(/\//g, '-').replace(/,/g, '').replace(/&/g, 'and');
			goto(`/artist/${slug}`);
		} else {
			goto('/discover');
		}
	});
</script>

<div class="artist-page px-md py-lg">
	<div class="mb-md">
		<a href="/discover" class="btn btn-secondary text-sm">
			← Back to Discover
		</a>
	</div>

	{#if artist}
		<ArtistDetail {artist} />
	{:else}
		<div class="flex-center py-2xl">
			<div class="spinner"></div>
		</div>
	{/if}
</div>

<style>
	.px-md { padding-left: var(--space-md); padding-right: var(--space-md); }
	.py-lg { padding-top: var(--space-lg); padding-bottom: var(--space-lg); }
	.py-2xl { padding-top: var(--space-2xl); padding-bottom: var(--space-2xl); }
	.mb-md { margin-bottom: var(--space-md); }
</style>
