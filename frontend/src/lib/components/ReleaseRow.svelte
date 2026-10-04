<script lang="ts">
	import type { ReleaseDetail } from '$lib/types';
	
	interface Props {
		release: ReleaseDetail;
	}
	
	let { release }: Props = $props();
	
	let expanded = $state(false);
	
	function toggleCredits() {
		expanded = !expanded;
	}
	
	function addToLidarr() {
		// Stub for per-album lidarr add
		alert(`Adding ${release.title} to Lidarr`);
	}
</script>

<div class="release-row">
	<div class="release-main flex items-center gap-md">
		<div class="cover">
			{#if release.cover_url}
				<img src={release.cover_url} alt={release.title} loading="lazy" />
			{:else}
				<div class="cover-placeholder"></div>
			{/if}
		</div>
		
		<div class="info flex-col">
			<span class="font-bold">{release.title}</span>
			<span class="text-sm text-secondary">
				{release.year || 'Unknown'} • {release.release_type || 'Release'} • {release.label || 'Independent'}
			</span>
		</div>
		
		<div class="actions ml-auto flex gap-sm">
			<button class="credits-btn" onclick={toggleCredits}>
				{expanded ? 'Hide Credits' : 'Credits'}
			</button>
			<button class="lidarr-album-btn" onclick={addToLidarr} title="Add Album to Lidarr">
				+ Lidarr
			</button>
		</div>
	</div>
	
	{#if expanded}
		<div class="credits-panel mt-sm">
			{#if release.credits && release.credits.length > 0}
				<ul class="credits-list">
					{#each release.credits as credit (credit.id || credit.entity_slug)}
						<li>
							<span class="role">{credit.role}:</span> 
							<a href="/credit/{credit.entity_slug}" class="entity">{credit.entity_name}</a>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="text-sm text-secondary">No credits available.</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.release-row {
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.5rem 1rem;
	}
	
	.cover {
		width: 48px;
		height: 48px;
		flex-shrink: 0;
		border-radius: var(--radius-sm);
		overflow: hidden;
	}
	
	.cover img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.cover-placeholder {
		width: 100%;
		height: 100%;
		background: var(--bg-secondary);
	}
	
	.credits-btn, .lidarr-album-btn {
		background: none;
		border: 1px solid var(--border);
		color: var(--text-secondary);
		padding: 0.25rem 0.75rem;
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-size: 0.8rem;
	}
	
	.credits-btn:hover {
		border-color: var(--accent);
		color: var(--accent);
	}
	
	.lidarr-album-btn:hover {
		border-color: var(--success);
		color: var(--success);
	}
	
	.credits-panel {
		border-top: 1px solid var(--border);
		padding-top: 0.5rem;
		padding-left: 3rem;
	}
	
	.credits-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 0.5rem;
		font-size: 0.85rem;
	}
	
	.role {
		color: var(--text-secondary);
	}
	
	.entity {
		color: var(--accent);
		text-decoration: none;
	}
	
	.entity:hover {
		text-decoration: underline;
	}
</style>
