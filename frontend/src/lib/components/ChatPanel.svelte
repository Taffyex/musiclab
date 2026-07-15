<script lang="ts">
	import { apiClient } from '$lib/api';
	
	interface Message {
		role: 'user' | 'assistant';
		content: string;
	}

	let { initialMessages = [] }: { initialMessages?: Message[] } = $props();
	
	let messages: Message[] = $state([...initialMessages]);
	let inputMessage = $state('');
	let isStreaming = $state(false);
	let chatContainer: HTMLElement;

	function scrollToBottom() {
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	}

	$effect(() => {
		if (isStreaming || messages.length > 0) {
			scrollToBottom();
		}
	});

	async function sendMessage() {
		if (!inputMessage.trim() || isStreaming) return;

		const userContent = inputMessage.trim();
		messages = [...messages, { role: 'user', content: userContent }];
		inputMessage = '';
		isStreaming = true;

		// Add an empty assistant message that will be populated via SSE
		messages = [...messages, { role: 'assistant', content: '' }];

		try {
			const stream = apiClient.llm.chatMessage(userContent);
			for await (const chunk of stream) {
				// Update the last message (the assistant's response)
				messages[messages.length - 1].content += chunk;
			}
		} catch (error) {
			console.error('Chat error:', error);
			messages[messages.length - 1].content += '\n\n[Error communicating with the assistant.]';
		} finally {
			isStreaming = false;
			setTimeout(scrollToBottom, 50);
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}
</script>

<div class="chat-panel card flex-col">
	<div class="chat-history" bind:this={chatContainer}>
		{#if messages.length === 0}
			<div class="flex-center h-full text-secondary">
				Start a conversation about your music taste!
			</div>
		{:else}
			{#each messages as msg}
				<div class="message {msg.role}">
					<div class="message-bubble">
						{msg.content}
					</div>
				</div>
			{/each}
		{/if}
	</div>

	<div class="chat-input-area mt-md">
		<textarea
			class="input"
			placeholder="Ask for recommendations..."
			bind:value={inputMessage}
			onkeydown={handleKeydown}
			rows="2"
			disabled={isStreaming}
		></textarea>
		<button 
			class="btn btn-primary mt-sm send-btn" 
			onclick={sendMessage} 
			disabled={isStreaming || !inputMessage.trim()}
		>
			{#if isStreaming}
				<span class="spinner"></span>
			{:else}
				Send
			{/if}
		</button>
	</div>
</div>

<style>
	.chat-panel {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: var(--bg-secondary);
	}

	.chat-history {
		flex: 1;
		overflow-y: auto;
		padding-right: var(--space-sm);
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.h-full { height: 100%; }
	.mt-sm { margin-top: var(--space-sm); }
	.mt-md { margin-top: var(--space-md); }

	.message {
		display: flex;
		width: 100%;
	}

	.message.user {
		justify-content: flex-end;
	}

	.message.assistant {
		justify-content: flex-start;
	}

	.message-bubble {
		max-width: 80%;
		padding: var(--space-sm) var(--space-md);
		border-radius: var(--radius-lg);
		white-space: pre-wrap;
	}

	.message.user .message-bubble {
		background: var(--accent);
		color: white;
		border-bottom-right-radius: 4px;
	}

	.message.assistant .message-bubble {
		background: var(--bg);
		color: var(--text);
		border: 1px solid var(--border);
		border-bottom-left-radius: 4px;
	}

	.chat-input-area {
		display: flex;
		flex-direction: column;
	}

	.input {
		resize: none;
	}

	.send-btn {
		align-self: flex-end;
	}
</style>
