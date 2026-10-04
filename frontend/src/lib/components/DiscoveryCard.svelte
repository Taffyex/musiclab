<script lang="ts">
	import type { DiscoveryCard } from '$lib/types';
	import { slugify } from '$lib/utils/slugify';
	import LidarrConfirm from './LidarrConfirm.svelte';

	interface Props {
		item: DiscoveryCard;
		/** Optional 0–100 animated entrance delay index */
		index?: number;
	}

	let { item, index = 0 }: Props = $props();
	
	let showLidarrConfirm = $state(false);
	let imgFailed = $state(false);

	function getMbid() {
		return item.mb_data?.mbid || item.id;
	}

	function getPopularityTier(listeners: number | null | undefined): 'iconic' | 'popular' | 'emerging' | 'hidden' {
		if (!listeners) return 'hidden';
		if (listeners >= 2_000_000) return 'iconic';
		if (listeners >= 500_000) return 'popular';
		if (listeners >= 50_000) return 'emerging';
		return 'hidden';
	}

	function formatNumber(n: number | null | undefined): string {
		if (n == null) return '—';
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K';
		return n.toLocaleString();
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
		const idx = Math.abs(hash) % gradients.length;
		return gradients[idx];
	}

	let tier = $derived(getPopularityTier(item.lastfm_listeners));
	let popularityPct = $derived(Math.min(100, ((item.lastfm_listeners ?? 0) / 3_000_000) * 100));
</script>

<div 
	class="card discovery-card flex-col gap-sm"
	style:animation-delay="{index * 60}ms"
>
	<!-- Popularity bar at the top edge -->
	<div class="match-bar-wrapper">
		<div class="match-bar" style:width="{popularityPct}%"></div>
	</div>

	<div class="header flex items-center gap-sm">
		<div class="avatar-wrapper">
			{#if item.image_url && !imgFailed}
				<img 
					src={item.image_url} 
					alt={item.artist_name} 
					class="artist-avatar"
					loading="lazy"
					onerror={() => imgFailed = true}
				/>
			{:else}
				<div class="avatar-placeholder flex-center" style="background: {getInitialBg(item.artist_name)}">
					<span>{item.artist_name.charAt(0).toUpperCase()}</span>
				</div>
			{/if}
		</div>

		<div class="header-info flex-col flex-1">
			<h3 class="artist-name">
				<a href="/artist/{slugify(item.artist_name)}" class="artist-link">{item.artist_name}</a>
			</h3>
			{#if item.lastfm_listeners}
				<div class="popularity-meta text-xs">
					<span class="meta-item">👥 {formatNumber(item.lastfm_listeners)} listeners</span>
				</div>
			{/if}
		</div>

		<div class="badges">
			{#if item.already_in_lidarr}
				<span class="badge lidarr-badge" title="Already in your Lidarr library">✓ Lidarr</span>
			{/if}
			<span class="badge tier-badge tier-{tier}" title="Popularity tier">{tier}</span>
		</div>
	</div>

	<!-- AI Blurb -->
	<p class="reason text-secondary text-sm">{item.why_it_matches || item.ai_blurb}</p>

	<!-- Genre / Style Tags -->
	<div class="tags flex gap-xs wrap">
		{#if item.era}
			<span class="tag era-tag">{item.era}</span>
		{/if}
		{#each item.genre_tags as tag (tag)}
			<a href="/explore?tag={slugify(tag)}" class="tag genre-tag">{tag}</a>
		{/each}
	</div>

	<div class="divider"></div>

	<!-- Actions -->
	<div class="links flex gap-sm">
		<a href="/artist/{slugify(item.artist_name)}" class="btn btn-secondary text-sm action-btn">
			View Details
		</a>
		{#if !item.already_in_lidarr}
			<button class="btn btn-primary text-sm action-btn" onclick={() => showLidarrConfirm = true}>
				+ Lidarr
			</button>
		{/if}
	</div>

	{#if showLidarrConfirm}
		<div class="mt-sm lidarr-confirm-wrapper">
			<LidarrConfirm 
				artistName={item.artist_name}
				foreignArtistId={getMbid()}
				onCancel={() => showLidarrConfirm = false}
				onSuccess={() => {
					showLidarrConfirm = false;
					item.already_in_lidarr = true;
				}}
			/>
		</div>
	{/if}
</div>

<style>
	.discovery-card {
		height: 100%;
		display: flex;
		flex-direction: column;
		animation: cardEntrance 0.4s ease-out both;
		overflow: hidden;
		padding-top: 0; /* bar sits flush at top */
	}

	@keyframes cardEntrance {
		from {
			opacity: 0;
			transform: translateY(12px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.discovery-card:hover {
		transform: translateY(-3px);
		box-shadow: var(--shadow-lg);
		border-color: rgba(108, 92, 231, 0.3);
	}

	/* Match/popularity bar */
	.match-bar-wrapper {
		height: 3px;
		background: var(--border);
		margin: 0 calc(-1 * var(--space-lg)) var(--space-md);
		border-radius: 0;
	}

	.match-bar {
		height: 100%;
		background: linear-gradient(90deg, var(--accent), var(--info, #74b9ff));
		border-radius: 0 2px 2px 0;
		transition: width 0.6s ease;
	}

	/* Header area */
	.header {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
	}

	.avatar-wrapper {
		width: 46px;
		height: 46px;
		border-radius: 50%;
		overflow: hidden;
		flex-shrink: 0;
		border: 2px solid var(--border);
	}

	.artist-avatar {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.avatar-placeholder {
		width: 100%;
		height: 100%;
		color: #ffffff;
		font-weight: 700;
		font-size: 1.1rem;
	}

	.header-info {
		min-width: 0;
	}

	.artist-name {
		margin: 0;
		font-size: 1.05rem;
		font-weight: 700;
		line-height: 1.3;
	}

	.artist-link {
		color: var(--text);
		text-decoration: none;
		display: -webkit-box;
		-webkit-line-clamp: 1;
		line-clamp: 1;
		-webkit-box-orient: vertical;
		overflow: hidden;
		transition: color var(--transition-fast);
	}

	.artist-link:hover {
		color: var(--accent);
	}

	/* Badges */
	.badges {
		display: flex;
		flex-direction: column;
		gap: 4px;
		align-items: flex-end;
		flex-shrink: 0;
	}

	.badge {
		padding: 2px 8px;
		border-radius: var(--radius-sm);
		font-size: 0.7rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.lidarr-badge {
		background: rgba(0, 184, 148, 0.15);
		color: var(--success);
	}

	/* Popularity tier badge */
	.tier-iconic {
		background: rgba(253, 203, 110, 0.2);
		color: #b8860b;
	}
	.tier-popular {
		background: rgba(108, 92, 231, 0.15);
		color: var(--accent);
	}
	.tier-emerging {
		background: rgba(0, 184, 148, 0.15);
		color: var(--success);
	}
	.tier-hidden {
		background: var(--bg);
		color: var(--text-secondary);
	}

	/* Popularity meta */
	.popularity-meta {
		display: flex;
		gap: var(--space-sm);
		flex-wrap: wrap;
		color: var(--text-secondary);
	}

	.meta-item {
		white-space: nowrap;
	}

	/* AI reason */
	.reason {
		flex-grow: 1;
		line-height: 1.5;
		display: -webkit-box;
		-webkit-line-clamp: 4;
		line-clamp: 4;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	/* Tags */
	.era-tag {
		background: var(--accent);
		color: #ffffff;
		border-color: transparent;
	}

	.genre-tag {
		color: var(--accent);
		background: rgba(108, 92, 231, 0.1);
		border-color: rgba(108, 92, 231, 0.2);
		text-decoration: none;
		transition: background var(--transition-fast);
	}

	.genre-tag:hover {
		background: rgba(108, 92, 231, 0.2);
	}

	/* Divider */
	.divider {
		height: 1px;
		background: var(--border);
		margin: var(--space-xs) 0;
	}

	/* Action buttons */
	.action-btn {
		flex: 1;
		justify-content: center;
	}
</style>
