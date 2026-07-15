export const API_BASE = '/api';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
	constructor(public status: number, public data: any) {
		super(data?.detail || 'An API error occurred');
		this.name = 'ApiError';
	}
}

/**
 * Base fetch wrapper that handles common configuration and error throwing
 */
async function fetchBase(endpoint: string, options: RequestInit = {}) {
	const url = `${API_BASE}${endpoint}`;
	const config: RequestInit = {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options.headers
		}
	};
	
	const response = await fetch(url, config);

	if (!response.ok) {
		let data;
		try {
			data = await response.json();
		} catch (e) {
			data = { detail: response.statusText };
		}
		throw new ApiError(response.status, data);
	}

	return response;
}

export const apiClient = {
	auth: {
		login: async (username: string, password: string) => {
			const formData = new URLSearchParams();
			formData.append('username', username);
			formData.append('password', password);

			const res = await fetch(`${API_BASE}/auth/login`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded'
				},
				body: formData.toString()
			});

			if (!res.ok) {
				const data = await res.json().catch(() => ({ detail: res.statusText }));
				throw new ApiError(res.status, data);
			}
			return res.json();
		},
		logout: async () => {
			const res = await fetchBase('/auth/logout', { method: 'POST' });
			return res.json();
		},
		me: async () => {
			const res = await fetchBase('/auth/me');
			return res.json();
		}
	},
	lastfm: {
		getProfile: async () => {
			const res = await fetchBase('/lastfm/profile');
			return res.json();
		},
		refresh: async () => {
			const res = await fetchBase('/lastfm/refresh', { method: 'POST' });
			return res.json();
		}
	},
	discovery: {
		generate: async (count: number = 8) => {
			const res = await fetchBase(`/discovery/generate?count=${count}`, { method: 'POST' });
			return res.json();
		},
		explore: async (artistName: string, count: number = 5) => {
			const res = await fetchBase(`/discovery/explore/${encodeURIComponent(artistName)}?count=${count}`);
			return res.json();
		},
		history: async () => {
			const res = await fetchBase('/discovery/history');
			return res.json();
		}
	},
	llm: {
		chatMessage: async function* (content: string) {
			const res = await fetch(`${API_BASE}/llm/chat/message`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ content })
			});

			if (!res.ok) {
				const data = await res.json().catch(() => ({ detail: res.statusText }));
				throw new ApiError(res.status, data);
			}

			const reader = res.body?.getReader();
			if (!reader) throw new Error('No readable stream available');

			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const data = line.slice(6);
						if (data === '[DONE]') {
							return;
						}
						yield data;
					}
				}
			}
		},
		getMemory: async () => {
			const res = await fetchBase('/llm/chat/memory');
			return res.json();
		}
	}
};
