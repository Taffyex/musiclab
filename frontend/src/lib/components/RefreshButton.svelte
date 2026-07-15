<script lang="ts">
	import { profileStore } from '$lib/stores';
	import { apiClient } from '$lib/api';

	interface Props {
		label?: string;
	}

	let { label = 'Refresh Profile' }: Props = $props();
	
	let loading = $state(false);

	async function handleClick() {
		loading = true;
		try {
			const res = await apiClient.lastfm.refresh();
			profileStore.set(res);
		} catch (err) {
			console.error('Failed to refresh profile', err);
		} finally {
			loading = false;
		}
	}
</script>

<button
	class="btn btn-secondary refresh-btn"
	onclick={handleClick}
	disabled={loading}
>
	{#if loading}
		<span class="spinner"></span>
		Refreshing…
	{:else}
		🔄 {label}
	{/if}
</button>

<style>
	.refresh-btn {
		min-width: 160px;
	}
</style>
