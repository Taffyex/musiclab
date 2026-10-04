<script lang="ts">
    import type { Snippet } from 'svelte';
    import { onMount } from 'svelte';
    
    interface Props {
        children: Snippet;
        gap?: string;
    }
    
    let { children, gap = '16px' }: Props = $props();

    let carouselRef: HTMLElement;
    let showLeftArrow = $state(false);
    let showRightArrow = $state(false); // Start false — updateArrows() sets it on mount

    function updateArrows() {
        if (!carouselRef) return;
        showLeftArrow = carouselRef.scrollLeft > 0;
        showRightArrow = Math.ceil(carouselRef.scrollLeft + carouselRef.clientWidth) < carouselRef.scrollWidth;
    }

    function scroll(offset: number) {
        if (carouselRef) {
            carouselRef.scrollBy({ left: offset, behavior: 'smooth' });
        }
    }

    onMount(() => {
        updateArrows();
        // Use ResizeObserver so arrow state refreshes if window resizes
        const ro = new ResizeObserver(() => updateArrows());
        ro.observe(carouselRef);
        return () => ro.disconnect();
    });
</script>

<div class="carousel-wrapper">
    {#if showLeftArrow}
        <button class="arrow-btn left" aria-label="Scroll left" onclick={() => scroll(-300)}>
            ←
        </button>
    {/if}

    <div 
        class="carousel-container" 
        bind:this={carouselRef} 
        onscroll={updateArrows}
        style:gap={gap}
    >
        {@render children()}
    </div>

    {#if showRightArrow}
        <button class="arrow-btn right" aria-label="Scroll right" onclick={() => scroll(300)}>
            →
        </button>
    {/if}
</div>

<style>
    .carousel-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        width: 100%;
    }

    .carousel-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        scrollbar-width: none; /* Firefox */
        padding-bottom: 8px; /* Room for focus rings/shadows */
        width: 100%;
        scroll-behavior: smooth;
    }

    .carousel-container::-webkit-scrollbar {
        display: none; /* Chrome/Safari/Edge */
    }

    .carousel-container > :global(*) {
        scroll-snap-align: start;
        flex-shrink: 0;
    }

    .arrow-btn {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        background: var(--card-bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 50%;
        width: 36px;
        height: 36px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        opacity: 0;
        transition: opacity 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
        box-shadow: var(--shadow);
        font-size: 1rem;
    }

    .carousel-wrapper:hover .arrow-btn {
        opacity: 1;
    }
    
    .arrow-btn:hover {
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
        box-shadow: var(--shadow-lg);
    }

    .arrow-btn.left {
        left: -18px;
    }

    .arrow-btn.right {
        right: -18px;
    }
    
    /* Gradient edges to indicate scrollable content */
    .carousel-wrapper::before,
    .carousel-wrapper::after {
        content: '';
        position: absolute;
        top: 0;
        bottom: 0;
        width: 32px;
        pointer-events: none;
        z-index: 5;
        transition: opacity 0.3s;
    }

    .carousel-wrapper::before {
        left: 0;
        background: linear-gradient(to right, var(--bg), transparent);
    }

    .carousel-wrapper::after {
        right: 0;
        background: linear-gradient(to left, var(--bg), transparent);
    }
</style>
