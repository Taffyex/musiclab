<script lang="ts">
	// TODO: Implement Lidarr add flow and explore similar navigation
	import type { DiscoveryCard } from '$lib/types';
	import { truncateText } from '$lib/utils/formatting';

	interface Props {
		card: DiscoveryCard;
		onExplore?: (artistName: string) => void;
		onAdd?: (card: DiscoveryCard) => void;
	}

	let { card, onExplore, onAdd }: Props = $props();
</script>

<article class="discovery-card card">
	{#if card.image_url}
		<div class="card-image">
			<img src={card.image_url} alt={card.artist_name} />
		</div>
	{/if}

	<div class="card-body">
		<h3 class="artist-name">{card.artist_name}</h3>

		{#if card.genres.length > 0}
			<div class="genres flex gap-sm">
				{#each card.genres.slice(0, 4) as genre}
					<span class="tag">{genre}</span>
				{/each}
			</div>
		{/if}

		<p class="blurb text-secondary text-sm">
			{truncateText(card.blurb, 150)}
		</p>

		<div class="card-actions flex gap-sm">
			<button
				class="btn btn-secondary"
				onclick={() => onExplore?.(card.artist_name)}
			>
				🔍 Explore Similar
			</button>
			<button
				class="btn btn-primary"
				onclick={() => onAdd?.(card)}
			>
				➕ Add to Lidarr
			</button>
		</div>
	</div>
</article>

<style>
	.discovery-card {
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.card-image {
		height: 180px;
		overflow: hidden;
		margin: calc(-1 * var(--space-lg));
		margin-bottom: 0;
	}

	.card-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.card-body {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		padding-top: var(--space-md);
	}

	.artist-name {
		font-size: 1.125rem;
		font-weight: 600;
	}

	.genres {
		flex-wrap: wrap;
	}

	.blurb {
		line-height: 1.5;
	}

	.card-actions {
		margin-top: var(--space-sm);
	}
</style>
