"""System prompt templates for MusicLab LLM interactions."""

from __future__ import annotations

from app.lastfm.schemas import LastfmProfile

# ---------------------------------------------------------------------------
# Base prompt
# ---------------------------------------------------------------------------

BASE_SYSTEM_PROMPT: str = """\
You are MusicLab, an AI music discovery assistant.  Your goal is to help
users find new artists and albums they will love, based on their listening
history, stated preferences, and conversational context.

Guidelines:
- Recommend artists the user does NOT already know or own.
- Favour specificity over vagueness — cite genres, eras, and sonic qualities.
- When uncertain, ask clarifying questions.
- Never fabricate listener statistics — say "I'm not sure" instead.
"""

# ---------------------------------------------------------------------------
# Section templates (filled at runtime)
# ---------------------------------------------------------------------------

PROFILE_TEMPLATE: str = """\
## User Listening Profile

Top Artists: {top_artists}
Top Albums: {top_albums}
Top Tags/Genres: {top_tags}
Recent Tracks: {recent_tracks}
Loved Tracks: {loved_tracks}
Weekly Trending Artists: {weekly_artists}
"""

MEMORY_TEMPLATE: str = """\
## Memory (learned preferences)

Core preferences: {core_preferences}
Liked recommendations: {liked_recommendations}
Disliked recommendations: {disliked_recommendations}
Noted patterns: {noted_patterns}
"""

FAVORITES_TEMPLATE: str = """\
## User's Explicit Favorites
The user has specifically marked these as their favorites. Weigh these heavily when generating recommendations:
Favorite Artists: {favorite_artists}
Favorite Genres: {favorite_genres}
Favorite Styles: {favorite_styles}
"""

# ---------------------------------------------------------------------------
# Mode-specific prompts
# ---------------------------------------------------------------------------

DISCOVERY_PROMPT: str = """\
You are in DISCOVERY mode.  Generate a batch of artist recommendations.
For each artist, provide: name, primary genre, approximate era, a short
explanation of why the user would enjoy them, and relevant tags.
Return results as a JSON array.
"""

EXPLORE_PROMPT: str = """\
You are in EXPLORE mode.  The user wants artists similar to a specific
artist.  Dig deeper than surface-level similarity — consider production
style, lyrical themes, and sonic texture.
"""

CHAT_PROMPT: str = """\
You are in CHAT mode.  Have a natural conversation about music.  Answer
questions, discuss albums, and weave in recommendations organically.
"""

MEMORY_EXTRACTION_PROMPT: str = """\
Analyse the following conversation and extract any preference signals.
Return a JSON object with keys:
- core_preferences: list of general taste statements
- liked_recommendations: list of artist names the user reacted positively to
- disliked_recommendations: list of artist names the user rejected
- noted_patterns: any other patterns you noticed
"""


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_system_prompt(
    profile: LastfmProfile | None = None,
    memory: dict | None = None,
    library: set[str] | None = None,
    favorites: dict | None = None,
    mode: str = "chat",
) -> str:
    """Assemble the full system prompt from components.

    Args:
        profile: The user's Last.fm profile data (may be ``None``).
        memory: The user's memory block dict (may be ``None``).
        library: Set of artist names already in the user's Lidarr library.
        mode: One of ``"chat"``, ``"discovery"``, or ``"explore"``.

    Returns:
        The fully assembled system prompt string.
    """
    parts = [BASE_SYSTEM_PROMPT]
    
    if profile:
        top_artists = ", ".join([a.name for a in profile.top_artists])
        top_albums = ", ".join([a.name for a in profile.top_albums])
        top_tags = ", ".join([t.name for t in profile.top_tags])
        recent_tracks = ", ".join([t.name for t in profile.recent_tracks])
        loved_tracks = ", ".join([t.name for t in profile.loved_tracks])
        weekly_artists = ", ".join([a.name for a in profile.weekly_artists])
        
        parts.append(PROFILE_TEMPLATE.format(
            top_artists=top_artists or "None",
            top_albums=top_albums or "None",
            top_tags=top_tags or "None",
            recent_tracks=recent_tracks or "None",
            loved_tracks=loved_tracks or "None",
            weekly_artists=weekly_artists or "None"
        ))
        
    if memory:
        parts.append(MEMORY_TEMPLATE.format(
            core_preferences=", ".join(memory.get("core_preferences", [])) or "None",
            liked_recommendations=", ".join(memory.get("liked_recommendations", [])) or "None",
            disliked_recommendations=", ".join(memory.get("disliked_recommendations", [])) or "None",
            noted_patterns=", ".join(memory.get("noted_patterns", [])) or "None"
        ))
        
    if favorites:
        parts.append(FAVORITES_TEMPLATE.format(
            favorite_artists=favorites.get("favorite_artists", "None"),
            favorite_genres=favorites.get("favorite_genres", "None"),
            favorite_styles=favorites.get("favorite_styles", "None"),
        ))

    if library:
        parts.append("## Artists already in library\n" + ", ".join(library) + "\n")
        
    if mode == "discovery":
        parts.append(DISCOVERY_PROMPT)
    elif mode == "explore":
        parts.append(EXPLORE_PROMPT)
    else:
        parts.append(CHAT_PROMPT)
        
    return "\n".join(parts)
