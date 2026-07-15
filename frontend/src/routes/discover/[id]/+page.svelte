<script lang="ts">
  import ArtistDetail from '$lib/components/ArtistDetail.svelte';
  import DiscoveryCard from '$lib/components/DiscoveryCard.svelte';
  import { page } from '$app/stores';
  
  // TODO: load data based on $page.params.id
  let artist = {};
  let similar: any[] = [];
</script>

<div class="artist-page">
  <ArtistDetail {artist} />
  
  <div class="similar-section">
    <h3>Similar Artists</h3>
    <div class="grid">
      {#each similar as card}
        <DiscoveryCard {card} />
      {/each}
    </div>
  </div>
</div>

<style>
  .artist-page { padding: 2rem; }
  .similar-section { margin-top: 2rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem; }
</style>
