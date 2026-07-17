<script lang="ts">
	interface Props {
		artistName: string;
		alreadyInLidarr: boolean;
		onAdd: () => void;
	}
	
	let { artistName, alreadyInLidarr, onAdd }: Props = $props();
	
	function handleClick(e: MouseEvent) {
		if (alreadyInLidarr) return;
		if (e.shiftKey) {
			// Trigger advanced add modal/dropdown (stub for now)
			onAdd();
		} else {
			// Quick add
			onAdd();
		}
	}
</script>

<button 
	class="lidarr-btn" 
	class:in-library={alreadyInLidarr}
	onclick={handleClick}
	disabled={alreadyInLidarr}
>
	{#if alreadyInLidarr}
		✓ In Library
	{:else}
		+ Add to Lidarr
	{/if}
</button>

<style>
	.lidarr-btn {
		background: var(--accent, #6c5ce7);
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: var(--radius-sm, 4px);
		cursor: pointer;
		font-weight: bold;
		transition: background 0.2s;
	}
	
	.lidarr-btn:hover:not(:disabled) {
		background: var(--accent-hover, #5a4bcf);
	}
	
	.lidarr-btn.in-library {
		background: var(--success, #2ecc71);
		cursor: default;
	}
</style>
