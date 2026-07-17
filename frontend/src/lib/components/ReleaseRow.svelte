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
					{#each release.credits as credit}
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
		background: var(--bg-app, #12121c);
		border: 1px solid var(--border-color, #333);
		border-radius: var(--radius-sm, 4px);
		padding: 0.5rem 1rem;
	}
	
	.cover {
		width: 48px;
		height: 48px;
		flex-shrink: 0;
		border-radius: var(--radius-sm, 4px);
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
		background: var(--bg-hover, #2a2a3e);
	}
	
	.credits-btn, .lidarr-album-btn {
		background: none;
		border: 1px solid var(--border-color, #444);
		color: var(--text-secondary, #aaa);
		padding: 0.25rem 0.75rem;
		border-radius: var(--radius-sm, 4px);
		cursor: pointer;
		font-size: 0.8rem;
	}
	
	.credits-btn:hover {
		border-color: var(--accent, #6c5ce7);
		color: var(--accent, #6c5ce7);
	}
	
	.lidarr-album-btn:hover {
		border-color: var(--success, #2ecc71);
		color: var(--success, #2ecc71);
	}
	
	.credits-panel {
		border-top: 1px solid var(--border-color, #333);
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
		color: var(--text-secondary, #aaa);
	}
	
	.entity {
		color: var(--accent, #6c5ce7);
		text-decoration: none;
	}
	
	.entity:hover {
		text-decoration: underline;
	}
	
	.ml-auto {
		margin-left: auto;
	}
</style>
