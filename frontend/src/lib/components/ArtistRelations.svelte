<script lang="ts">
	import type { MBRelation } from '$lib/types';
	
	interface Props {
		relations: MBRelation[];
	}
	
	let { relations }: Props = $props();
	
	// Group relations by type
	let groupedRelations = $derived.by(() => {
		const groups: Record<string, MBRelation[]> = {};
		for (const rel of relations) {
			const type = rel.type || 'other';
			if (!groups[type]) groups[type] = [];
			groups[type].push(rel);
		}
		return groups;
	});
</script>

{#if relations && relations.length > 0}
	<div class="artist-relations mt-lg">
		<h3 class="font-bold text-lg mb-sm">Relationships</h3>
		
		<div class="relations-grid">
			{#each Object.entries(groupedRelations) as [type, rels]}
				<div class="relation-group">
					<h4 class="text-sm text-secondary mb-xs capitalize">{type.replace(/_/g, ' ')}</h4>
					<ul class="relation-list">
						{#each rels as rel}
							<li>
								<a href="/artist/{rel.target_name.toLowerCase().replace(/ /g, '-')}" class="entity-link">
									{rel.target_name}
								</a>
								{#if rel.begin || rel.end}
									<span class="text-xs text-secondary ml-xs">
										({rel.begin || '?'} - {rel.end || 'Present'})
									</span>
								{/if}
							</li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.artist-relations {
		background: var(--bg-surface, #1e1e2e);
		padding: 1.5rem;
		border-radius: var(--radius-md, 8px);
		border: 1px solid var(--border-color, #333);
	}
	
	.relations-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1.5rem;
	}
	
	.relation-group {
		background: var(--bg-app, #12121c);
		padding: 1rem;
		border-radius: var(--radius-sm, 4px);
		border: 1px solid var(--border-color, #222);
	}
	
	.capitalize {
		text-transform: capitalize;
	}
	
	.relation-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.entity-link {
		color: var(--accent, #6c5ce7);
		text-decoration: none;
		font-weight: 500;
	}
	
	.entity-link:hover {
		text-decoration: underline;
	}
	
	.ml-xs {
		margin-left: 0.25rem;
	}
</style>
