<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { requireAuth } from '$lib/utils/auth-guard';
	import { apiClient } from '$lib/api';
	import type { CreditEntity } from '$lib/types';
	
	import CreditHeader from '$lib/components/CreditHeader.svelte';
	import CreditReleaseGrid from '$lib/components/CreditReleaseGrid.svelte';
	
	let slug = $derived($page.params.slug);
	
	let loading = $state(true);
	let error = $state<string | null>(null);
	let entity = $state<CreditEntity | null>(null);
	
	$effect(() => {
		if (slug) {
			loadCredit(slug);
		}
	});
	
	async function loadCredit(creditSlug: string) {
		loading = true;
		error = null;
		try {
			await requireAuth();
			entity = await apiClient.explore.getCreditEntity(creditSlug);
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'An unexpected error occurred';
			error = message;
		} finally {
			loading = false;
		}
	}
</script>

<div class="credit-page">
	{#if loading && !entity}
		<div class="flex-center py-xl">
			<p>Loading credit details...</p>
		</div>
	{:else if error}
		<div class="error-msg">{error}</div>
	{:else if entity}
		<CreditHeader {entity} />
		<CreditReleaseGrid releases={entity.releases} />
	{/if}
</div>

<style>
	.credit-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		display: flex;
		flex-direction: column;
	}
</style>
