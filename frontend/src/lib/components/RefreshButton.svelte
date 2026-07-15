<script lang="ts">
	import { refreshProfile } from '$lib/stores/profile';
	import { loading } from '$lib/stores/profile';

	interface Props {
		label?: string;
	}

	let { label = 'Refresh Profile' }: Props = $props();

	async function handleClick() {
		await refreshProfile();
	}
</script>

<button
	class="btn btn-secondary refresh-btn"
	onclick={handleClick}
	disabled={$loading}
>
	{#if $loading}
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
