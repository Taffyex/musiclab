<script lang="ts">
	import { onMount } from 'svelte';
	import { userStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';
	import ChatPanel from '$lib/components/ChatPanel.svelte';

	let loading = $state(true);
	let error = $state('');
	let initialMessages: any[] = $state([]);

	onMount(async () => {
		if (!$userStore) {
			try {
				const res = await apiClient.auth.me();
				userStore.login(res.user);
			} catch (e) {
				goto('/login');
				return;
			}
		}

		try {
			const memory = await apiClient.llm.getMemory();
			initialMessages = [];
		} catch (err: any) {
			console.error('Failed to load memory', err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="chat-page h-full">
	<h1 class="text-2xl font-bold mb-md">AI Music Assistant</h1>
	<p class="text-secondary mb-lg">Chat with the AI to refine your taste profile or ask for specific recommendations.</p>

	{#if loading}
		<div class="flex-center py-xl">
			<div class="spinner"></div>
		</div>
	{:else}
		<div class="chat-container">
			<ChatPanel {initialMessages} />
		</div>
	{/if}
</div>

<style>
	.chat-page {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 150px);
	}
	
	.chat-container {
		flex: 1;
		min-height: 0; /* Important for flex child scrolling */
		border-radius: var(--radius-lg);
		overflow: hidden;
		box-shadow: var(--shadow);
		border: 1px solid var(--border);
	}

	.mb-md { margin-bottom: var(--space-md); }
	.mb-lg { margin-bottom: var(--space-lg); }
	.py-xl { padding: var(--space-xl) 0; }
</style>
