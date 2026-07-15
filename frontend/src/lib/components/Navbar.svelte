<script lang="ts">
	// TODO: Wire up active route highlighting
	import { isAuthenticated, logout } from '$lib/stores/auth';
	import ThemeToggle from './ThemeToggle.svelte';

	async function handleLogout() {
		await logout();
		window.location.href = '/login';
	}
</script>

<nav class="navbar">
	<div class="navbar-inner container flex-between">
		<a href="/" class="logo">
			<span class="logo-icon">🎵</span>
			<span class="logo-text">MusicLab</span>
		</a>

		<div class="nav-links flex gap-md">
			<a href="/" class="nav-link">Dashboard</a>
			<a href="/discover" class="nav-link">Discover</a>
			<a href="/chat" class="nav-link">Chat</a>
			<a href="/settings" class="nav-link">Settings</a>
		</div>

		<div class="nav-actions flex gap-sm">
			<ThemeToggle />
			<button class="btn btn-ghost" onclick={handleLogout}>Logout</button>
		</div>
	</div>
</nav>

<style>
	.navbar {
		position: sticky;
		top: 0;
		z-index: 100;
		background: var(--card-bg);
		border-bottom: 1px solid var(--border);
		backdrop-filter: blur(8px);
	}

	.navbar-inner {
		height: 60px;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--text);
	}

	.logo:hover {
		color: var(--accent);
	}

	.logo-icon {
		font-size: 1.5rem;
	}

	.nav-link {
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius-md);
		color: var(--text-secondary);
		font-weight: 500;
		transition:
			color var(--transition-fast),
			background var(--transition-fast);
	}

	.nav-link:hover {
		color: var(--text);
		background: var(--bg);
	}
</style>
