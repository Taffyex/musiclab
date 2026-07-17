<script lang="ts">
	import type { ReleaseWithArtist } from '$lib/types';
	
	interface Props {
		releases: ReleaseWithArtist[];
	}
	
	let { releases }: Props = $props();
</script>

<div class="credit-grid mt-xl">
	<h3 class="font-bold text-lg mb-md">Associated Releases</h3>
	
	{#if releases.length === 0}
		<p class="text-secondary">No releases found.</p>
	{:else}
		<div class="grid">
			{#each releases as release}
				<div class="release-card">
					<div class="cover">
						{#if release.cover_url}
							<img src={release.cover_url} alt={release.title} loading="lazy" />
						{:else}
							<div class="placeholder"></div>
						{/if}
					</div>
					
					<div class="info">
						<div class="title font-bold text-sm truncate">{release.title}</div>
						<a href="/artist/{release.artist_slug}" class="artist truncate text-xs">
							{release.artist_name}
						</a>
						<div class="meta flex-between text-xs text-secondary mt-xs">
							<span>{release.year || '----'}</span>
							<span>{release.role}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 1.5rem;
	}
	
	.release-card {
		background: var(--bg-surface, #1e1e2e);
		border-radius: var(--radius-md, 8px);
		border: 1px solid var(--border-color, #333);
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	
	.cover {
		width: 100%;
		aspect-ratio: 1;
	}
	
	.cover img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	
	.placeholder {
		width: 100%;
		height: 100%;
		background: var(--bg-hover, #2a2a3e);
	}
	
	.info {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.truncate {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.artist {
		color: var(--accent, #6c5ce7);
		text-decoration: none;
	}
	
	.artist:hover {
		text-decoration: underline;
	}
</style>
