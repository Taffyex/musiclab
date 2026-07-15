<script lang="ts">
	import { themeStore } from '$lib/stores';
</script>

<button
	class="btn btn-secondary theme-toggle"
	onclick={themeStore.toggle}
	aria-label="Toggle theme"
>
	{#if $themeStore === 'light'}
		🌙 Dark
	{:else}
		☀️ Light
	{/if}
</button>

<style>
	.theme-toggle {
		font-size: 1.25rem;
		padding: 0.375rem;
		border-radius: var(--radius-full);
		line-height: 1;
	}

	.icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.5rem;
		height: 1.5rem;
	}
</style>
