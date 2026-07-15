<script lang="ts">
  // TODO: state and forms
</script>

<div class="settings-page">
  <h1>Settings</h1>
  
  <div class="settings-grid">
    <section>
      <h2>Last.fm</h2>
      <input type="text" placeholder="Username" />
    </section>
    
    <section>
      <h2>Lidarr</h2>
      <input type="text" placeholder="URL" />
      <input type="password" placeholder="API Key" />
    </section>
    
    <section>
      <h2>LLM Provider</h2>
      <select>
        <option value="anthropic">Anthropic (Claude)</option>
        <option value="openai">OpenAI</option>
        <option value="ollama">Ollama</option>
      </select>
    </section>
  </div>
  
  <button class="save-btn">Save Settings</button>
</div>

<style>
  .settings-page { padding: 2rem; max-width: 800px; margin: 0 auto; }
  .settings-grid { display: grid; gap: 2rem; margin-bottom: 2rem; }
  section { background: var(--card-bg); padding: 1.5rem; border: 1px solid var(--border); border-radius: 8px; }
  h2 { margin-top: 0; font-size: 1.2rem; }
  input, select {
    display: block;
    width: 100%;
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 4px;
  }
  .save-btn {
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }
</style>
