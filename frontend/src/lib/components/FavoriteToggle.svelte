<script lang="ts">
	import { favoritesStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import type { FavoriteItem } from '$lib/types';

	interface Props {
		entity_type: 'artist' | 'genre' | 'style';
		entity_id: number;
		name: string;
		slug: string;
		image_url?: string;
		/** Optional: override the CSS class on the button */
		class?: string;
	}

	let { entity_type, entity_id, name, slug, image_url = '', class: klass = '' }: Props = $props();

	let isFav = $derived($favoritesStore[entity_type + 's' as keyof typeof $favoritesStore]?.some(
		(f: FavoriteItem) => f.entity_id === entity_id
	) ?? false);

	async function toggle(e: Event) {
		e.preventDefault();
		e.stopPropagation();
		const wasFav = isFav;
		const item: FavoriteItem = { entity_type, entity_id, name, slug, image_url };

		if (wasFav) {
			favoritesStore.remove(entity_type, entity_id);
		} else {
			favoritesStore.add(item);
		}

		try {
			if (wasFav) {
				await apiClient.explore.removeFavorite(entity_type, entity_id);
			} else {
				await apiClient.explore.addFavorite(entity_type, entity_id);
			}
		} catch {
			// Revert on failure
			if (wasFav) {
				favoritesStore.add(item);
			} else {
				favoritesStore.remove(entity_type, entity_id);
			}
		}
	}
</script>

<button class="fav-toggle {klass}" class:active={isFav} onclick={toggle} aria-label={isFav ? 'Remove favorite' : 'Add favorite'}>
	{isFav ? '❤️' : '🤍'}
</button>

<style>
	.fav-toggle {
		background: none;
		border: none;
		cursor: pointer;
		font-size: 1.2rem;
		padding: 0.2rem;
		transition: transform 0.15s;
		line-height: 1;
	}
	.fav-toggle:hover { transform: scale(1.2); }
	.fav-toggle.active { animation: pop 0.3s ease; }
	@keyframes pop {
		0% { transform: scale(1); }
		50% { transform: scale(1.4); }
		100% { transform: scale(1); }
	}
</style>
