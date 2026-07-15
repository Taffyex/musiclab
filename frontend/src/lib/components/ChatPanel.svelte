<script lang="ts">
	// TODO: Implement full SSE streaming, auto-scroll, markdown rendering
	import type { ChatMessage as ChatMessageType } from '$lib/types';
	import ChatMessage from './ChatMessage.svelte';
	import { sendMessage } from '$lib/api/chat';

	let messages = $state<ChatMessageType[]>([]);
	let inputText = $state('');
	let isStreaming = $state(false);
	let messagesEnd: HTMLDivElement | undefined = $state();

	function scrollToBottom() {
		messagesEnd?.scrollIntoView({ behavior: 'smooth' });
	}

	function handleSend() {
		const text = inputText.trim();
		if (!text || isStreaming) return;

		// Add user message
		messages = [...messages, { role: 'user', content: text }];
		inputText = '';
		isStreaming = true;

		// Start SSE stream
		let assistantContent = '';
		const source = sendMessage(text);

		// Add placeholder for assistant response
		messages = [...messages, { role: 'assistant', content: '' }];

		source.addEventListener('message', (event: MessageEvent) => {
			assistantContent += event.data;
			// Update the last message in place
			messages = [
				...messages.slice(0, -1),
				{ role: 'assistant', content: assistantContent }
			];
			scrollToBottom();
		});

		source.addEventListener('error', () => {
			source.close();
			isStreaming = false;
			if (!assistantContent) {
				// Remove empty placeholder on error
				messages = messages.slice(0, -1);
			}
		});

		// When the server closes the connection
		source.addEventListener('end', () => {
			source.close();
			isStreaming = false;
		});

		scrollToBottom();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSend();
		}
	}
</script>

<div class="chat-panel flex-col">
	<div class="messages-area">
		{#if messages.length === 0}
			<div class="empty-state flex-center">
				<div class="empty-content">
					<span class="empty-icon">💬</span>
					<h3>Start a Conversation</h3>
					<p class="text-secondary">
						Ask me about music recommendations, your taste profile, or anything music-related!
					</p>
				</div>
			</div>
		{:else}
			{#each messages as message}
				<ChatMessage {message} />
			{/each}
		{/if}
		<div bind:this={messagesEnd}></div>
	</div>

	<div class="input-area">
		<div class="input-wrapper flex gap-sm">
			<textarea
				class="input chat-input"
				bind:value={inputText}
				onkeydown={handleKeydown}
				placeholder="Ask about music..."
				rows={1}
				disabled={isStreaming}
			></textarea>
			<button
				class="btn btn-primary send-btn"
				onclick={handleSend}
				disabled={isStreaming || !inputText.trim()}
			>
				{#if isStreaming}
					<span class="spinner"></span>
				{:else}
					Send
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.chat-panel {
		height: calc(100vh - 60px - 2 * var(--space-lg));
		max-height: 800px;
	}

	.messages-area {
		flex: 1;
		overflow-y: auto;
		padding: var(--space-lg);
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.empty-state {
		flex: 1;
	}

	.empty-content {
		text-align: center;
	}

	.empty-icon {
		font-size: 3rem;
		display: block;
		margin-bottom: var(--space-md);
	}

	.input-area {
		padding: var(--space-md) var(--space-lg);
		border-top: 1px solid var(--border);
		background: var(--card-bg);
	}

	.chat-input {
		resize: none;
		min-height: 44px;
		max-height: 120px;
	}

	.send-btn {
		align-self: flex-end;
		min-width: 80px;
		height: 44px;
	}
</style>
