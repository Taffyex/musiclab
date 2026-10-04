<script lang="ts">
    import { apiClient } from '$lib/api';
    import { trackModalStore } from '$lib/stores';
    import type { TrackSummary } from '$lib/types';

    interface Props {
        slug: string;
        artistName: string;
        /** Max tracks to display */
        limit?: number;
    }

    let { slug, artistName, limit = 10 }: Props = $props();

    let tracks = $state<TrackSummary[]>([]);
    let loading = $state(true);
    let error = $state<string | null>(null);

    // Audio preview state
    let activeTrackId = $state<number | null>(null);
    let isPlaying = $state(false);
    let currentTime = $state(0);
    let duration = $state(30);
    let audioElement = $state<HTMLAudioElement | null>(null);

    // Derived max play count for proportional bar widths
    let maxPlayCount = $derived(
        tracks.reduce((max, t) => Math.max(max, t.lastfm_playcount || 0), 0)
    );

    $effect(() => {
        if (slug) {
            loadTracks(slug);
        }
    });

    async function loadTracks(artistSlug: string) {
        try {
            loading = true;
            error = null;
            tracks = await apiClient.explore.getTracks(artistSlug, limit);
        } catch (err: unknown) {
            error = err instanceof Error ? err.message : 'Failed to load tracks';
            tracks = [];
        } finally {
            loading = false;
        }
    }

    function togglePlay(track: TrackSummary, event: MouseEvent) {
        event.stopPropagation();
        
        if (!track.preview_url) {
            // Fall back to opening modal with streaming links
            openModal(track);
            return;
        }

        if (activeTrackId === track.id) {
            if (isPlaying) {
                audioElement?.pause();
                isPlaying = false;
            } else {
                audioElement?.play();
                isPlaying = true;
            }
        } else {
            activeTrackId = track.id;
            if (audioElement) {
                audioElement.src = track.preview_url;
                audioElement.play().then(() => {
                    isPlaying = true;
                }).catch(() => {
                    isPlaying = false;
                });
            }
        }
    }

    function onTimeUpdate() {
        if (audioElement) {
            currentTime = audioElement.currentTime;
            duration = audioElement.duration || 30;
        }
    }

    function onAudioEnded() {
        isPlaying = false;
        currentTime = 0;
        activeTrackId = null;
    }

    function formatTime(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    function formatNumber(num: number | null | undefined): string {
        if (num === null || num === undefined) return '—';
        if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
        if (num >= 1_000) return (num / 1_000).toFixed(0) + 'K';
        return num.toLocaleString();
    }

    function openModal(track: TrackSummary) {
        trackModalStore.set({ track, artistName });
    }
</script>

<!-- Hidden audio element for preview playback -->
<audio 
    bind:this={audioElement}
    ontimeupdate={onTimeUpdate}
    onended={onAudioEnded}
></audio>

<div class="top-tracks-section">
    <div class="section-header flex-between items-center">
        <h2>🎵 Top Tracks &amp; Previews</h2>
        <span class="preview-badge">30s Audio Previews</span>
    </div>

    {#if loading}
        <div class="tracks-list">
            {#each Array(limit) as _, i (i)}
                <div class="skeleton-row card">
                    <div class="skeleton skeleton-play"></div>
                    <div class="skeleton skeleton-rank"></div>
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-bar"></div>
                </div>
            {/each}
        </div>
    {:else if error}
        <p class="error-msg">{error}</p>
    {:else if tracks.length === 0}
        <p class="text-secondary">No tracks available for this artist.</p>
    {:else}
        <div class="tracks-list">
            {#each tracks as track, i (track.id)}
                <!-- svelte-ignore a11y_click_events_have_key_events -->
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div 
                    class="track-row" 
                    class:active={activeTrackId === track.id}
                    onclick={() => openModal(track)} 
                    title="Click for full links &amp; info"
                >
                    <!-- Play / Pause Preview button -->
                    <button 
                        class="play-btn" 
                        class:playing={activeTrackId === track.id && isPlaying}
                        onclick={(e) => togglePlay(track, e)}
                        title={track.preview_url ? (activeTrackId === track.id && isPlaying ? "Pause preview" : "Play 30s preview") : "Listen on Spotify / YouTube"}
                    >
                        {#if activeTrackId === track.id && isPlaying}
                            <span class="pause-icon">⏸</span>
                        {:else if track.preview_url}
                            <span class="play-icon">▶</span>
                        {:else}
                            <span class="ext-icon">🔗</span>
                        {/if}
                    </button>

                    <div class="track-rank text-secondary">{i + 1}</div>

                    {#if track.cover_url}
                        <img src={track.cover_url} alt="" class="track-thumb" />
                    {/if}

                    <div class="track-info">
                        <div class="track-title font-medium">{track.title}</div>
                        {#if activeTrackId === track.id}
                            <div class="preview-progress-wrapper">
                                <div 
                                    class="preview-progress-bar" 
                                    style:width="{(currentTime / (duration || 30)) * 100}%"
                                ></div>
                                <span class="preview-time text-xs">{formatTime(currentTime)} / {formatTime(duration)}</span>
                            </div>
                        {/if}
                    </div>

                    <div class="track-stats">
                        <div class="play-count text-sm text-secondary" title="Total scrobbles">
                            ▶ {formatNumber(track.lastfm_playcount)}
                        </div>
                        <div class="bar-bg">
                            <div 
                                class="bar-fill" 
                                style:width="{maxPlayCount > 0 ? ((track.lastfm_playcount || 0) / maxPlayCount) * 100 : 0}%"
                            ></div>
                        </div>
                    </div>

                    <div class="track-modal-btn" title="Open listen options">
                        ⋯
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .top-tracks-section {
        display: flex;
        flex-direction: column;
        gap: var(--space-md, 1rem);
    }

    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    h2 {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text);
    }

    .preview-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: var(--radius-full);
        background: rgba(108, 92, 231, 0.15);
        color: var(--accent);
        border: 1px solid rgba(108, 92, 231, 0.3);
    }

    .tracks-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    /* Skeleton */
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    .skeleton-row {
        display: flex;
        align-items: center;
        padding: 0.75rem var(--space-md);
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        gap: var(--space-md);
    }

    .skeleton {
        background: linear-gradient(90deg, var(--bg) 25%, var(--card-bg) 50%, var(--bg) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite linear;
        border-radius: 4px;
    }

    .skeleton-play { width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0; }
    .skeleton-rank { width: 1.5rem; height: 1.5rem; flex-shrink: 0; }
    .skeleton-title { flex: 1; height: 1.25rem; }
    .skeleton-bar { width: 100px; height: 1.25rem; }

    /* Track rows */
    .track-row {
        display: flex;
        align-items: center;
        padding: 0.6rem 1rem;
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        gap: var(--space-md);
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
    }

    .track-row:hover {
        background-color: var(--bg-secondary);
        border-color: var(--accent);
        transform: translateX(3px);
    }

    .track-row.active {
        background: rgba(108, 92, 231, 0.1);
        border-color: var(--accent);
    }

    .play-btn {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        border: 1px solid var(--border);
        background: var(--bg);
        color: var(--text);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        flex-shrink: 0;
        transition: all 0.15s ease;
        font-size: 0.85rem;
    }

    .play-btn:hover {
        background: var(--accent);
        color: #ffffff;
        border-color: var(--accent);
        transform: scale(1.08);
    }

    .play-btn.playing {
        background: var(--accent);
        color: #ffffff;
        border-color: var(--accent);
        box-shadow: 0 0 12px rgba(108, 92, 231, 0.5);
    }

    .track-rank {
        width: 1.25rem;
        text-align: right;
        font-size: 0.85rem;
        font-variant-numeric: tabular-nums;
        flex-shrink: 0;
    }

    .track-thumb {
        width: 32px;
        height: 32px;
        border-radius: 4px;
        object-fit: cover;
        flex-shrink: 0;
    }

    .track-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 0;
    }

    .track-title {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 0.95rem;
        color: var(--text);
    }

    .preview-progress-wrapper {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .preview-progress-bar {
        height: 3px;
        background: var(--accent);
        border-radius: 2px;
        transition: width 0.2s linear;
        max-width: 120px;
    }

    .preview-time {
        color: var(--accent);
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }

    .track-stats {
        display: flex;
        align-items: center;
        gap: var(--space-sm);
        flex-shrink: 0;
    }

    .play-count {
        min-width: 4rem;
        text-align: right;
        font-size: 0.8rem;
        font-variant-numeric: tabular-nums;
    }

    .bar-bg {
        width: 70px;
        height: 5px;
        background-color: var(--border);
        border-radius: 3px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent), var(--info, #74b9ff));
        border-radius: 3px;
        transition: width 0.5s ease;
    }

    .track-modal-btn {
        color: var(--text-secondary);
        font-size: 1.1rem;
        padding: 0 4px;
        opacity: 0.6;
        transition: opacity 0.15s;
    }

    .track-row:hover .track-modal-btn {
        opacity: 1;
        color: var(--accent);
    }
</style>
