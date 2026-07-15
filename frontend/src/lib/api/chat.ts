// ===== Chat API =====

import { API_BASE } from './client';
import { apiGet } from './client';
import type { MemoryBlock } from '$lib/types';

/**
 * Send a chat message and receive a Server-Sent Events stream.
 * Returns an EventSource that emits 'message' events with streamed tokens.
 *
 * Usage:
 *   const source = sendMessage('recommend something jazzy');
 *   source.addEventListener('message', (e) => { console.log(e.data); });
 *   source.addEventListener('error', () => { source.close(); });
 */
export function sendMessage(message: string): EventSource {
	const params = new URLSearchParams({ message });
	const url = `${API_BASE}/chat/stream?${params.toString()}`;

	const eventSource = new EventSource(url, {
		// Note: EventSource sends cookies automatically for same-origin
	});

	return eventSource;
}

/**
 * Alternative: send message via POST and read a streaming response.
 * Useful when you need to send complex payloads or POST is required.
 */
export async function sendMessageStream(message: string): Promise<ReadableStream<string>> {
	const response = await fetch(`${API_BASE}/chat/stream`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		credentials: 'include',
		body: JSON.stringify({ message })
	});

	if (!response.ok) {
		throw new Error(`Chat request failed: ${response.status}`);
	}

	if (!response.body) {
		throw new Error('No response body');
	}

	const reader = response.body.pipeThrough(new TextDecoderStream());
	return reader.readable;
}

/** Fetch the AI's accumulated memory/context about the user */
export function getMemory(): Promise<MemoryBlock> {
	return apiGet<MemoryBlock>('/chat/memory');
}
