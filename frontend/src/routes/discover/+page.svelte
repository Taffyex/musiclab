<script lang="ts">
  import DiscoveryCard from '$lib/components/DiscoveryCard.svelte';
  
  let cards: any[] = []; // TODO: fetch from discovery store
</script>

<div class="discover-page">
  <header>
    <h1>Discover</h1>
    <button>Generate New Batch</button>
  </header>
  
  <div class="grid">
    {#each cards as card}
      <DiscoveryCard {card} />
    {/each}
  </div>
</div>

<style>
  .discover-page { padding: 2rem; }
  header { display: flex; justify-content: space-between; align-items: center; }
  button { padding: 0.5rem 1rem; background: var(--accent); color: white; border: none; border-radius: 4px; cursor: pointer; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem; }
</style>
