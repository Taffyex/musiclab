<script lang="ts">
    interface Props {
        artistName: string;
        discogsId?: number | null;
        mbid?: string | null;
    }

    let { artistName, discogsId = null, mbid = null }: Props = $props();

    // Derived URLs based on the artist info
    let lastfmUrl = $derived(`https://www.last.fm/music/${encodeURIComponent(artistName)}`);
    let spotifyUrl = $derived(`https://open.spotify.com/search/${encodeURIComponent(artistName)}`);
    let youtubeUrl = $derived(`https://music.youtube.com/search?q=${encodeURIComponent(artistName)}`);
    let discogsUrl = $derived(discogsId ? `https://www.discogs.com/artist/${discogsId}` : null);
    let musicBrainzUrl = $derived(mbid ? `https://musicbrainz.org/artist/${mbid}` : null);
</script>

<div class="external-links">
    <a href={lastfmUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
        <span>🎧</span> Last.fm
    </a>
    
    <a href={spotifyUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
        <span>🟢</span> Spotify
    </a>
    
    <a href={youtubeUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
        <span>▶️</span> YouTube Music
    </a>
    
    {#if discogsUrl}
        <a href={discogsUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
            <span>📀</span> Discogs
        </a>
    {/if}
    
    {#if musicBrainzUrl}
        <a href={musicBrainzUrl} target="_blank" rel="noopener noreferrer" class="link-btn">
            <span>🎼</span> MusicBrainz
        </a>
    {/if}
</div>

<style>
    .external-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .link-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 9999px; /* Pill shape */
        color: var(--text);
        text-decoration: none;
        font-size: 0.875rem;
        font-weight: 500;
        transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
    }
    
    .link-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: var(--bg);
    }
</style>
