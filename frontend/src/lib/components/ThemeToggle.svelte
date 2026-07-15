<script lang="ts">
	import { theme, toggleTheme } from '$lib/stores/theme';
</script>

<button
	class="theme-toggle btn btn-ghost"
	onclick={toggleTheme}
	aria-label="Toggle theme"
	title={$theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
>
	{#if $theme === 'light'}
		<span class="icon">🌙</span>
	{:else}
		<span class="icon">☀️</span>
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
