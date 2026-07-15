<script lang="ts">
	import type { ChatMessage as ChatMessageType } from '$lib/types';

	interface Props {
		message: ChatMessageType;
	}

	let { message }: Props = $props();
</script>

<div class="chat-message" class:user={message.role === 'user'} class:assistant={message.role === 'assistant'}>
	<div class="message-avatar">
		{#if message.role === 'user'}
			👤
		{:else}
			🤖
		{/if}
	</div>
	<div class="message-bubble">
		<p class="message-content">{message.content}</p>
	</div>
</div>

<style>
	.chat-message {
		display: flex;
		gap: var(--space-sm);
		max-width: 80%;
	}

	.chat-message.user {
		align-self: flex-end;
		flex-direction: row-reverse;
	}

	.chat-message.assistant {
		align-self: flex-start;
	}

	.message-avatar {
		font-size: 1.25rem;
		flex-shrink: 0;
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.message-bubble {
		padding: var(--space-sm) var(--space-md);
		border-radius: var(--radius-lg);
		line-height: 1.5;
	}

	.user .message-bubble {
		background: var(--accent);
		color: #ffffff;
		border-bottom-right-radius: var(--radius-sm);
	}

	.assistant .message-bubble {
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-bottom-left-radius: var(--radius-sm);
	}

	.message-content {
		white-space: pre-wrap;
		word-break: break-word;
	}
</style>
