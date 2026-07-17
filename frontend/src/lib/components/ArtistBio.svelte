<script lang="ts">
	interface Props {
		bio: string;
	}
	
	let { bio }: Props = $props();
	let expanded = $state(false);
	
	function stripHtml(html: string) {
		let tmp = document.createElement("DIV");
		tmp.innerHTML = html;
		return tmp.textContent || tmp.innerText || "";
	}
</script>

{#if bio}
	<div class="artist-bio mt-lg">
		<h3 class="font-bold text-lg mb-sm">Biography</h3>
		<div class="bio-content" class:expanded>
			{stripHtml(bio)}
		</div>
		{#if bio.length > 300}
			<button class="expand-btn mt-sm text-accent" onclick={() => expanded = !expanded}>
				{expanded ? 'Read Less' : 'Read More'}
			</button>
		{/if}
	</div>
{/if}

<style>
	.artist-bio {
		background: var(--bg-surface, #1e1e2e);
		padding: 1.5rem;
		border-radius: var(--radius-md, 8px);
		border: 1px solid var(--border-color, #333);
	}
	
	.bio-content {
		color: var(--text-secondary, #aaa);
		line-height: 1.6;
		white-space: pre-line;
	}
	
	.bio-content:not(.expanded) {
		display: -webkit-box;
		-webkit-line-clamp: 4;
		-webkit-box-orient: vertical;  
		overflow: hidden;
	}
	
	.expand-btn {
		background: none;
		border: none;
		cursor: pointer;
		font-weight: bold;
		padding: 0;
	}
	
	.expand-btn:hover {
		text-decoration: underline;
	}
</style>
