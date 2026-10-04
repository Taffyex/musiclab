<script lang="ts">
	import type { LastfmProfile } from '$lib/types';
	
	interface Props {
		profile?: LastfmProfile | null;
		loading?: boolean;
		error?: string | null;
	}
	let { profile = null, loading = false, error = null }: Props = $props();
</script>

<div class="card taste-profile">
	<h2 class="text-2xl font-bold mb-md">Your Musical Taste</h2>
	
	{#if loading}
		<div class="flex-center py-xl">
			<div class="spinner"></div>
		</div>
	{:else if error}
		<div class="error-msg">{error}</div>
	{:else if profile}
		<div class="grid grid-cols-2 gap-lg profile-content">
			<div class="section">
				<h3 class="text-lg font-medium text-secondary mb-sm">Top Artists</h3>
				<ul class="flex-col gap-xs">
					{#each profile.top_artists.slice(0, 5) as artist (artist.url || artist.name)}
						<li class="flex-between">
							<a href={artist.url} target="_blank" rel="noopener noreferrer">{artist.name}</a>
							<span class="text-sm text-secondary">{artist.playcount} plays</span>
						</li>
					{/each}
				</ul>
			</div>
			
			<div class="section">
				<h3 class="text-lg font-medium text-secondary mb-sm">Top Genres</h3>
				<div class="flex gap-sm wrap">
					{#each profile.top_tags as genre (genre.name)}
						<span class="tag">{genre.name}</span>
					{/each}
				</div>
			</div>
		</div>
		
		<div class="section mt-lg">
			<h3 class="text-lg font-medium text-secondary mb-sm">Recent Tracks</h3>
			<ul class="flex-col gap-xs">
				{#each profile.recent_tracks.slice(0, 3) as track (track.name + (track.timestamp || ''))}
					<li class="track-item flex gap-sm">
						<span class="font-medium">{track.name}</span>
						<span class="text-secondary">by {track.artist}</span>
					</li>
				{/each}
			</ul>
		</div>
	{:else}
		<div class="text-secondary py-md">No profile data available.</div>
	{/if}
</div>

<style>
	.taste-profile {
		background: linear-gradient(135deg, var(--card-bg), var(--bg));
	}
	
	.track-item {
		padding: var(--space-xs) 0;
		border-bottom: 1px solid var(--border);
	}
	.track-item:last-child {
		border-bottom: none;
	}
</style>
