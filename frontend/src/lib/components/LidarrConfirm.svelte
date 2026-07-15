<script lang="ts">
	// TODO: Fetch profiles and root folders on mount, wire up confirmation flow
	import type { DiscoveryCard, QualityProfile, RootFolder } from '$lib/types';
	import { addArtist } from '$lib/api/lidarr';

	interface Props {
		card: DiscoveryCard;
		profiles?: QualityProfile[];
		rootFolders?: RootFolder[];
		onClose?: () => void;
		onSuccess?: () => void;
	}

	let { card, profiles = [], rootFolders = [], onClose, onSuccess }: Props = $props();

	let selectedProfileId = $state(profiles[0]?.id ?? 0);
	let selectedRootFolder = $state(rootFolders[0]?.path ?? '');
	let submitting = $state(false);
	let errorMessage = $state('');

	async function handleConfirm() {
		submitting = true;
		errorMessage = '';
		try {
			await addArtist({
				artistName: card.artist_name,
				foreignArtistId: card.id,
				qualityProfileId: selectedProfileId,
				rootFolderPath: selectedRootFolder,
				monitored: true
			});
			onSuccess?.();
		} catch (err) {
			errorMessage = err instanceof Error ? err.message : 'Failed to add artist';
		} finally {
			submitting = false;
		}
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={onClose}>
	<div class="modal card" onclick={(e) => e.stopPropagation()}>
		<div class="modal-header flex-between">
			<h2>Add to Lidarr</h2>
			<button class="btn btn-ghost" onclick={onClose}>✕</button>
		</div>

		<div class="modal-body flex-col gap-md">
			<p>
				Add <strong>{card.artist_name}</strong> to your Lidarr library?
			</p>

			<div class="form-group">
				<label class="label" for="quality-profile">Quality Profile</label>
				<select
					id="quality-profile"
					class="input"
					bind:value={selectedProfileId}
				>
					{#each profiles as profile}
						<option value={profile.id}>{profile.name}</option>
					{/each}
					{#if profiles.length === 0}
						<option value={0}>No profiles available</option>
					{/if}
				</select>
			</div>

			<div class="form-group">
				<label class="label" for="root-folder">Root Folder</label>
				<select
					id="root-folder"
					class="input"
					bind:value={selectedRootFolder}
				>
					{#each rootFolders as folder}
						<option value={folder.path}>{folder.path}</option>
					{/each}
					{#if rootFolders.length === 0}
						<option value="">No folders available</option>
					{/if}
				</select>
			</div>

			{#if errorMessage}
				<p class="error-text">{errorMessage}</p>
			{/if}
		</div>

		<div class="modal-footer flex gap-sm" style="justify-content: flex-end;">
			<button class="btn btn-secondary" onclick={onClose} disabled={submitting}>
				Cancel
			</button>
			<button class="btn btn-primary" onclick={handleConfirm} disabled={submitting}>
				{#if submitting}
					<span class="spinner"></span> Adding…
				{:else}
					Confirm
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 200;
		backdrop-filter: blur(4px);
	}

	.modal {
		width: 100%;
		max-width: 480px;
		max-height: 90vh;
		overflow-y: auto;
	}

	.modal-header {
		margin-bottom: var(--space-md);
	}

	.modal-body {
		margin-bottom: var(--space-lg);
	}

	.modal-footer {
		padding-top: var(--space-md);
		border-top: 1px solid var(--border);
	}

	.error-text {
		color: var(--error);
		font-size: 0.875rem;
	}
</style>
