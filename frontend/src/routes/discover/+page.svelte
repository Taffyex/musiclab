<script lang="ts">
	import { onMount } from 'svelte';
	import { userStore, profileStore, discoveryStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';
	import TasteProfile from '$lib/components/TasteProfile.svelte';
	import DiscoveryCard from '$lib/components/DiscoveryCard.svelte';

	let profileLoading = $state(false);
	let profileError = $state('');
	
	let discoveryLoading = $state(false);
	let discoveryError = $state('');

	onMount(async () => {
		if (!$userStore) {
			// Try to restore session
			try {
				const res = await apiClient.auth.me();
				userStore.login(res.user);
			} catch (e) {
				goto('/login');
				return;
			}
		}

		loadProfile();
		
		if (!$discoveryStore) {
			generateRecommendations();
		}
	});

	async function loadProfile() {
		profileLoading = true;
		profileError = '';
		try {
			const res = await apiClient.lastfm.getProfile();
			profileStore.set(res);
		} catch (err: any) {
			profileError = err.message || 'Failed to load Last.fm profile.';
		} finally {
			profileLoading = false;
		}
	}

	async function refreshProfile() {
		profileLoading = true;
		profileError = '';
		try {
			const res = await apiClient.lastfm.refresh();
			profileStore.set(res);
		} catch (err: any) {
			profileError = err.message || 'Failed to refresh profile.';
		} finally {
			profileLoading = false;
		}
	}

	async function generateRecommendations() {
		discoveryLoading = true;
		discoveryError = '';
		try {
			const res = await apiClient.discovery.generate(8);
			discoveryStore.set(res);
		} catch (err: any) {
			discoveryError = err.message || 'Failed to generate recommendations.';
		} finally {
			discoveryLoading = false;
		}
	}
</script>

<div class="discover-page flex-col gap-2xl">
	<section class="profile-section">
		<div class="flex-between mb-md">
			<h1 class="text-2xl font-bold">Discovery Dashboard</h1>
			<button class="btn btn-secondary text-sm" onclick={refreshProfile} disabled={profileLoading}>
				Refresh Profile
			</button>
		</div>
		<TasteProfile profile={$profileStore} loading={profileLoading} error={profileError} />
	</section>

	<section class="recommendations-section">
		<div class="flex-between mb-md">
			<h2 class="text-xl font-bold">AI Recommendations</h2>
			<button class="btn btn-primary text-sm" onclick={generateRecommendations} disabled={discoveryLoading}>
				{#if discoveryLoading}
					<span class="spinner"></span> Generating...
				{:else}
					Generate New Batch
				{/if}
			</button>
		</div>

		{#if discoveryError}
			<div class="error-msg mb-md">{discoveryError}</div>
		{/if}

		{#if discoveryLoading && !$discoveryStore}
			<div class="flex-center py-2xl">
				<div class="spinner"></div>
			</div>
		{:else if $discoveryStore}
			<div class="grid grid-cols-4 recommendations-grid">
				{#each $discoveryStore.recommendations as item}
					<DiscoveryCard {item} />
				{/each}
			</div>
		{:else}
			<div class="text-secondary text-center py-xl card">
				Click "Generate New Batch" to get your personalized recommendations.
			</div>
		{/if}
	</section>
</div>

<style>
	.gap-2xl { gap: var(--space-2xl); }
	.mb-md { margin-bottom: var(--space-md); }
	.py-xl { padding: var(--space-xl) 0; }
	.py-2xl { padding: var(--space-2xl) 0; }
	
	.error-msg {
		color: var(--error);
		background: rgba(225, 112, 85, 0.1);
		padding: var(--space-md);
		border-radius: var(--radius-md);
	}
	
	/* Responsiveness is handled by global .grid-cols-4 */
</style>
