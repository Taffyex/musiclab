<script lang="ts">
  import ChatPanel from '$lib/components/ChatPanel.svelte';
</script>

<div class="chat-page">
  <ChatPanel />
</div>

<style>
  .chat-page {
    height: calc(100vh - 64px); /* Subtract navbar height roughly */
  }
</style>
