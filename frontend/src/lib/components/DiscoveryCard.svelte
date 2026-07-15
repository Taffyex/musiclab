<script lang="ts">
	import type { DiscoveryCard } from '$lib/types';
	import LidarrConfirm from './LidarrConfirm.svelte';
	interface Props {
		item: DiscoveryCard;
	}
	let { item }: Props = $props();
	
	let showLidarrConfirm = $state(false);

	function getMbid() {
		return item.mb_data?.mbid || item.id;
	}
</script>

<div class="card discovery-card flex-col gap-sm">
	<div class="header flex-between">
		<h3 class="text-xl font-bold">
			<a href="/discover/{item.id}" class="text-primary hover-underline">{item.artist_name}</a>
		</h3>
		{#if item.already_in_lidarr}
			<span class="score-badge lidarr-badge">In Lidarr</span>
		{/if}
	</div>
	
	<p class="text-secondary text-sm reason">{item.why_it_matches || item.ai_blurb}</p>
	
	<div class="tags flex gap-xs wrap mt-sm">
		{#each item.genre_tags as tag}
			<span class="tag">{tag}</span>
		{/each}
	</div>
	
	<div class="links flex gap-sm mt-md">
		<a href="/discover/{item.id}" class="btn btn-secondary text-sm platform-btn">
			View Details
		</a>
		{#if !item.already_in_lidarr}
			<button class="btn btn-primary text-sm platform-btn" onclick={() => showLidarrConfirm = true}>
				Add to Lidarr
			</button>
		{/if}
	</div>

	{#if showLidarrConfirm}
		<div class="mt-md lidarr-confirm-wrapper">
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
	}
	
	.score-badge {
		background: rgba(108, 92, 231, 0.1);
		color: var(--accent);
		padding: 4px 8px;
		border-radius: var(--radius-sm);
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.lidarr-badge {
		background: rgba(46, 204, 113, 0.1);
		color: #2ecc71;
	}

	.hover-underline:hover {
		text-decoration: underline;
	}
	
	.reason {
		flex-grow: 1;
	}
	.mt-md { margin-top: var(--space-md); }
	
	.platform-btn {
		flex: 1;
		text-transform: capitalize;
	}
</style>
