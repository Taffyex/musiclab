<script lang="ts">
	import type { ArtistDetail } from '$lib/types';
	import LidarrQuickAdd from './LidarrQuickAdd.svelte';
	
	interface Props {
		artist: ArtistDetail;
	}
	
	let { artist }: Props = $props();
	
	function formatNumber(num: number | null | undefined): string {
		if (num == null) return 'N/A';
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
		return num.toString();
	}
	
	function handleLidarrAdd() {
		// API call to Lidarr logic goes here (stub)
		console.log(`Adding ${artist.name} to Lidarr`);
	}
</script>

<div class="artist-header flex gap-lg wrap items-center">
	<div class="image-container">
		{#if artist.image_url}
			<img src={artist.image_url} alt={artist.name} />
		{:else}
			<div class="placeholder flex-center">
				<span class="text-2xl font-bold">{artist.name.charAt(0)}</span>
			</div>
		{/if}
	</div>
	
	<div class="info-container flex-col gap-sm">
		<h1 class="text-2xl font-bold">{artist.name}</h1>
		<div class="meta text-secondary text-sm">
			{#if artist.country}<span>🌍 {artist.country}</span>{/if}
			{#if artist.begin_date}
				<span>📅 {artist.begin_date} - {artist.end_date || 'Present'}</span>
			{/if}
			{#if artist.artist_type}<span>👤 {artist.artist_type}</span>{/if}
		</div>
		
		<div class="tags flex wrap gap-xs">
			{#each artist.genres as genre}
				<a href="/explore?genre={genre}" class="tag genre-tag">{genre}</a>
			{/each}
			{#each artist.styles as style}
				<a href="/explore?style={style}" class="tag style-tag">{style}</a>
			{/each}
		</div>
		
		<div class="stats text-sm mt-xs">
			<strong>{formatNumber(artist.lastfm_listeners)}</strong> Listeners | 
			<strong>{formatNumber(artist.lastfm_playcount)}</strong> Scrobbles
		</div>
		
		<div class="actions mt-sm">
			<LidarrQuickAdd 
				artistName={artist.name} 
				alreadyInLidarr={artist.already_in_lidarr} 
				onAdd={handleLidarrAdd} 
			/>
		</div>
	</div>
</div>

<style>
	.artist-header {
		background: var(--bg-surface, #1e1e2e);
		padding: 2rem;
		border-radius: var(--radius-lg, 12px);
		border: 1px solid var(--border-color, #333);
	}
	
	.image-container {
		width: 200px;
		height: 200px;
		border-radius: 50%;
		overflow: hidden;
		flex-shrink: 0;
		border: 4px solid var(--bg-input, #2a2a3e);
	}
	
	.image-container img {
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
	
	.info-container {
		flex: 1;
		min-width: 250px;
	}
	
	.meta {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.tag {
		padding: 0.2rem 0.6rem;
		border-radius: 12px;
		font-size: 0.8rem;
		text-decoration: none;
	}
	
	.genre-tag {
		background: var(--accent-alpha, rgba(108, 92, 231, 0.2));
		color: var(--accent, #6c5ce7);
	}
	
	.style-tag {
		background: var(--bg-hover, #2a2a3e);
		color: var(--text-secondary, #aaa);
	}
	
	.tag:hover {
		opacity: 0.8;
	}
</style>
