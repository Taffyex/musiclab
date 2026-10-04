<script lang="ts">
    import { onMount } from 'svelte';
    import { userStore, favoritesStore } from '$lib/stores';
    import { apiClient } from '$lib/api';
    import type { ArtistSummary, RecentArtist } from '$lib/types';
    import ArtistCard from '$lib/components/ArtistCard.svelte';
    import HorizontalCarousel from '$lib/components/HorizontalCarousel.svelte';
    import HomeSection from '$lib/components/HomeSection.svelte';
    
    let recentArtists: RecentArtist[] = $state([]);
    let genreCarousels: { genreName: string; genreSlug: string; artists: ArtistSummary[] }[] = $state([]);
    let genreLoading = $state(false);
    let loading = $state(true);

    // Greeting based on time of day
    let greeting = $derived(() => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good morning';
        if (hour < 18) return 'Good afternoon';
        return 'Good evening';
    });
    
    onMount(async () => {
        loadRecentArtists();
        
        if ($userStore) {
            genreLoading = true;
            await loadGenreCarousels();
            genreLoading = false;
        }
        loading = false;
    });
    
    function loadRecentArtists() {
        if (typeof window === 'undefined') return;
        try {
            const data = JSON.parse(localStorage.getItem('musiclab_recent') || '[]');
            recentArtists = data.slice(0, 10);
        } catch (err: unknown) { /* ignore parse errors */ }
    }
    
    async function loadGenreCarousels() {
        const favGenres = $favoritesStore.genres.slice(0, 3);
        const carousels = [];
        
        for (const genre of favGenres) {
            try {
                const res = await apiClient.explore.getGenreArtists(genre.slug, {
                    sort_by: 'listeners', sort_order: 'desc', page: 1, per_page: 15
                });
                if (res.artists.length > 0) {
                    carousels.push({
                        genreName: genre.name,
                        genreSlug: genre.slug,
                        artists: res.artists
                    });
                }
            } catch (err: unknown) { /* skip genre if API fails */ }
        }
        
        genreCarousels = carousels;
    }

    // Quick action definitions — easy to extend for future features
    const quickActions = [
        { href: '/discover', icon: '🎯', label: 'Discover', description: 'AI recommendations' },
        { href: '/explore', icon: '🌍', label: 'Explore', description: 'Browse by genre' },
        { href: '/favorites', icon: '❤️', label: 'Favorites', description: 'Your collection' },
        { href: '/chat', icon: '💬', label: 'Chat', description: 'Ask AI about music' },
    ];
</script>

<div class="homepage">
    <section class="hero">
        <div class="hero-bg-gradient"></div>
        <div class="hero-content">
            <div class="hero-badge">
                <span class="badge-dot"></span>
                Your Music Universe
            </div>
            <h1 class="hero-title">
                {#if $userStore}
                    {greeting()}, <span class="hero-username">{$userStore.username}</span>
                {:else}
                    Discover your next<br/><span class="hero-accent">favorite artist</span>
                {/if}
            </h1>
            <p class="hero-subtitle">
                {#if $userStore}
                    Explore artists, discover new music, and build your collection.
                {:else}
                    MusicLab is a premium music exploration tool powered by Last.fm, Discogs, and AI.
                {/if}
            </p>
            <div class="hero-actions">
                {#if $userStore}
                    <a href="/discover" class="btn btn-primary hero-btn">
                        <span>✨ Discover</span>
                    </a>
                    <a href="/explore" class="btn btn-secondary hero-btn">Explore →</a>
                {:else}
                    <a href="/login" class="btn btn-primary hero-btn">Get Started →</a>
                {/if}
            </div>
        </div>
        <div class="hero-visual">
            <div class="vinyl-record">
                <div class="vinyl-inner"></div>
                <div class="vinyl-label">🎵</div>
            </div>
        </div>
    </section>

    {#if $userStore}
        {#if recentArtists.length > 0}
            <HomeSection title="Recently Explored" subtitle="Your recent artist visits">
                <HorizontalCarousel>
                    {#each recentArtists as artist (artist.slug)}
                        <a href="/artist/{artist.slug}" class="recent-artist-card">
                            <div class="recent-image">
                                {#if artist.image_url}
                                    <img src={artist.image_url} alt={artist.name} loading="lazy" />
                                {:else}
                                    <div class="recent-placeholder">
                                        {artist.name.charAt(0).toUpperCase()}
                                    </div>
                                {/if}
                                <div class="recent-overlay"></div>
                            </div>
                            <span class="recent-name">{artist.name}</span>
                        </a>
                    {/each}
                </HorizontalCarousel>
            </HomeSection>
        {/if}

        {#if genreLoading}
            <HomeSection title="Because You Love..." loading={true}>
                {#snippet children()}{/snippet}
            </HomeSection>
        {:else if genreCarousels.length > 0}
            {#each genreCarousels as carousel (carousel.genreSlug)}
                <HomeSection 
                    title={`Because you love ${carousel.genreName}`} 
                    href={`/explore?genre=${carousel.genreSlug}`}
                >
                    <HorizontalCarousel>
                        {#each carousel.artists as artist (artist.slug)}
                            <div class="artist-card-wrapper">
                                <ArtistCard {artist} />
                            </div>
                        {/each}
                    </HorizontalCarousel>
                </HomeSection>
            {/each}
        {:else if $favoritesStore.genres.length === 0}
            <HomeSection title="Personalized Recommendations">
                <div class="empty-genres card">
                    <span class="empty-icon">🎸</span>
                    <p>Favorite some genres in <a href="/explore">Explore</a> to get personalized recommendations here.</p>
                </div>
            </HomeSection>
        {/if}

        <HomeSection title="Quick Actions">
            <div class="quick-actions-grid">
                {#each quickActions as action (action.href)}
                    <a href={action.href} class="quick-action-card">
                        <div class="action-icon">{action.icon}</div>
                        <div class="action-text">
                            <span class="action-label">{action.label}</span>
                            <span class="action-desc">{action.description}</span>
                        </div>
                    </a>
                {/each}
            </div>
        </HomeSection>
    {/if}
</div>

<style>
    .homepage {
        display: flex;
        flex-direction: column;
        gap: var(--space-2xl, 3rem);
    }

    /* ---- Hero ---- */
    .hero {
        position: relative;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius-xl);
        padding: var(--space-2xl) var(--space-xl);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-xl);
        min-height: 240px;
    }

    .hero-bg-gradient {
        position: absolute;
        inset: 0;
        background: 
            radial-gradient(ellipse at 80% 50%, rgba(108, 92, 231, 0.12) 0%, transparent 60%),
            radial-gradient(ellipse at 20% 80%, rgba(116, 185, 255, 0.08) 0%, transparent 50%);
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        gap: var(--space-md);
        max-width: 560px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: var(--space-xs);
        background: rgba(108, 92, 231, 0.12);
        color: var(--accent);
        border: 1px solid rgba(108, 92, 231, 0.25);
        padding: 4px 12px;
        border-radius: var(--radius-full);
        font-size: 0.8rem;
        font-weight: 600;
        width: fit-content;
    }

    .badge-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--accent);
        animation: pulse-dot 2s infinite;
    }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    .hero-title {
        font-size: clamp(1.8rem, 4vw, 2.8rem);
        font-weight: 800;
        line-height: 1.15;
        color: var(--text);
        margin: 0;
    }

    .hero-username {
        color: var(--accent);
    }

    .hero-accent {
        background: linear-gradient(135deg, var(--accent), var(--info));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1.05rem;
        line-height: 1.6;
        margin: 0;
    }

    .hero-actions {
        display: flex;
        gap: var(--space-sm);
        flex-wrap: wrap;
    }

    .hero-btn {
        padding: var(--space-sm) var(--space-lg);
        font-size: 1rem;
        border-radius: var(--radius-md);
    }

    /* Vinyl animation */
    .hero-visual {
        position: relative;
        z-index: 1;
        flex-shrink: 0;
    }

    .vinyl-record {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: 
            radial-gradient(circle at center, #1a1a2e 0%, #1a1a2e 20%, #2d2d44 20%, #2d2d44 22%, #1a1a2e 22%, #1a1a2e 24%, #2d2d44 24%, #2d2d44 26%, #1a1a2e 26%, #1a1a2e 100%);
        border: 3px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: spin-record 8s linear infinite;
        box-shadow: 0 0 40px rgba(108, 92, 231, 0.2), var(--shadow-lg);
        position: relative;
    }

    .vinyl-inner {
        position: absolute;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--card-bg);
        border: 2px solid var(--border);
    }

    .vinyl-label {
        position: relative;
        z-index: 1;
        font-size: 1.2rem;
    }

    @keyframes spin-record {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* ---- Recently Explored ---- */
    .recent-artist-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        text-decoration: none;
        color: var(--text);
        width: 110px;
        transition: transform 0.2s ease;
    }

    .recent-artist-card:hover {
        transform: translateY(-4px);
    }

    .recent-image {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        overflow: hidden;
        position: relative;
        border: 2px solid var(--border);
        transition: border-color 0.2s;
        background: var(--card-bg);
    }

    .recent-artist-card:hover .recent-image {
        border-color: var(--accent);
    }

    .recent-image img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .recent-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        font-weight: bold;
        color: var(--text-secondary);
        background: var(--bg);
    }

    .recent-overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(to bottom, transparent 60%, rgba(0,0,0,0.3));
        opacity: 0;
        transition: opacity 0.2s;
        border-radius: 50%;
    }

    .recent-artist-card:hover .recent-overlay {
        opacity: 1;
    }

    .recent-name {
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 100%;
        color: var(--text);
    }

    /* ---- Artist Card Wrapper ---- */
    .artist-card-wrapper {
        width: 200px;
    }

    /* ---- Empty genres state ---- */
    .empty-genres {
        display: flex;
        align-items: center;
        gap: var(--space-md);
        padding: var(--space-lg);
    }
    .empty-icon { font-size: 2rem; }
    .empty-genres p { color: var(--text-secondary); margin: 0; }
    .empty-genres a { color: var(--accent); }

    /* ---- Quick Actions ---- */
    .quick-actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: var(--space-md);
    }

    .quick-action-card {
        display: flex;
        align-items: center;
        gap: var(--space-md);
        padding: var(--space-lg);
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        text-decoration: none;
        color: var(--text);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .quick-action-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent);
    }

    .action-icon {
        font-size: 1.8rem;
        flex-shrink: 0;
    }

    .action-text {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .action-label {
        font-weight: 700;
        font-size: 1rem;
    }

    .action-desc {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    /* ---- Responsive ---- */
    @media (max-width: 640px) {
        .hero {
            flex-direction: column;
            text-align: center;
            padding: var(--space-xl) var(--space-md);
        }
        .hero-content {
            align-items: center;
        }
        .hero-badge {
            margin: 0 auto;
        }
        .hero-actions {
            justify-content: center;
        }
        .vinyl-record {
            width: 100px;
            height: 100px;
        }
    }
</style>
