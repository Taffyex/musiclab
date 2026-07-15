import { get } from 'svelte/store';
import { userStore } from '$lib/stores';
import { apiClient } from '$lib/api';
import { goto } from '$app/navigation';

export async function requireAuth() {
	const user = get(userStore);
	if (!user) {
		try {
			const res = await apiClient.auth.me();
			userStore.login(res.user);
			return true;
		} catch (e) {
			goto('/login');
			return false;
		}
	}
	return true;
}
