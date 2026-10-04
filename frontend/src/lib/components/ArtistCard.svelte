<script lang="ts">
	import type { ArtistSummary } from '$lib/types';
	import FavoriteToggle from './FavoriteToggle.svelte';
	
	interface Props {
		artist: ArtistSummary;
	}
	
	let { artist }: Props = $props();
	let imgFailed = $state(false);
	
	function formatNumber(num: number | null | undefined): string {
		if (num == null || num === 0) return '—';
		if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
		if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
		return num.toString();
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
</script>

<a href="/artist/{artist.slug}" class="artist-card block">
	<div class="image-wrapper">
		{#if artist.image_url && !imgFailed}
			<img 
				src={artist.image_url} 
				alt={artist.name} 
				loading="lazy" 
				onerror={() => imgFailed = true}
			/>
		{:else}
			<div class="placeholder flex-center" style="background: {getInitialBg(artist.name)}">
				<span class="initial-letter">{artist.name.charAt(0).toUpperCase()}</span>
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
		<h4 class="artist-name" title={artist.name}>{artist.name}</h4>
		<div class="stats text-sm text-secondary mb-sm">
			<span title="Last.fm Listeners">👥 {formatNumber(artist.lastfm_listeners)}</span>
			<span title="Playcount">▶ {formatNumber(artist.lastfm_playcount)}</span>
		</div>
		
		<div class="tags flex wrap gap-xs">
			{#each (artist.genres || []).filter(g => g && g !== '1' && !/^\d+$/.test(g)).slice(0, 2) as genre (genre)}
				<span class="tag">{genre}</span>
			{/each}
			{#if (artist.styles || []).length > 0 && (artist.genres || []).filter(g => g && g !== '1').length < 2}
				{#each (artist.styles || []).filter(s => s && s !== '1' && !/^\d+$/.test(s)).slice(0, 2 - (artist.genres || []).filter(g => g && g !== '1').length) as style (style)}
					<span class="tag style-tag">{style}</span>
				{/each}
			{/if}
			{#if ((artist.genres || []).filter(g => g && g !== '1').length + (artist.styles || []).filter(s => s && s !== '1').length) > 2}
				<span class="tag more-tag">+{((artist.genres || []).filter(g => g && g !== '1').length + (artist.styles || []).filter(s => s && s !== '1').length) - 2}</span>
			{/if}
		</div>
	</div>
</a>

<style>
	.artist-card {
		background: var(--card-bg);
		border-radius: var(--radius-lg);
		overflow: hidden;
		transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease, border-color 0.2s ease;
		text-decoration: none;
		color: inherit;
		border: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		height: 100%;
		position: relative;
	}
	
	.artist-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
		border-color: var(--accent);
	}
	
	.image-wrapper {
		width: 100%;
		aspect-ratio: 1;
		position: relative;
		overflow: hidden;
		background: var(--bg-secondary);
	}
	
	.image-wrapper img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		transition: transform 0.3s ease;
	}

	.artist-card:hover .image-wrapper img {
		transform: scale(1.04);
	}
	
	.placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.initial-letter {
		font-size: 2.5rem;
		font-weight: 800;
		color: #ffffff;
		text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
	}
	
	.lidarr-badge {
		background: var(--success);
		color: #ffffff;
		width: 22px;
		height: 22px;
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		font-weight: 800;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
	}
	
	.card-actions {
		position: absolute;
		top: 8px;
		right: 8px;
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
		align-items: center;
		z-index: 2;
	}
	
	.content {
		padding: 0.85rem 1rem 1rem;
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.artist-name {
		font-size: 0.95rem;
		font-weight: 700;
		margin: 0 0 0.35rem;
		color: var(--text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		line-height: 1.3;
	}
	
	.stats {
		display: flex;
		gap: 0.75rem;
		font-size: 0.75rem;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
	}

	.tag {
		font-size: 0.7rem;
		padding: 2px 6px;
		background: var(--bg-secondary);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		white-space: nowrap;
		max-width: 100px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.style-tag {
		border: 1px solid var(--border);
	}

	.more-tag {
		background: none;
		color: var(--accent);
		font-weight: 600;
	}
</style>
