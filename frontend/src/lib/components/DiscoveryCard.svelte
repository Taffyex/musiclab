<script lang="ts">
	import type { DiscoveryCardItem } from '$lib/stores';
	let { item }: { item: DiscoveryCardItem } = $props();
</script>

<div class="card discovery-card flex-col gap-sm">
	<div class="header flex-between">
		<h3 class="text-xl font-bold">{item.artist_name}</h3>
		<span class="score-badge">{(item.similarity_score * 100).toFixed(0)}% Match</span>
	</div>
	
	<p class="text-secondary text-sm reason">{item.reason}</p>
	
	<div class="tags flex gap-xs wrap mt-sm">
		{#each item.tags as tag}
			<span class="tag">{tag}</span>
		{/each}
	</div>
	
	<div class="links flex gap-sm mt-md">
		{#each Object.entries(item.listen_links) as [platform, url]}
			<a href={url} target="_blank" rel="noopener noreferrer" class="btn btn-secondary text-sm platform-btn">
				Listen on {platform}
			</a>
		{/each}
	</div>
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
	
	.reason {
		flex-grow: 1;
	}
	
	.gap-xs { gap: var(--space-xs); }
	.mt-sm { margin-top: var(--space-sm); }
	.mt-md { margin-top: var(--space-md); }
	.wrap { flex-wrap: wrap; }
	
	.platform-btn {
		flex: 1;
		text-transform: capitalize;
	}
</style>
