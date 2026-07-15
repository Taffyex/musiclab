<script lang="ts">
	import { userStore, themeStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto } from '$app/navigation';

	async function handleLogout() {
		try {
			await apiClient.auth.logout();
			userStore.logout();
			goto('/login');
		} catch (e) {
			console.error('Failed to logout', e);
		}
	}
</script>

<nav class="navbar flex-between">
	<div class="logo">
		<a href="/" class="text-xl font-bold">MusicLab</a>
	</div>
	
	<div class="nav-links flex-center gap-md">
		<button class="btn btn-ghost" onclick={themeStore.toggle}>
			{$themeStore === 'light' ? '🌙 Dark' : '☀️ Light'}
		</button>
		
		{#if $userStore}
			<a href="/discover" class="btn btn-ghost">Discover</a>
			<a href="/chat" class="btn btn-ghost">Chat</a>
			<div class="user-menu flex-center gap-sm">
				<span class="text-sm">{$userStore.username}</span>
				<button class="btn btn-secondary text-sm" onclick={handleLogout}>Logout</button>
			</div>
		{:else}
			<a href="/login" class="btn btn-primary">Login</a>
		{/if}
	</div>
</nav>

<style>
	.navbar {
		padding: var(--space-md) var(--space-lg);
		background: var(--card-bg);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		z-index: 100;
	}
	.logo a {
		color: var(--text);
	}
	.logo a:hover {
		color: var(--accent);
	}
</style>
