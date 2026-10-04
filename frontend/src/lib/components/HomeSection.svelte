<script lang="ts">
    import type { Snippet } from 'svelte';
    
    interface Props {
        title: string;
        subtitle?: string;
        /** Optional "See all →" link target */
        href?: string;
        /** Show skeleton loading state instead of children */
        loading?: boolean;
        /** Number of skeleton card placeholders to show when loading */
        skeletonCount?: number;
        children: Snippet;
    }
    
    let { title, subtitle, href, loading = false, skeletonCount = 5, children }: Props = $props();
</script>

<section class="home-section">
    <div class="section-header">
        <div class="title-group">
            <h2 class="section-title">{title}</h2>
            {#if subtitle}
                <p class="section-subtitle">{subtitle}</p>
            {/if}
        </div>
        {#if href}
            <a {href} class="see-all">See all →</a>
        {/if}
    </div>
    
    <div class="section-content">
        {#if loading}
            <div class="skeleton-row">
                {#each Array(skeletonCount) as _, i (i)}
                    <div class="skeleton-card shimmer" style:animation-delay="{i * 80}ms"></div>
                {/each}
            </div>
        {:else}
            {@render children()}
        {/if}
    </div>
</section>

<style>
    .home-section {
        display: flex;
        flex-direction: column;
        gap: 16px;
        width: 100%;
    }

    .section-header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: var(--space-md);
    }
    
    .title-group {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .section-title {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text);
    }
    
    .section-subtitle {
        margin: 0;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    .see-all {
        font-size: 0.875rem;
        color: var(--accent);
        text-decoration: none;
        font-weight: 600;
        white-space: nowrap;
        transition: opacity var(--transition-fast);
    }
    
    .see-all:hover {
        opacity: 0.7;
        text-decoration: underline;
    }

    /* Skeleton loading state */
    .skeleton-row {
        display: flex;
        gap: 16px;
        overflow: hidden;
    }

    .skeleton-card {
        width: 180px;
        height: 220px;
        flex-shrink: 0;
        border-radius: var(--radius-md);
        /* shimmer class applied via global app.css */
        background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border) 50%, var(--bg-secondary) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
    }

    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
</style>
