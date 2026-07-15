<script lang="ts">
	import { userStore } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { apiClient } from '$lib/api';
	import { requireAuth } from '$lib/utils/auth-guard';

	onMount(async () => {
		await requireAuth();
	});
</script>

<div class="settings-page max-w">
	<h1 class="text-2xl font-bold mb-md">Settings</h1>
	
	<div class="card flex-col gap-md">
		<div>
			<h3 class="text-lg font-medium">Account Information</h3>
			<p class="text-secondary mt-sm">
				<strong>Username:</strong> {$userStore?.username || 'Loading...'}
			</p>
			<p class="text-secondary mt-sm">
				<strong>Last.fm Username:</strong> {$userStore?.lastfm_username || 'Not configured'}
			</p>
		</div>
		
		<hr class="divider" />
		
		<div>
			<h3 class="text-lg font-medium mb-sm">Preferences</h3>
			<p class="text-secondary">
				You can toggle the application theme from the navigation bar.
			</p>
		</div>
	</div>
</div>

<style>
	.max-w {
		max-width: 600px;
		margin: 0 auto;
	}
	
	.mb-md { margin-bottom: var(--space-md); }
	.mb-sm { margin-bottom: var(--space-sm); }
	.mt-sm { margin-top: var(--space-sm); }
	
	.divider {
		border: none;
		border-top: 1px solid var(--border);
		margin: var(--space-md) 0;
	}
</style>
