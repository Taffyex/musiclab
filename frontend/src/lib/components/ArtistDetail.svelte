<script lang="ts">
	import type { DiscoveryCard } from '$lib/types';
	import { apiClient } from '$lib/api';
	import DiscoveryCardComp from './DiscoveryCard.svelte';
	import LidarrConfirm from './LidarrConfirm.svelte';

	let { artist } = $props<{ artist: DiscoveryCard }>();

	let similarArtists = $state<DiscoveryCard[] | null>(null);
	let loadingSimilar = $state(false);
	let errorSimilar = $state('');
	
	let showLidarrConfirm = $state(false);

	async function exploreSimilar() {
		loadingSimilar = true;
		errorSimilar = '';
		try {
			// using count=4 for a nice grid
			similarArtists = await apiClient.discovery.explore(artist.artist_name, 4);
		} catch (err: any) {
			errorSimilar = err.message || 'Failed to find similar artists.';
		} finally {
			loadingSimilar = false;
		}
	}

	function getMbid() {
		return artist.mb_data?.mbid || artist.id;
	}
</script>

<div class="artist-detail flex-col gap-xl">
	<div class="header-section flex-between items-center card">
		<div>
			<h1 class="text-3xl font-bold text-primary mb-xs">{artist.artist_name}</h1>
			{#if artist.era}
				<p class="text-sm text-secondary">Era: {artist.era}</p>
			{/if}
			<div class="tags flex gap-xs wrap mt-sm">
				{#each artist.genre_tags as tag}
					<span class="tag">{tag}</span>
				{/each}
			</div>
		</div>
		<div class="actions">
			{#if artist.already_in_lidarr}
				<span class="badge success-badge text-lg">In Lidarr Library</span>
			{:else}
				<button class="btn btn-primary text-lg" onclick={() => showLidarrConfirm = true}>
					Add to Lidarr
				</button>
			{/if}
		</div>
	</div>

	{#if showLidarrConfirm}
		<div class="lidarr-confirm-wrapper max-w-md">
			<LidarrConfirm 
				artistName={artist.artist_name}
				foreignArtistId={getMbid()}
				onCancel={() => showLidarrConfirm = false}
				onSuccess={() => {
					showLidarrConfirm = false;
					artist.already_in_lidarr = true;
				}}
			/>
		</div>
	{/if}

	<div class="info-grid grid gap-xl">
		<div class="card flex-col gap-md">
			<h3 class="text-xl font-bold">Why it matches your taste</h3>
			<p class="text-secondary leading-relaxed">{artist.why_it_matches}</p>
			
			<h3 class="text-xl font-bold mt-sm">AI Blurb</h3>
			<p class="text-secondary leading-relaxed">{artist.ai_blurb}</p>
		</div>

		<div class="card flex-col gap-md stats-card">
			<h3 class="text-xl font-bold">Stats</h3>
			<div class="stat-item flex-between border-b pb-sm">
				<span class="text-secondary">Last.fm Listeners</span>
				<span class="font-bold">{artist.lastfm_listeners?.toLocaleString() || 'N/A'}</span>
			</div>
			<div class="stat-item flex-between border-b pb-sm">
				<span class="text-secondary">Last.fm Playcount</span>
				<span class="font-bold">{artist.lastfm_playcount?.toLocaleString() || 'N/A'}</span>
			</div>
			{#if artist.mb_data}
				<div class="stat-item flex-between border-b pb-sm">
					<span class="text-secondary">Country</span>
					<span class="font-bold">{artist.mb_data.country || 'N/A'}</span>
				</div>
				<div class="stat-item flex-between pb-sm">
					<span class="text-secondary">Type</span>
					<span class="font-bold capitalize">{artist.mb_data.type || 'N/A'}</span>
				</div>
			{/if}
		</div>
	</div>

	<div class="explore-section card">
		<div class="flex-between items-center mb-lg">
			<h2 class="text-2xl font-bold">Explore Similar</h2>
			{#if !similarArtists && !loadingSimilar}
				<button class="btn btn-secondary" onclick={exploreSimilar}>
					Find Similar Artists
				</button>
			{/if}
		</div>

		{#if loadingSimilar}
			<div class="flex-center py-2xl">
				<div class="spinner"></div>
			</div>
		{/if}

		{#if errorSimilar}
			<div class="error-msg">{errorSimilar}</div>
		{/if}

		{#if similarArtists}
			<div class="grid grid-cols-4 recommendations-grid">
				{#each similarArtists as sim}
					<DiscoveryCardComp item={sim} />
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.gap-xl { gap: var(--space-xl); }
	.gap-xs { gap: var(--space-xs); }
	.mt-sm { margin-top: var(--space-sm); }
	.mb-xs { margin-bottom: var(--space-xs); }
	.mb-lg { margin-bottom: var(--space-lg); }
	.wrap { flex-wrap: wrap; }
	.items-center { align-items: center; }
	.border-b { border-bottom: 1px solid var(--border); }
	.pb-sm { padding-bottom: var(--space-sm); }
	.py-2xl { padding: var(--space-2xl) 0; }
	.leading-relaxed { line-height: 1.6; }
	.capitalize { text-transform: capitalize; }
	.max-w-md { max-width: 400px; margin-bottom: var(--space-xl); }

	.info-grid {
		grid-template-columns: 2fr 1fr;
	}

	.success-badge {
		background: rgba(46, 204, 113, 0.1);
		color: #2ecc71;
		padding: 8px 16px;
		border-radius: var(--radius-md);
		font-weight: bold;
	}

	.error-msg {
		color: var(--error);
		background: rgba(225, 112, 85, 0.1);
		padding: var(--space-md);
		border-radius: var(--radius-md);
	}

	@media (max-width: 768px) {
		.info-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
