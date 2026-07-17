<script lang="ts">
	import type { CreditEntity } from '$lib/types';
	
	interface Props {
		entity: CreditEntity;
	}
	
	let { entity }: Props = $props();
</script>

<div class="credit-header flex-col gap-sm">
	<div class="badges flex gap-sm">
		<span class="badge type-badge">{entity.entity_type === 'studio' ? 'Studio' : 'Person'}</span>
	</div>
	
	<h1 class="text-2xl font-bold">{entity.name}</h1>
	
	<div class="meta text-secondary text-sm">
		<span>Roles: {entity.roles.join(', ') || 'Unknown'}</span>
		<span> • </span>
		<span>{entity.release_count} releases</span>
	</div>
</div>

<style>
	.credit-header {
		background: var(--bg-surface, #1e1e2e);
		padding: 2rem;
		border-radius: var(--radius-lg, 12px);
		border: 1px solid var(--border-color, #333);
		text-align: center;
		align-items: center;
	}
	
	.badge {
		padding: 0.2rem 0.6rem;
		border-radius: 12px;
		font-size: 0.8rem;
		font-weight: bold;
	}
	
	.type-badge {
		background: var(--accent-alpha, rgba(108, 92, 231, 0.2));
		color: var(--accent, #6c5ce7);
	}
</style>
