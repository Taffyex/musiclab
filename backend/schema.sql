-- MusicLab Database Schema
-- Run via init_db() on application startup

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    lastfm_username TEXT,
    llm_provider  TEXT    DEFAULT 'anthropic',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT      PRIMARY KEY,
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS discovery_batches (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cards       JSON      NOT NULL,
    prompt_used TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memory_blocks (
    id         INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory     JSON      NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cache_entries (
    key        TEXT      PRIMARY KEY,
    value      JSON      NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- Genre/Style taxonomy (Discogs backbone + Last.fm supplemental tags)
CREATE TABLE IF NOT EXISTS genres (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    UNIQUE NOT NULL,
    slug        TEXT    UNIQUE NOT NULL,
    source      TEXT    NOT NULL DEFAULT 'discogs',  -- 'discogs' | 'lastfm'
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS styles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    slug        TEXT    NOT NULL,
    genre_id    INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    source      TEXT    NOT NULL DEFAULT 'discogs',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, genre_id)
);

-- Artist cache (enriched data from all 3 APIs)
CREATE TABLE IF NOT EXISTS artists (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    slug                TEXT    UNIQUE NOT NULL,
    discogs_id          INTEGER,
    mbid                TEXT,
    bio                 TEXT    DEFAULT '',
    country             TEXT    DEFAULT '',
    begin_date          TEXT    DEFAULT '',
    end_date            TEXT    DEFAULT '',
    artist_type         TEXT    DEFAULT '',       -- 'Person' | 'Group' | etc.
    image_url           TEXT    DEFAULT '',
    lastfm_listeners    INTEGER,
    lastfm_playcount    INTEGER,
    discogs_profile     TEXT    DEFAULT '',
    mb_tags             JSON,                     -- MusicBrainz tags array
    mb_relations        JSON,                     -- MusicBrainz relations array
    fetched_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(discogs_id),
    UNIQUE(mbid)
);

-- Many-to-many: artist ↔ genre/style
CREATE TABLE IF NOT EXISTS artist_genres (
    artist_id   INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    genre_id    INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (artist_id, genre_id)
);

CREATE TABLE IF NOT EXISTS artist_styles (
    artist_id   INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    style_id    INTEGER NOT NULL REFERENCES styles(id) ON DELETE CASCADE,
    PRIMARY KEY (artist_id, style_id)
);

-- Releases / Discography
CREATE TABLE IF NOT EXISTS releases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_id       INTEGER NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    discogs_id      INTEGER,
    mbid            TEXT,
    title           TEXT    NOT NULL,
    year            INTEGER,
    release_type    TEXT    DEFAULT '',    -- 'Album' | 'Single' | 'EP' | 'Compilation'
    label           TEXT    DEFAULT '',
    format          TEXT    DEFAULT '',
    cover_url       TEXT    DEFAULT '',
    genres          JSON,
    styles          JSON,
    fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artist_id, discogs_id)
);

-- Credits (producer, engineer, studio — linked to releases)
CREATE TABLE IF NOT EXISTS credits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id      INTEGER NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
    entity_name     TEXT    NOT NULL,
    entity_slug     TEXT    NOT NULL,
    role            TEXT    NOT NULL,       -- 'Producer' | 'Engineer' | 'Mixed By' | 'Mastered By' | 'Recorded At'
    entity_type     TEXT    NOT NULL,       -- 'person' | 'studio'
    discogs_id      INTEGER,               -- Discogs artist/label ID if available
    UNIQUE(release_id, entity_name, role)
);

-- User favorites (for future LLM seeding)
CREATE TABLE IF NOT EXISTS favorites (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entity_type TEXT    NOT NULL,           -- 'artist' | 'genre' | 'style'
    entity_id   INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_artists_slug ON artists(slug);
CREATE INDEX IF NOT EXISTS idx_artists_listeners ON artists(lastfm_listeners DESC);
CREATE INDEX IF NOT EXISTS idx_artists_playcount ON artists(lastfm_playcount DESC);
CREATE INDEX IF NOT EXISTS idx_releases_artist ON releases(artist_id);
CREATE INDEX IF NOT EXISTS idx_credits_entity_slug ON credits(entity_slug);
CREATE INDEX IF NOT EXISTS idx_credits_role ON credits(role);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_styles_genre ON styles(genre_id);
