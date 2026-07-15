# MusicLab Frontend

The frontend for MusicLab is built with [SvelteKit](https://kit.svelte.dev/) (Svelte 5 runes mode) and provides a premium, responsive user interface to interact with the AI-powered music discovery backend.

## Features

- **Authentication**: Seamless login handling integrated with the FastAPI backend.
- **State Management**: Built-in Svelte stores (`userStore`, `themeStore`, `profileStore`, `discoveryStore`) to manage global app state.
- **API Clients**: Fully typed TypeScript wrappers for communicating with the backend's `auth`, `lastfm`, `discovery`, and `llm` endpoints, including native Server-Sent Events (SSE) support for real-time LLM chat streaming.
- **Dynamic Theming**: Vanilla CSS custom properties with built-in dark and light mode support (`app.css`).
- **Core Components**:
  - `Navbar`: Navigation and theme toggling.
  - `TasteProfile`: Visualizes the user's Last.fm top artists, genres, and recent tracks.
  - `DiscoveryCard`: Displays AI-generated recommendations with match percentages and listen links.
  - `ChatPanel`: Interactive chat interface for talking with the AI, streaming responses token-by-token.

## Project Structure

- `src/app.css`: Global styles, design system tokens, and utility classes.
- `src/lib/api.ts`: Centralized API client wrappers (`apiClient`).
- `src/lib/stores.ts`: Svelte global state stores.
- `src/lib/components/`: Reusable UI components.
- `src/routes/`: SvelteKit application routes (`/`, `/login`, `/discover`, `/chat`, `/settings`).

## Developing

To start the development server:

```sh
npm install
npm run dev
```

## Building

To create a production build:

```sh
npm run build
```

The application uses `@sveltejs/adapter-static` or similar to generate a build folder that can be served by the FastAPI backend or an external static host.
