// ===== Auth Store =====

import { writable, derived } from 'svelte/store';
import { apiPost } from '$lib/api/client';
import type { User, LoginRequest, LoginResponse } from '$lib/types';

/** Current authenticated user (null when not logged in) */
export const user = writable<User | null>(null);

/** Derived boolean for quick auth checks */
export const isAuthenticated = derived(user, ($user) => $user !== null);

/**
 * Authenticate with username and password.
 * On success, updates the user store and returns the user object.
 */
export async function login(username: string, password: string): Promise<User> {
	const payload: LoginRequest = { username, password };
	const response = await apiPost<LoginResponse>('/auth/login', payload);
	user.set(response.user);
	return response.user;
}

/** Log out and clear the user store */
export async function logout(): Promise<void> {
	try {
		await apiPost('/auth/logout');
	} finally {
		user.set(null);
	}
}

/** Check if the current session is still valid (e.g., on page load) */
export async function checkSession(): Promise<void> {
	try {
		const currentUser = await apiPost<User>('/auth/me');
		user.set(currentUser);
	} catch {
		user.set(null);
	}
}
