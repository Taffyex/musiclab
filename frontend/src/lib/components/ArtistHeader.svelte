<script lang="ts">
	import type { ArtistDetail } from '$lib/types';
	import { slugify } from '$lib/utils/slugify';
	import LidarrQuickAdd from './LidarrQuickAdd.svelte';
	import FavoriteToggle from './FavoriteToggle.svelte';
	
	interface Props {
		artist: ArtistDetail;
	}
	
	let { artist }: Props = $props();
	let imgFailed = $state(false);
	
	function formatNumber(num: number | null | undefined): string {
		if (num == null) return 'N/A';
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
		return num.toLocaleString();
	}
	
	function getInitialBg(name: string): string {
		const gradients = [
			'linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)',
			'linear-gradient(135deg, #0984e3 0%, #74b9ff 100%)',
			'linear-gradient(135deg, #00b894 0%, #55efc4 100%)',
			'linear-gradient(135deg, #e17055 0%, #fab1a0 100%)',
			'linear-gradient(135deg, #d63031 0%, #ff7675 100%)',
			'linear-gradient(135deg, #fd79a8 0%, #e84393 100%)',
			'linear-gradient(135deg, #6c5ce7 0%, #fd79a8 100%)',
			'linear-gradient(135deg, #00cec9 0%, #81ecec 100%)'
		];
		let hash = 0;
		for (let i = 0; i < name.length; i++) {
			hash = name.charCodeAt(i) + ((hash << 5) - hash);
		}
		const index = Math.abs(hash) % gradients.length;
		return gradients[index];
	}

	function handleLidarrAdd() {
		console.log(`Adding ${artist.name} to Lidarr`);
	}
</script>

<div class="artist-header flex gap-lg wrap items-center">
	<div class="image-container">
		{#if artist.image_url && !imgFailed}
			<img 
				src={artist.image_url} 
				alt={artist.name} 
				onerror={() => imgFailed = true}
			/>
		{:else}
			<div class="placeholder flex-center" style="background: {getInitialBg(artist.name)}">
				<span class="avatar-letter font-bold">{artist.name.charAt(0).toUpperCase()}</span>
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
			{#each artist.genres as genre (genre)}
				<a href="/explore?genre={slugify(genre)}" class="tag genre-tag">{genre}</a>
			{/each}
			{#each artist.styles as style (style)}
				<a href="/explore?style={slugify(style)}" class="tag style-tag">{style}</a>
			{/each}
		</div>
		
		<div class="stats text-sm mt-xs">
			<strong>{formatNumber(artist.lastfm_listeners)}</strong> Listeners | 
			<strong>{formatNumber(artist.lastfm_playcount)}</strong> Scrobbles
		</div>
		
		<div class="actions mt-sm flex gap-sm items-center">
			<FavoriteToggle 
				entity_type="artist"
				entity_id={artist.id}
				name={artist.name}
				slug={artist.slug}
				image_url={artist.image_url}
			/>
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
		background: var(--card-bg);
		padding: 2rem;
		border-radius: var(--radius-lg);
		border: 1px solid var(--border);
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
	}
	
	.image-container {
		width: 180px;
		height: 180px;
		border-radius: 50%;
		overflow: hidden;
		flex-shrink: 0;
		border: 4px solid var(--border);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
	}
	
	.image-container img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.avatar-letter {
		font-size: 4rem;
		color: #ffffff;
		text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
	}
	
	.info-container {
		flex: 1;
		min-width: 250px;
	}
	
	.meta {
		display: flex;
		gap: var(--space-md);
		flex-wrap: wrap;
	}
	
	.tag {
		padding: 0.25rem 0.75rem;
		border-radius: var(--radius-full);
		font-size: 0.8rem;
		text-decoration: none;
		font-weight: 500;
	}
	
	.genre-tag {
		background: rgba(108, 92, 231, 0.15);
		color: var(--accent);
		border: 1px solid rgba(108, 92, 231, 0.3);
	}
	
	.style-tag {
		background: var(--bg-secondary);
		color: var(--text-secondary);
		border: 1px solid var(--border);
	}
	
	.tag:hover {
		opacity: 0.85;
		transform: translateY(-1px);
	}
</style>
