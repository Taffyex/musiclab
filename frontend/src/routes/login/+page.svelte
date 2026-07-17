<script lang="ts">
	import { userStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit() {
		error = '';
		loading = true;
		try {
			await apiClient.auth.login(username, password);
			const res = await apiClient.auth.me();
			userStore.login(res.user);
			goto('/discover');
		} catch (err: unknown) {
			error = err instanceof Error ? err.message : 'Login failed. Please check your credentials.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="login-container flex-center">
	<div class="card login-card">
		<h2 class="text-2xl font-bold mb-md text-center">Welcome Back</h2>
		
		{#if error}
			<div class="error-msg mb-md">{error}</div>
		{/if}

		<form onsubmit={handleSubmit} class="flex-col gap-md">
			<div>
				<label class="label" for="username">Username</label>
				<input 
					type="text" 
					id="username" 
					class="input" 
					bind:value={username} 
					required 
					disabled={loading}
				/>
			</div>
			
			<div>
				<label class="label" for="password">Password</label>
				<input 
					type="password" 
					id="password" 
					class="input" 
					bind:value={password} 
					required 
					disabled={loading}
				/>
			</div>
			
			<button type="submit" class="btn btn-primary w-full mt-sm" disabled={loading}>
				{#if loading}
					<span class="spinner"></span>
				{:else}
					Login
				{/if}
			</button>
		</form>
	</div>
</div>

<style>
	.login-container {
		min-height: calc(100vh - 200px);
	}
	
	.login-card {
		width: 100%;
		max-width: 400px;
		padding: var(--space-xl);
	}
</style>
