<script lang="ts">
	import type { MBRelation } from '$lib/types';
	import { slugify } from '$lib/utils/slugify';
	
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
	
	/**
	 * Resolve the display name and (best-effort) slug for a relation.
	 * The backend stores raw MusicBrainz relation dicts, where the target
	 * name lives under `target.name`. The frontend MBRelation type also
	 * supports a flat `target_name` for normalized records.
	 */
	function resolveRelation(rel: MBRelation) {
		// Raw MusicBrainz shape: { target: { name } }
		const rawTarget = (rel as { target?: { name?: string } }).target;
		const name = rel.target_name || rawTarget?.name || 'Unknown';
		return { name, slug: slugify(name) };
	}
</script>

{#if relations && relations.length > 0}
	<div class="artist-relations mt-lg">
		<h3 class="font-bold text-lg mb-sm">Relationships</h3>
		
		<div class="relations-grid">
			{#each Object.entries(groupedRelations) as [type, rels] (type)}
				<div class="relation-group">
					<h4 class="text-sm text-secondary mb-xs capitalize">{type.replace(/_/g, ' ')}</h4>
					<ul class="relation-list">
						{#each rels as rel (rel.target_name || rel.target_mbid || rel.type)}
							{@const { name, slug } = resolveRelation(rel)}
							<li>
								<a href="/artist/{slug}" class="entity-link">
									{name}
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
		background: var(--card-bg);
		padding: 1.5rem;
		border-radius: var(--radius-md);
		border: 1px solid var(--border);
	}
	
	.relations-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1.5rem;
	}
	
	.relation-group {
		background: var(--bg);
		padding: 1rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border);
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
		color: var(--accent);
		text-decoration: none;
		font-weight: 500;
	}
	
	.entity-link:hover {
		text-decoration: underline;
	}
</style>
