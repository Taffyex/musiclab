<script lang="ts">
	import { trackModalStore } from '$lib/stores';
	
	let open = $derived($trackModalStore !== null);
	let data = $derived($trackModalStore);

	let isPlaying = $state(false);
	let currentTime = $state(0);
	let duration = $state(30);
	let audioElement = $state<HTMLAudioElement | null>(null);

	function close() {
		if (audioElement) {
			audioElement.pause();
		}
		isPlaying = false;
		trackModalStore.set(null);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && open) {
			close();
		}
	}

	function toggleAudio() {
		if (!audioElement || !data?.track.preview_url) return;
		if (isPlaying) {
			audioElement.pause();
			isPlaying = false;
		} else {
			audioElement.play().then(() => {
				isPlaying = true;
			}).catch(() => {
				isPlaying = false;
			});
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
	}

	function formatNumber(num: number | null | undefined): string {
		if (num == null) return '—';
		return new Intl.NumberFormat('en-US').format(num);
	}

	function formatDuration(ms: number | null | undefined): string {
		if (ms == null) return '—';
		const totalSeconds = Math.floor(ms / 1000);
		const minutes = Math.floor(totalSeconds / 60);
		const seconds = totalSeconds % 60;
		return `${minutes}:${seconds.toString().padStart(2, '0')}`;
	}

	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	$effect(() => {
		if (typeof window !== 'undefined') {
			if (open) {
				document.body.style.overflow = 'hidden';
			} else {
				document.body.style.overflow = '';
			}
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open && data}
	{#if data.track.preview_url}
		<audio 
			bind:this={audioElement}
			src={data.track.preview_url}
			ontimeupdate={onTimeUpdate}
			onended={onAudioEnded}
		></audio>
	{/if}

	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="backdrop flex-center" onclick={close}>
		<div class="modal card flex-col gap-md" onclick={(e) => e.stopPropagation()}>
			<button class="close-btn" onclick={close} aria-label="Close modal">×</button>
			
			<div class="header flex gap-md items-center">
				{#if data.track.cover_url}
					<img src={data.track.cover_url} alt="" class="modal-cover" />
				{/if}
				<div class="header-text flex-col">
					<h2>{data.track.title}</h2>
					<p class="text-secondary">{data.artistName}</p>
				</div>
			</div>

			<!-- Audio Preview Player if available -->
			{#if data.track.preview_url}
				<div class="player-box card flex-col gap-xs">
					<div class="flex-between items-center">
						<button class="preview-play-btn" onclick={toggleAudio}>
							{isPlaying ? '⏸ Pause Preview' : '▶ Play 30s Preview'}
						</button>
						<span class="preview-time-text text-sm">
							{formatTime(currentTime)} / {formatTime(duration)}
						</span>
					</div>
					<div class="player-progress-bg">
						<div 
							class="player-progress-fill" 
							style:width="{(currentTime / (duration || 30)) * 100}%"
						></div>
					</div>
				</div>
			{/if}

			<div class="stats flex gap-md">
				{#if data.track.duration_ms}
					<div class="stat flex-col">
						<span class="text-xs text-secondary">Duration</span>
						<span class="font-bold">{formatDuration(data.track.duration_ms)}</span>
					</div>
				{/if}
				<div class="stat flex-col">
					<span class="text-xs text-secondary">Last.fm Plays</span>
					<span class="font-bold">{formatNumber(data.track.lastfm_playcount)}</span>
				</div>
				<div class="stat flex-col">
					<span class="text-xs text-secondary">Listeners</span>
					<span class="font-bold">{formatNumber(data.track.lastfm_listeners)}</span>
				</div>
			</div>

			<div class="divider"></div>

			<div class="links flex-col gap-sm">
				<h3 class="text-xs text-secondary">Listen Full Track On</h3>
				<div class="link-buttons flex-col gap-xs">
					<a 
						href={`https://open.spotify.com/search/${encodeURIComponent(data.artistName + ' ' + data.track.title)}`} 
						target="_blank" 
						rel="noopener noreferrer" 
						class="btn link-btn spotify-btn"
					>
						🟢 Open in Spotify
					</a>
					<a 
						href={`https://music.youtube.com/search?q=${encodeURIComponent(data.artistName + ' ' + data.track.title)}`} 
						target="_blank" 
						rel="noopener noreferrer" 
						class="btn link-btn youtube-btn"
					>
						▶️ Search on YouTube Music
					</a>
					<a 
						href={`https://music.apple.com/search?term=${encodeURIComponent(data.artistName + ' ' + data.track.title)}`} 
						target="_blank" 
						rel="noopener noreferrer" 
						class="btn link-btn apple-btn"
					>
						🍎 Search on Apple Music
					</a>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.75);
		z-index: 1000;
		animation: fadeIn 0.2s ease-out forwards;
		backdrop-filter: blur(4px);
	}

	.modal {
		position: relative;
		width: 100%;
		max-width: 480px;
		margin: var(--space-md);
		padding: 1.75rem;
		background: var(--card-bg);
		animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
		border: 1px solid var(--border);
		border-radius: var(--radius-lg, 12px);
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
	}

	.close-btn {
		position: absolute;
		top: var(--space-sm);
		right: var(--space-md);
		background: none;
		border: none;
		color: var(--text-secondary);
		font-size: 1.5rem;
		cursor: pointer;
		padding: var(--space-sm);
		transition: color 0.15s;
	}
	
	.close-btn:hover {
		color: var(--text);
	}

	.modal-cover {
		width: 56px;
		height: 56px;
		border-radius: var(--radius-md);
		object-fit: cover;
		flex-shrink: 0;
		border: 1px solid var(--border);
	}

	.header-text h2 {
		margin: 0;
		font-size: 1.3rem;
		line-height: 1.2;
		color: var(--text);
	}

	.header-text p {
		margin: var(--space-xs) 0 0 0;
		font-size: 0.95rem;
	}

	.player-box {
		padding: 0.85rem 1rem;
		background: rgba(108, 92, 231, 0.1);
		border: 1px solid rgba(108, 92, 231, 0.25);
		border-radius: var(--radius-md);
	}

	.preview-play-btn {
		background: var(--accent);
		color: #ffffff;
		border: none;
		padding: 0.4rem 0.9rem;
		border-radius: var(--radius-full);
		font-size: 0.85rem;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.15s, opacity 0.15s;
	}

	.preview-play-btn:hover {
		opacity: 0.9;
		transform: scale(1.03);
	}

	.preview-time-text {
		color: var(--accent);
		font-weight: 600;
		font-variant-numeric: tabular-nums;
	}

	.player-progress-bg {
		width: 100%;
		height: 4px;
		background: var(--border);
		border-radius: 2px;
		overflow: hidden;
		margin-top: 4px;
	}

	.player-progress-fill {
		height: 100%;
		background: var(--accent);
		border-radius: 2px;
		transition: width 0.2s linear;
	}

	.stat {
		flex: 1;
		background: var(--bg);
		padding: 0.6rem 0.8rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border);
	}

	.divider {
		height: 1px;
		background: var(--border);
		margin: 0.25rem 0;
	}

	h3 {
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 700;
	}

	.link-buttons {
		width: 100%;
	}

	.link-btn {
		width: 100%;
		justify-content: flex-start;
		padding: 0.65rem 1rem;
		font-weight: 500;
		font-size: 0.9rem;
		text-decoration: none;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		transition: all 0.15s ease;
	}

	.link-btn:hover {
		background: var(--bg-secondary);
		border-color: var(--accent);
		color: var(--text);
		transform: translateX(3px);
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slideUp {
		from { 
			opacity: 0; 
			transform: translateY(20px); 
		}
		to { 
			opacity: 1; 
			transform: translateY(0); 
		}
	}
</style>
