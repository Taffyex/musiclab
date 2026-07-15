<script lang="ts">
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api';
	import type { QualityProfile, RootFolder } from '$lib/types';
	interface Props {
		artistName: string;
		foreignArtistId: string;
		onCancel: () => void;
		onSuccess: () => void;
	}
	let { artistName, foreignArtistId, onCancel, onSuccess }: Props = $props();

	let profiles = $state<QualityProfile[]>([]);
	let rootFolders = $state<RootFolder[]>([]);
	
	let selectedProfileId = $state<number | null>(null);
	let selectedRootFolderPath = $state<string | null>(null);
	let isMonitored = $state<boolean>(true);

	let loading = $state(false);
	let error = $state('');

	onMount(async () => {
		try {
			const [profilesData, foldersData] = await Promise.all([
				apiClient.lidarr.getProfiles(),
				apiClient.lidarr.getRootFolders()
			]);
			profiles = profilesData;
			rootFolders = foldersData;
			
			if (profiles.length > 0) selectedProfileId = profiles[0].id;
			if (rootFolders.length > 0) selectedRootFolderPath = rootFolders[0].path;
		} catch (err: any) {
			error = 'Failed to load Lidarr configurations. Check your connection or settings.';
			console.error(err);
		}
	});

	async function handleSubmit() {
		if (selectedProfileId === null || selectedRootFolderPath === null) {
			error = 'Please select a quality profile and a root folder.';
			return;
		}

		loading = true;
		error = '';

		try {
			await apiClient.lidarr.addArtist({
				artistName,
				foreignArtistId,
				qualityProfileId: selectedProfileId,
				rootFolderPath: selectedRootFolderPath,
				monitored: isMonitored
			});
			onSuccess();
		} catch (err: any) {
			error = err.message || 'Failed to add artist to Lidarr.';
			loading = false;
		}
	}
</script>

<div class="lidarr-confirm card p-lg">
	<h3 class="text-xl font-bold mb-md">Add {artistName} to Lidarr</h3>
	
	{#if error}
		<div class="error-msg mb-md">{error}</div>
	{/if}

	<div class="form-group mb-sm">
		<label for="profile" class="text-sm font-bold block mb-xs">Quality Profile</label>
		<select id="profile" bind:value={selectedProfileId} class="w-full p-sm input-field">
			{#each profiles as profile}
				<option value={profile.id}>{profile.name}</option>
			{/each}
		</select>
	</div>

	<div class="form-group mb-sm">
		<label for="rootFolder" class="text-sm font-bold block mb-xs">Root Folder</label>
		<select id="rootFolder" bind:value={selectedRootFolderPath} class="w-full p-sm input-field">
			{#each rootFolders as folder}
				<option value={folder.path}>{folder.path}</option>
			{/each}
		</select>
	</div>

	<div class="form-group mb-md flex items-center gap-sm">
		<input type="checkbox" id="monitored" bind:checked={isMonitored} class="checkbox" />
		<label for="monitored" class="text-sm">Monitor missing albums</label>
	</div>

	<div class="flex gap-sm justify-end">
		<button class="btn btn-secondary text-sm" onclick={onCancel} disabled={loading}>
			Cancel
		</button>
		<button class="btn btn-primary text-sm" onclick={handleSubmit} disabled={loading}>
			{#if loading}
				<span class="spinner inline-block mr-xs"></span> Adding...
			{:else}
				Confirm
			{/if}
		</button>
	</div>
</div>

<style>
	.lidarr-confirm {
		background: var(--card-bg);
		border: 1px solid var(--border);
	}
	
	.input-field {
		background: var(--bg);
		border: 1px solid var(--border);
		color: var(--text);
		border-radius: var(--radius-sm);
	}

	.checkbox {
		width: 1rem;
		height: 1rem;
	}
	
	.inline-block { display: inline-block; }
	.mr-xs { margin-right: var(--space-xs); }
	.block { display: block; }
	.w-full { width: 100%; }
	.justify-end { justify-content: flex-end; }
	.items-center { align-items: center; }
</style>
