<script lang="ts">
	import { userStore } from '$lib/stores';
	import { onMount } from 'svelte';
	import { requireAuth } from '$lib/utils/auth-guard';
	import { apiClient } from '$lib/api';

	let settings = $state({
		lastfm_username: '',
		lastfm_api_key: '',
		lidarr_url: '',
		lidarr_api_key: '',
		llm_provider: 'anthropic',
		anthropic_api_key: '',
		openai_api_key: '',
		deepseek_api_key: ''
	});
	
	let loading = $state(true);
	let saving = $state(false);
	let message = $state('');
	let error = $state('');

	onMount(async () => {
		await requireAuth();
		try {
			const data = await apiClient.settings.get();
			settings = { ...settings, ...data };
		} catch (e) {
			console.error("Failed to load settings", e);
		} finally {
			loading = false;
		}
	});

	async function saveSettings() {
		saving = true;
		message = '';
		error = '';
		try {
			await apiClient.settings.save(settings);
			message = 'Settings saved successfully!';
			
			if ($userStore) {
				$userStore.lastfm_username = settings.lastfm_username;
				$userStore.llm_provider = settings.llm_provider;
			}
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : 'Failed to save';
		} finally {
			saving = false;
		}
	}
</script>

<div class="settings-page max-w">
	<h1 class="text-2xl font-bold mb-md">Settings</h1>
	
	{#if loading}
		<div class="flex-center py-xl">
			<div class="spinner"></div>
		</div>
	{:else}
		<div class="card flex-col gap-md">
			{#if message}
				<div class="success-msg text-green-500 mb-sm" style="color: #10B981">{message}</div>
			{/if}
			{#if error}
				<div class="error-msg text-red-500 mb-sm" style="color: #EF4444">{error}</div>
			{/if}

			<div>
				<h3 class="text-lg font-medium mb-sm">Account Information</h3>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="username">Username</label>
					<input class="input w-full" id="username" type="text" value={$userStore?.username || ''} disabled />
				</div>
			</div>
			
			<hr class="divider" />
			
			<div>
				<h3 class="text-lg font-medium mb-sm">Last.fm Configuration</h3>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="lastfm_username">Last.fm Username</label>
					<input class="input w-full" id="lastfm_username" type="text" bind:value={settings.lastfm_username} />
				</div>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="lastfm_api_key">Last.fm API Key</label>
					<input class="input w-full" id="lastfm_api_key" type="password" bind:value={settings.lastfm_api_key} />
				</div>
			</div>
			
			<hr class="divider" />

			<div>
				<h3 class="text-lg font-medium mb-sm">Lidarr Configuration (Optional)</h3>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="lidarr_url">Lidarr URL</label>
					<input class="input w-full" id="lidarr_url" type="text" bind:value={settings.lidarr_url} placeholder="http://localhost:8686" />
				</div>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="lidarr_api_key">Lidarr API Key</label>
					<input class="input w-full" id="lidarr_api_key" type="password" bind:value={settings.lidarr_api_key} />
				</div>
			</div>

			<hr class="divider" />

			<div>
				<h3 class="text-lg font-medium mb-sm">LLM Configuration</h3>
				<div class="form-group mb-sm">
					<label class="text-secondary" for="llm_provider">Provider</label>
					<select class="input w-full" id="llm_provider" bind:value={settings.llm_provider}>
						<option value="openai">OpenAI (ChatGPT)</option>
						<option value="deepseek">DeepSeek</option>
					</select>
				</div>
				{#if settings.llm_provider === 'openai'}
					<div class="form-group mb-sm">
						<label class="text-secondary" for="openai_api_key">OpenAI API Key</label>
						<input class="input w-full" id="openai_api_key" type="password" bind:value={settings.openai_api_key} />
					</div>
				{/if}
				{#if settings.llm_provider === 'deepseek'}
					<div class="form-group mb-sm">
						<label class="text-secondary" for="deepseek_api_key">DeepSeek API Key</label>
						<input class="input w-full" id="deepseek_api_key" type="password" bind:value={settings.deepseek_api_key} />
					</div>
				{/if}
			</div>
			
			<div class="mt-md flex" style="justify-content: flex-end;">
				<button class="btn btn-primary" onclick={saveSettings} disabled={saving}>
					{#if saving}<span class="spinner" style="border-width:2px;width:1rem;height:1rem;"></span>{:else}Save Settings{/if}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.max-w {
		max-width: 600px;
		margin: 0 auto;
	}
	
	.divider {
		border: none;
		border-top: 1px solid var(--border);
		margin: var(--space-md) 0;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}
</style>
