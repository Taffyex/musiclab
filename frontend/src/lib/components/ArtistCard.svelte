<script lang="ts">
	import type { ArtistSummary } from '$lib/types';
	import FavoriteToggle from './FavoriteToggle.svelte';
	
	interface Props {
		artist: ArtistSummary;
	}
	
	let { artist }: Props = $props();
	
	function formatNumber(num: number | null | undefined): string {
		if (num == null) return 'N/A';
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
		return num.toString();
	}
</script>

<a href="/artist/{artist.slug}" class="artist-card block">
	<div class="image-wrapper">
		{#if artist.image_url}
			<img src={artist.image_url} alt={artist.name} loading="lazy" />
		{:else}
			<div class="placeholder flex-center">
				<span class="text-xl font-bold">{artist.name.charAt(0)}</span>
			</div>
		{/if}
		<div class="card-actions">
			<FavoriteToggle 
				entity_type="artist"
				entity_id={artist.id}
				name={artist.name}
				slug={artist.slug}
				image_url={artist.image_url}
			/>
			{#if artist.already_in_lidarr}
				<div class="lidarr-badge" title="Already in Lidarr">✓</div>
			{/if}
		</div>
	</div>
	
	<div class="content">
		<h4 class="font-bold mb-xs">{artist.name}</h4>
		<div class="stats text-sm text-secondary mb-sm">
			<span>👥 {formatNumber(artist.lastfm_listeners)}</span>
			<span>▶ {formatNumber(artist.lastfm_playcount)}</span>
		</div>
		
		<div class="tags flex wrap gap-xs">
			{#each artist.genres.slice(0, 2) as genre}
				<span class="tag">{genre}</span>
			{/each}
			{#if artist.genres.length > 2}
				<span class="tag">+{artist.genres.length - 2}</span>
			{/if}
		</div>
	</div>
</a>

<style>
	.artist-card {
		background: var(--card-bg, #1e1e2e);
		border-radius: var(--radius-md, 8px);
		overflow: hidden;
		transition: transform 0.2s, box-shadow 0.2s;
		text-decoration: none;
		color: inherit;
		border: 1px solid var(--border, #333);
		display: flex;
		flex-direction: column;
		height: 100%;
	}
	
	.artist-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		border-color: var(--accent, #6c5ce7);
	}
	
	.image-wrapper {
		width: 100%;
		aspect-ratio: 1;
		position: relative;
		overflow: hidden;
	}
	
	.image-wrapper img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.placeholder {
		width: 100%;
		height: 100%;
		background: var(--bg-hover, #2a2a3e);
		color: var(--text-secondary, #aaa);
	}
	
	.lidarr-badge {
		background: var(--success, #2ecc71);
		color: white;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		font-weight: bold;
		box-shadow: 0 2px 4px rgba(0,0,0,0.3);
	}
	
	.card-actions {
		position: absolute;
		top: 8px;
		right: 8px;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		align-items: center;
	}
	
	.content {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		flex: 1;
	}
	
	.stats {
		display: flex;
		gap: 1rem;
	}
	
	.tag {
		background: var(--bg-hover, #2a2a3e);
		color: var(--text-secondary, #aaa);
		padding: 0.1rem 0.4rem;
		border-radius: var(--radius-sm, 4px);
		font-size: 0.75rem;
	}
</style>
