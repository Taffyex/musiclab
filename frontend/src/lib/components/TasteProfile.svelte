<script lang="ts">
	// TODO: Add charts/visualizations for listening stats
	import type { LastfmProfile } from '$lib/types';
	import { formatNumber } from '$lib/utils/formatting';

	interface Props {
		profile: LastfmProfile;
	}

	let { profile }: Props = $props();
</script>

<div class="taste-profile">
	<div class="profile-header flex-between">
		<div>
			<h2>🎧 Your Taste Profile</h2>
			<p class="text-secondary text-sm">Last.fm: {profile.username}</p>
		</div>
		<div class="stats flex gap-lg">
			<div class="stat">
				<span class="stat-value">{formatNumber(profile.playcount)}</span>
				<span class="stat-label text-secondary text-sm">Scrobbles</span>
			</div>
			<div class="stat">
				<span class="stat-value">{formatNumber(profile.artist_count)}</span>
				<span class="stat-label text-secondary text-sm">Artists</span>
			</div>
		</div>
	</div>

	{#if profile.top_artists.length > 0}
		<section class="section">
			<h3>Top Artists</h3>
			<div class="artist-list">
				{#each profile.top_artists.slice(0, 8) as artist, i}
					<div class="artist-item flex-between">
						<div class="flex gap-sm">
							<span class="rank text-secondary">#{i + 1}</span>
							<span class="font-medium">{artist.name}</span>
						</div>
						<span class="text-secondary text-sm">{formatNumber(artist.playcount)} plays</span>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if profile.top_tags.length > 0}
		<section class="section">
			<h3>Top Tags</h3>
			<div class="flex gap-sm" style="flex-wrap: wrap;">
				{#each profile.top_tags as tag}
					<span class="tag">{tag}</span>
				{/each}
			</div>
		</section>
	{/if}

	{#if profile.recent_tracks.length > 0}
		<section class="section">
			<h3>Recent Tracks</h3>
			<div class="track-list">
				{#each profile.recent_tracks.slice(0, 5) as track}
					<div class="track-item flex gap-sm">
						<span class="font-medium">{track.name}</span>
						<span class="text-secondary">by {track.artist}</span>
					</div>
				{/each}
			</div>
		</section>
	{/if}
</div>

<style>
	.taste-profile {
		display: flex;
		flex-direction: column;
		gap: var(--space-xl);
	}

	.profile-header {
		flex-wrap: wrap;
		gap: var(--space-md);
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--accent);
	}

	.section h3 {
		margin-bottom: var(--space-md);
		font-size: 1rem;
		font-weight: 600;
	}

	.artist-list,
	.track-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.artist-item,
	.track-item {
		padding: var(--space-sm) var(--space-md);
		border-radius: var(--radius-md);
		background: var(--bg);
	}

	.rank {
		font-weight: 600;
		min-width: 2rem;
	}
</style>
