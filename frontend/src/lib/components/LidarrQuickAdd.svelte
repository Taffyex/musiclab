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
					{#each profiles as profile (profile.id)}
						<option value={profile.id}>{profile.name}</option>
					{/each}
				</select>
			</div>
			<div class="form-group mt-xs">
				<label for="folder" class="text-xs">Root Folder</label>
				<select id="folder" bind:value={selectedFolder} class="select-sm">
					{#each rootFolders as folder (folder.path)}
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
		background: var(--accent);
		color: #ffffff;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-weight: bold;
		transition: background var(--transition-fast);
	}
	
	.lidarr-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}
	
	.lidarr-btn.in-library {
		background: var(--success);
		cursor: default;
	}
	
	.options-dropdown {
		top: 100%;
		left: 0;
		background: var(--card-bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.75rem;
		z-index: 10;
		min-width: 200px;
		box-shadow: var(--shadow-lg);
	}
	
	.select-sm {
		width: 100%;
		background: var(--bg-secondary);
		color: var(--text);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.2rem;
		font-size: 0.8rem;
	}
	
	.btn-confirm {
		background: var(--success);
		color: #ffffff;
		border: none;
		padding: 0.3rem;
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-weight: bold;
	}
	
	.btn-confirm:hover {
		opacity: 0.9;
	}
</style>
