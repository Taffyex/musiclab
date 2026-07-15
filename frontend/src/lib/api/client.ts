// ===== MusicLab API Client =====

import type { ApiError } from '$lib/types';

/** Base URL for API requests — proxied through Vite in dev, same-origin in prod */
export const API_BASE = '/api';

export class ApiRequestError extends Error {
	status: number;
	detail: string;

	constructor(status: number, detail: string) {
		super(detail);
		this.name = 'ApiRequestError';
		this.status = status;
		this.detail = detail;
	}
}

/**
 * Generic fetch wrapper with JSON handling, credentials, and error management.
 * Automatically redirects to /login on 401 responses.
 */
export async function apiFetch<T>(
	path: string,
	options: RequestInit = {}
): Promise<T> {
	const url = `${API_BASE}${path}`;

	const headers: HeadersInit = {
		'Content-Type': 'application/json',
		...options.headers
	};

	// Remove Content-Type for FormData (browser sets it with boundary)
	if (options.body instanceof FormData) {
		delete (headers as Record<string, string>)['Content-Type'];
	}

	const response = await fetch(url, {
		...options,
		headers,
		credentials: 'include' // send auth cookies
	});

	// Handle 401 — redirect to login
	if (response.status === 401) {
		if (typeof window !== 'undefined') {
			window.location.href = '/login';
		}
		throw new ApiRequestError(401, 'Unauthorized');
	}

	// Handle other error responses
	if (!response.ok) {
		let detail = `Request failed with status ${response.status}`;
		try {
			const errorBody: ApiError = await response.json();
			detail = errorBody.detail || detail;
		} catch {
			// response body wasn't JSON, use default message
		}
		throw new ApiRequestError(response.status, detail);
	}

	// Handle 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	return response.json() as Promise<T>;
}

/** Convenience helpers */
export function apiGet<T>(path: string): Promise<T> {
	return apiFetch<T>(path, { method: 'GET' });
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
	return apiFetch<T>(path, {
		method: 'POST',
		body: body ? JSON.stringify(body) : undefined
	});
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
	return apiFetch<T>(path, {
		method: 'PUT',
		body: body ? JSON.stringify(body) : undefined
	});
}

export function apiDelete<T>(path: string): Promise<T> {
	return apiFetch<T>(path, { method: 'DELETE' });
}
