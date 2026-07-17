<script lang="ts">
	import { onMount } from 'svelte';
	import { themeStore, userStore, favoritesStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import Navbar from '$lib/components/Navbar.svelte';
	import '../app.css';

	let { children } = $props();

	onMount(async () => {
		themeStore.init();
		
		try {
			const res = await apiClient.auth.me();
			if (res.user) {
				userStore.login(res.user);
				apiClient.explore.getFavorites().then(data => favoritesStore.set(data));
			}
		} catch (e) {
			// Not logged in or error
			console.log('Not logged in on load');
		}
	});
</script>

<div class="app-layout">
	<Navbar />
	<main class="container">
		{@render children()}
	</main>
</div>

<style>
	.app-layout {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	main {
		flex: 1;
		padding-top: var(--space-xl);
		padding-bottom: var(--space-xl);
	}
</style>
