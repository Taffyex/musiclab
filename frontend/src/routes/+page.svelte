<script lang="ts">
	import { userStore } from '$lib/stores';
</script>

<div class="hero flex-col flex-center text-center gap-lg">
	<h1 class="text-2xl font-bold">Welcome to MusicLab</h1>
	<p class="text-lg text-secondary max-w">
		Discover new music tailored to your Last.fm listening history, powered by AI.
	</p>
	
	<div class="actions flex gap-md mt-lg">
		{#if $userStore}
			<a href="/discover" class="btn btn-primary">Go to Discovery</a>
			<a href="/chat" class="btn btn-secondary">Chat with AI</a>
		{:else}
			<a href="/login" class="btn btn-primary">Get Started</a>
		{/if}
	</div>
</div>

<style>
	.hero {
		padding: var(--space-2xl) 0;
	}
	
	.max-w {
		max-width: 600px;
		margin: 0 auto;
	}
	
	.mt-lg {
		margin-top: var(--space-lg);
	}
	
	h1 {
		font-size: 3rem;
		background: linear-gradient(135deg, var(--accent), var(--info));
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}
</style>
