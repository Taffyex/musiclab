<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api';
	import type { QualityProfile, RootFolder } from '$lib/types';
	
	interface Props {
		artistName: string;
		alreadyInLidarr: boolean;
		onAdd: (qualityProfileId?: number, rootFolderPath?: string) => void;
	}
	
	let { artistName, alreadyInLidarr, onAdd }: Props = $props();
	
	let showOptions = $state(false);
	let profiles = $state<QualityProfile[]>([]);
	let rootFolders = $state<RootFolder[]>([]);
	let selectedProfile = $state<number | null>(null);
	let selectedFolder = $state<string | null>(null);
	
	onMount(async () => {
		try {
			profiles = await apiClient.lidarr.getProfiles();
			rootFolders = await apiClient.lidarr.getRootFolders();
			if (profiles.length > 0) selectedProfile = profiles[0].id;
			if (rootFolders.length > 0) selectedFolder = rootFolders[0].path;
		} catch (e) {
			console.error("Failed to load Lidarr metadata", e);
		}
	});
	
	function handleClick(e: MouseEvent) {
		if (alreadyInLidarr) return;
		if (e.shiftKey) {
			showOptions = !showOptions;
		} else {
			onAdd();
		}
	}
	
	function submitAdvanced() {
		if (selectedProfile && selectedFolder) {
			onAdd(selectedProfile, selectedFolder);
			showOptions = false;
		}
	}
</script>

<div class="lidarr-quick-add relative">
	<button 
		class="lidarr-btn" 
		class:in-library={alreadyInLidarr}
		onclick={handleClick}
		disabled={alreadyInLidarr}
		title="Click to quick add, Shift+Click for options"
	>
		{#if alreadyInLidarr}
			✓ In Library
		{:else}
			+ Add to Lidarr
		{/if}
	</button>
	
	{#if showOptions}
		<div class="options-dropdown absolute mt-xs">
			<div class="form-group">
				<label for="profile" class="text-xs">Quality Profile</label>
				<select id="profile" bind:value={selectedProfile} class="select-sm">
					{#each profiles as profile}
						<option value={profile.id}>{profile.name}</option>
					{/each}
				</select>
			</div>
			<div class="form-group mt-xs">
				<label for="folder" class="text-xs">Root Folder</label>
				<select id="folder" bind:value={selectedFolder} class="select-sm">
					{#each rootFolders as folder}
						<option value={folder.path}>{folder.path}</option>
					{/each}
				</select>
			</div>
			<button class="btn-confirm mt-sm w-full text-xs" onclick={submitAdvanced}>Confirm</button>
		</div>
	{/if}
</div>

<style>
	.lidarr-quick-add {
		display: inline-block;
	}
	
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
	
	.relative { position: relative; }
	.absolute { position: absolute; }
	.w-full { width: 100%; }
	
	.options-dropdown {
		top: 100%;
		left: 0;
		background: var(--bg-surface, #1e1e2e);
		border: 1px solid var(--border-color, #444);
		border-radius: var(--radius-sm, 4px);
		padding: 0.75rem;
		z-index: 10;
		min-width: 200px;
		box-shadow: 0 4px 12px rgba(0,0,0,0.5);
	}
	
	.select-sm {
		width: 100%;
		background: var(--bg-input, #2a2a3e);
		color: var(--text-primary, #eee);
		border: 1px solid var(--border-color, #444);
		border-radius: var(--radius-sm, 4px);
		padding: 0.2rem;
		font-size: 0.8rem;
	}
	
	.btn-confirm {
		background: var(--success, #2ecc71);
		color: white;
		border: none;
		padding: 0.3rem;
		border-radius: var(--radius-sm, 4px);
		cursor: pointer;
		font-weight: bold;
	}
	
	.btn-confirm:hover {
		background: #27ae60;
	}
</style>
