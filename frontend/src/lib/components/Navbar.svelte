<script lang="ts">
	import { userStore, themeStore } from '$lib/stores';
	import { apiClient } from '$lib/api';
	import { goto, afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import SearchBar from '$lib/components/SearchBar.svelte';

	let mobileSearchOpen = $state(false);

	// Close mobile search on navigation
	afterNavigate(() => {
		mobileSearchOpen = false;
	});

	async function handleLogout() {
		try {
			await apiClient.auth.logout();
			userStore.logout();
			goto('/login');
		} catch (e) {
			console.error('Failed to logout', e);
		}
	}

	function isActive(href: string) {
		return $page.url.pathname.startsWith(href);
	}
</script>

<nav class="navbar">
	<div class="logo">
		<a href="/" class="logo-link">
			<span class="logo-icon">🎵</span>
			<span class="logo-text">MusicLab</span>
		</a>
	</div>
	
	<div class="search-section" class:mobile-open={mobileSearchOpen}>
		{#if $userStore}
			<SearchBar />
		{/if}
	</div>

	<div class="nav-links flex-center gap-md">
		{#if $userStore}
			<!-- Mobile search toggle -->
			<button 
				class="btn btn-ghost mobile-search-btn" 
				onclick={() => mobileSearchOpen = !mobileSearchOpen}
				aria-label="Toggle search"
			>
				⌕
			</button>

			<a href="/explore" class="btn btn-ghost nav-link" class:active={isActive('/explore')}>Explore</a>
			<a href="/favorites" class="btn btn-ghost nav-link" class:active={isActive('/favorites')}>Favorites</a>
			<a href="/discover" class="btn btn-ghost nav-link" class:active={isActive('/discover')}>Discover</a>
			<a href="/chat" class="btn btn-ghost nav-link" class:active={isActive('/chat')}>Chat</a>
			<div class="user-menu flex-center gap-sm">
				<span class="username text-sm">{$userStore.username}</span>
				<button class="btn btn-secondary text-sm" onclick={handleLogout}>Logout</button>
			</div>
		{:else}
			<a href="/login" class="btn btn-primary">Login</a>
		{/if}

		<button class="btn btn-ghost theme-btn" onclick={themeStore.toggle} title="Toggle theme">
			{$themeStore === 'light' ? '🌙' : '☀️'}
		</button>
	</div>
</nav>

<!-- Mobile search overlay -->
{#if mobileSearchOpen && $userStore}
	<div class="mobile-search-bar">
		<SearchBar />
	</div>
{/if}

<style>
	.navbar {
		padding: var(--space-sm) var(--space-lg);
		background: var(--card-bg);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-md);
		backdrop-filter: blur(8px);
	}

	.logo {
		flex-shrink: 0;
	}

	.logo-link {
		display: flex;
		align-items: center;
		gap: var(--space-xs);
		color: var(--text);
		font-weight: 700;
		font-size: 1.1rem;
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.logo-link:hover {
		color: var(--accent);
	}

	.logo-icon {
		font-size: 1.3rem;
	}

	.search-section {
		flex: 1;
		max-width: 440px;
		margin: 0 auto;
		display: flex;
		justify-content: center;
		width: 100%;
	}

	.nav-links {
		flex-shrink: 0;
	}

	.nav-link {
		position: relative;
		transition: color var(--transition-fast);
	}

	.nav-link.active {
		color: var(--accent);
		font-weight: 600;
	}

	.nav-link.active::after {
		content: '';
		position: absolute;
		bottom: -2px;
		left: var(--space-sm);
		right: var(--space-sm);
		height: 2px;
		background: var(--accent);
		border-radius: 2px;
	}

	.username {
		color: var(--text-secondary);
		font-weight: 500;
	}

	.theme-btn {
		font-size: 1rem;
		padding: var(--space-xs) var(--space-sm);
	}

	.mobile-search-btn {
		display: none;
		font-size: 1.2rem;
	}

	.mobile-search-bar {
		display: none;
		padding: var(--space-sm) var(--space-lg);
		background: var(--card-bg);
		border-bottom: 1px solid var(--border);
	}

	@media (max-width: 768px) {
		.search-section {
			display: none;
		}

		.mobile-search-btn {
			display: flex;
		}

		.mobile-search-bar {
			display: block;
		}

		.username {
			display: none;
		}

		.nav-link {
			font-size: 0.85rem;
		}
	}

	@media (max-width: 480px) {
		.nav-links {
			gap: var(--space-xs);
		}
	}
</style>
