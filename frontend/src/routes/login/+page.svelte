<script lang="ts">
  import { login } from '$lib/stores/auth';
  
  let username = '';
  let password = '';
  
  async function handleSubmit() {
    await login(username, password);
    // Redirect happens in the store or client
  }
</script>

<div class="login-container">
  <h2>Login to MusicLab</h2>
  <form on:submit|preventDefault={handleSubmit}>
    <input type="text" bind:value={username} placeholder="Username" />
    <input type="password" bind:value={password} placeholder="Password" />
    <button type="submit">Login</button>
  </form>
</div>

<style>
  .login-container {
    max-width: 400px;
    margin: 4rem auto;
    padding: 2rem;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  h2 { margin-top: 0; }
  input {
    width: 100%;
    margin-bottom: 1rem;
    padding: 0.5rem;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
  }
  button {
    width: 100%;
    padding: 0.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
