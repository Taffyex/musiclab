<script lang="ts">
	import { favoritesStore } from '$lib/stores';
	import ArtistCard from '$lib/components/ArtistCard.svelte';
</script>

<div class="favorites-page p-lg">
	<h1 class="text-2xl font-bold mb-lg">Your Favorites</h1>

	<section class="mb-xl">
		<h2 class="text-2xl font-bold mb-md text-secondary">Artists</h2>
		{#if $favoritesStore.artists.length > 0}
			<div class="favorites-grid gap-md">
				{#each $favoritesStore.artists as artist (artist.entity_id)}
					<ArtistCard
						artist={{
							id: artist.entity_id,
							name: artist.name,
							slug: artist.slug,
							image_url: artist.image_url || '',
							lastfm_listeners: null,
							lastfm_playcount: null,
							genres: [],
							styles: [],
							already_in_lidarr: false
						}}
					/>
				{/each}
			</div>
		{:else}
			<p class="text-secondary text-lg">No favorite artists yet.</p>
		{/if}
	</section>

	<div class="genre-style-grid gap-xl">
		<section>
			<h2 class="text-2xl font-bold mb-md text-secondary">Genres</h2>
			{#if $favoritesStore.genres.length > 0}
				<div class="flex wrap gap-sm">
					{#each $favoritesStore.genres as genre (genre.entity_id)}
						<a href="/explore?genre={genre.slug}" class="tag genre-tag text-lg px-md py-sm">
							{genre.name}
						</a>
					{/each}
				</div>
			{:else}
				<p class="text-secondary text-lg">No favorite genres yet.</p>
			{/if}
		</section>

		<section>
			<h2 class="text-2xl font-bold mb-md text-secondary">Styles</h2>
			{#if $favoritesStore.styles.length > 0}
				<div class="flex wrap gap-sm">
					{#each $favoritesStore.styles as style (style.entity_id)}
						<a href="/explore?style={style.slug}" class="tag style-tag text-lg px-md py-sm">
							{style.name}
						</a>
					{/each}
				</div>
			{:else}
				<p class="text-secondary text-lg">No favorite styles yet.</p>
			{/if}
		</section>
	</div>
</div>

<style>
	.favorites-page {
		max-width: 1152px;
		margin: 0 auto;
	}
	.favorites-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
	}
	.genre-style-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
	}
	.tag {
		text-decoration: none;
		border-radius: var(--radius-full, 9999px);
		display: inline-block;
		transition: transform 0.2s, opacity 0.2s;
	}
	.tag:hover {
		transform: translateY(-2px);
		opacity: 0.9;
	}
	.genre-tag {
		background: var(--accent-alpha, rgba(108, 92, 231, 0.2));
		color: var(--accent, #6c5ce7);
	}
	.style-tag {
		background: var(--bg-hover, #2a2a3e);
		color: var(--text-primary, #eee);
	}
</style>
