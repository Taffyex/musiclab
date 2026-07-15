<script lang="ts">
	// TODO: Expand with full metadata, discography, external links, etc.
	import type { DiscoveryCard } from '$lib/types';

	interface Props {
		artist: DiscoveryCard;
	}

	let { artist }: Props = $props();
</script>

<div class="artist-detail">
	<div class="artist-header flex gap-lg">
		{#if artist.image_url}
			<img class="artist-image" src={artist.image_url} alt={artist.artist_name} />
		{:else}
			<div class="artist-image placeholder">🎤</div>
		{/if}

		<div class="artist-info flex-col gap-sm">
			<h1>{artist.artist_name}</h1>

			{#if artist.genres.length > 0}
				<div class="genres flex gap-sm">
					{#each artist.genres as genre}
						<span class="tag">{genre}</span>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<section class="artist-blurb">
		<h2>About</h2>
		<p class="text-secondary">{artist.blurb}</p>
	</section>

	{#if artist.reason}
		<section class="artist-reason">
			<h2>Why You'll Like Them</h2>
			<p class="text-secondary">{artist.reason}</p>
		</section>
	{/if}

	{#if artist.similar_artists && artist.similar_artists.length > 0}
		<section class="similar-artists">
			<h2>Similar Artists</h2>
			<div class="flex gap-sm" style="flex-wrap: wrap;">
				{#each artist.similar_artists as name}
					<span class="tag">{name}</span>
				{/each}
			</div>
		</section>
	{/if}

	<div class="external-links flex gap-md">
		{#if artist.lastfm_url}
			<a href={artist.lastfm_url} target="_blank" rel="noopener" class="btn btn-secondary">
				Last.fm ↗
			</a>
		{/if}
		{#if artist.spotify_url}
			<a href={artist.spotify_url} target="_blank" rel="noopener" class="btn btn-secondary">
				Spotify ↗
			</a>
		{/if}
	</div>
</div>

<style>
	.artist-detail {
		display: flex;
		flex-direction: column;
		gap: var(--space-xl);
	}

	.artist-image {
		width: 200px;
		height: 200px;
		object-fit: cover;
		border-radius: var(--radius-lg);
	}

	.artist-image.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 4rem;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
	}

	h1 {
		font-size: 2rem;
	}

	h2 {
		font-size: 1.25rem;
		margin-bottom: var(--space-sm);
	}

	.genres {
		flex-wrap: wrap;
	}
</style>
