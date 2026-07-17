<script lang="ts">
	import type { ArtistSummary } from '$lib/types';
	import ArtistCard from './ArtistCard.svelte';
	
	interface Props {
		artists: ArtistSummary[];
	}
	
	let { artists }: Props = $props();
</script>

{#if artists && artists.length > 0}
	<div class="similar-artists mt-lg">
		<h3 class="font-bold text-lg mb-sm">Similar Artists</h3>
		<div class="horizontal-scroll">
			{#each artists as artist}
				<div class="artist-wrapper">
					<ArtistCard {artist} />
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.similar-artists {
		background: var(--bg-surface, #1e1e2e);
		padding: 1.5rem;
		border-radius: var(--radius-md, 8px);
		border: 1px solid var(--border-color, #333);
	}
	
	.horizontal-scroll {
		display: flex;
		gap: 1rem;
		overflow-x: auto;
		padding-bottom: 1rem;
		scrollbar-width: thin;
	}
	
	.horizontal-scroll::-webkit-scrollbar {
		height: 8px;
	}
	
	.horizontal-scroll::-webkit-scrollbar-thumb {
		background: var(--border-color, #444);
		border-radius: 4px;
	}
	
	.artist-wrapper {
		width: 200px;
		flex-shrink: 0;
	}
</style>
