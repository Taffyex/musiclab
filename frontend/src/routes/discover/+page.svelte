<script lang="ts">
	import { onMount } from 'svelte';
	import { userStore, profileStore, discoveryStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';
	import TasteProfile from '$lib/components/TasteProfile.svelte';
	import DiscoveryCard from '$lib/components/DiscoveryCard.svelte';
	import { requireAuth } from '$lib/utils/auth-guard';

	let profileLoading = $state(false);
	let profileError = $state('');
	
	let discoveryLoading = $state(false);
	let discoveryError = $state('');
	
	let historyLoading = $state(false);
	let historyData = $state<any[]>([]);

	onMount(async () => {
		const isAuthed = await requireAuth();
		if (!isAuthed) return;

		loadProfile();
		loadHistory();
		
		if (!$discoveryStore) {
			generateRecommendations();
		}
	});

	async function loadHistory() {
		historyLoading = true;
		try {
			historyData = await apiClient.discovery.history();
		} catch (err: unknown) {
			console.error('Failed to load history:', err);
		} finally {
			historyLoading = false;
		}
	}

	function loadBatch(batch: any) {
		discoveryStore.set(batch);
		if (typeof window !== 'undefined') {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	async function loadProfile() {
		profileLoading = true;
		profileError = '';
		try {
			const res = await apiClient.lastfm.getProfile();
			profileStore.set(res);
		} catch (err: unknown) {
			profileError = err instanceof Error ? err.message : 'Failed to load Last.fm profile.';
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
		} catch (err: unknown) {
			profileError = err instanceof Error ? err.message : 'Failed to refresh profile.';
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
			loadHistory();
		} catch (err: unknown) {
			discoveryError = err instanceof Error ? err.message : 'Failed to generate recommendations.';
		} finally {
			discoveryLoading = false;
		}
	}

	/** Group history batches by date label (Today / Yesterday / <date>) */
	function groupHistoryByDate(batches: any[]): { label: string; items: any[] }[] {
		const groups: Record<string, any[]> = {};
		const now = new Date();
		const todayStr = now.toDateString();
		const yesterdayStr = new Date(now.getTime() - 86400000).toDateString();

		for (const batch of batches) {
			const d = new Date(batch.created_at);
			const ds = d.toDateString();
			let label: string;
			if (ds === todayStr) label = 'Today';
			else if (ds === yesterdayStr) label = 'Yesterday';
			else label = d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
			(groups[label] ??= []).push(batch);
		}

		return Object.entries(groups).map(([label, items]) => ({ label, items }));
	}

	let historyGroups = $derived(groupHistoryByDate(historyData));
</script>

<div class="discover-page flex-col gap-2xl">
	<section class="profile-section">
		<div class="flex-between mb-md">
			<h1 class="text-2xl font-bold">Discovery Dashboard</h1>
			<button class="btn btn-secondary text-sm" onclick={refreshProfile} disabled={profileLoading}>
				{#if profileLoading}<span class="spinner"></span>{/if}
				Refresh Profile
			</button>
		</div>
		<TasteProfile profile={$profileStore} loading={profileLoading} error={profileError} />
	</section>

	<section class="recommendations-section">
		<div class="flex-between mb-md">
			<div>
				<h2 class="text-xl font-bold">AI Recommendations</h2>
				{#if $discoveryStore}
					<p class="text-sm text-secondary mt-xs">
						{$discoveryStore.cards.length} artists • Generated {new Date($discoveryStore.created_at).toLocaleDateString()}
					</p>
				{/if}
			</div>
		</div>

		{#if discoveryError}
			<div class="error-msg mb-md">{discoveryError}</div>
		{/if}

		{#if discoveryLoading && !$discoveryStore}
			<div class="grid grid-cols-4 recommendations-grid">
				{#each Array(8) as _, i (i)}
					<div class="skeleton-card card">
						<div class="skeleton skeleton-title"></div>
						<div class="skeleton skeleton-text"></div>
						<div class="skeleton skeleton-text short"></div>
						<div class="skeleton skeleton-tags"></div>
					</div>
				{/each}
			</div>
		{:else if $discoveryStore}
			<div class="grid grid-cols-4 recommendations-grid">
				{#each $discoveryStore.cards as item, i (item.id)}
					<DiscoveryCard {item} index={i} />
				{/each}
			</div>
		{:else}
			<div class="empty-state card">
				<div class="empty-icon">🎧</div>
				<h3>No recommendations yet</h3>
				<p class="text-secondary">Click the button to generate your personalized AI recommendations.</p>
			</div>
		{/if}
	</section>

	<section class="history-section">
		<h2 class="text-xl font-bold mb-md">Discovery History</h2>
		{#if historyLoading && historyData.length === 0}
			<div class="flex-center py-xl"><span class="spinner"></span></div>
		{:else if historyGroups.length > 0}
			<div class="timeline">
				{#each historyGroups as group (group.label)}
					<div class="timeline-group">
						<div class="timeline-date-header">
							<div class="timeline-line"></div>
							<span class="timeline-date-label">{group.label}</span>
							<div class="timeline-line"></div>
						</div>
						<div class="timeline-items">
							{#each group.items as batch (batch.id || batch.created_at)}
								<button class="timeline-batch card" onclick={() => loadBatch(batch)}>
									<div class="batch-dot"></div>
									<div class="batch-info">
										<div class="font-bold">
											{new Date(batch.created_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
										</div>
										<div class="text-sm text-secondary">
											{batch.cards?.length || 0} recommendations
										</div>
									</div>
									<span class="batch-load-btn">Load →</span>
								</button>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="text-secondary text-sm card py-xl text-center">
				No history available yet. Generate your first batch!
			</div>
		{/if}
	</section>
</div>

<!-- Floating Action Button -->
<button 
	class="fab" 
	onclick={generateRecommendations} 
	disabled={discoveryLoading}
	title="Generate New Batch"
>
	{#if discoveryLoading}
		<span class="fab-spinner"></span>
	{:else}
		<span class="fab-icon">✨</span>
	{/if}
	<span class="fab-label">{discoveryLoading ? 'Generating...' : 'New Batch'}</span>
</button>

<style>
	.discover-page {
		padding-bottom: 100px; /* Space for FAB */
	}

	/* Skeleton loaders */
	.skeleton-card {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.skeleton {
		background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border) 50%, var(--bg-secondary) 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: var(--radius-sm);
	}
	.skeleton-title { height: 1.5rem; width: 70%; }
	.skeleton-text { height: 1rem; width: 100%; }
	.skeleton-text.short { width: 50%; }
	.skeleton-tags { height: 1.5rem; width: 60%; }
	@keyframes shimmer {
		0% { background-position: 200% 0; }
		100% { background-position: -200% 0; }
	}

	/* Empty state */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-md);
		padding: var(--space-2xl);
		text-align: center;
	}
	.empty-icon {
		font-size: 3rem;
	}
	.empty-state h3 {
		margin: 0;
		font-size: 1.25rem;
	}
	.empty-state p {
		margin: 0;
		max-width: 400px;
	}

	/* Batch metadata */
	.recommendations-section .mt-xs {
		margin-top: var(--space-xs);
	}

	/* Timeline history */
	.timeline {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.timeline-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.timeline-date-header {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
	}

	.timeline-line {
		flex: 1;
		height: 1px;
		background: var(--border);
	}

	.timeline-date-label {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		white-space: nowrap;
		padding: 0 var(--space-xs);
	}

	.timeline-items {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
		padding-left: var(--space-md);
		border-left: 2px solid var(--border);
	}

	.timeline-batch {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		text-align: left;
		cursor: pointer;
		width: 100%;
		position: relative;
		transition: background-color var(--transition-fast), border-color var(--transition-fast);
		background: var(--card-bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-sm) var(--space-md);
	}

	.timeline-batch:hover {
		background: var(--bg);
		border-color: var(--accent);
	}

	.batch-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--accent);
		flex-shrink: 0;
		opacity: 0.6;
	}

	.batch-info {
		flex: 1;
	}

	.batch-load-btn {
		color: var(--accent);
		font-size: 0.9rem;
		font-weight: 600;
		opacity: 0;
		transition: opacity var(--transition-fast);
	}

	.timeline-batch:hover .batch-load-btn {
		opacity: 1;
	}

	/* Floating Action Button */
	.fab {
		position: fixed;
		bottom: var(--space-xl);
		right: var(--space-xl);
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		background: var(--accent);
		color: #ffffff;
		border: none;
		border-radius: var(--radius-full);
		padding: var(--space-md) var(--space-lg);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 20px rgba(108, 92, 231, 0.4), var(--shadow-lg);
		transition: transform var(--transition-fast), box-shadow var(--transition-fast);
		z-index: 50;
	}

	.fab:hover:not(:disabled) {
		transform: translateY(-2px) scale(1.02);
		box-shadow: 0 8px 30px rgba(108, 92, 231, 0.5), var(--shadow-lg);
	}

	.fab:active:not(:disabled) {
		transform: scale(0.98);
	}

	.fab:disabled {
		opacity: 0.8;
		cursor: not-allowed;
	}

	.fab-icon {
		font-size: 1.1rem;
	}

	.fab-label {
		white-space: nowrap;
	}

	.fab-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255,255,255,0.4);
		border-top-color: #ffffff;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.text-center { text-align: center; }
</style>
