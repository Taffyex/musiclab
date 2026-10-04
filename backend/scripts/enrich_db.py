"""Background script to gradually enrich the MusicLab database with real metadata, images, and releases."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

import aiosqlite
import httpx

# Add backend directory to sys.path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.common.utils import slugify
from app.config import settings
from app.discogs.client import DiscogsClient
from app.lastfm.client import LastfmClient
from app.musicbrainz.client import MusicBrainzClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("enrich_db")


def clean_artist_name(name: str) -> str:
    """Strip Discogs disambiguation numbers, e.g. 'Genesis (2)' -> 'Genesis'."""
    return re.sub(r"\s*\(\d+\)$", "", name).strip()


async def fetch_deezer_image(client: httpx.AsyncClient, name: str) -> str:
    """Fetch high-res artist picture from Deezer public search API."""
    clean = clean_artist_name(name)
    try:
        r = await client.get("https://api.deezer.com/search/artist", params={"q": clean})
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data and isinstance(data, list):
                return (
                    data[0].get("picture_xl")
                    or data[0].get("picture_big")
                    or data[0].get("picture_medium")
                    or ""
                )
    except Exception as e:
        logger.debug("Deezer image fetch error for '%s': %s", clean, e)
    return ""


async def resolve_or_create_genre(db: aiosqlite.Connection, genre_name: str) -> int | None:
    """Find or insert a genre record, returning its primary key ID."""
    genre_name = genre_name.strip()
    if not genre_name:
        return None
    slug = slugify(genre_name)
    if not slug:
        return None
    try:
        async with db.execute("SELECT id FROM genres WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return int(row["id"])

        await db.execute(
            "INSERT INTO genres (name, slug, source) VALUES (?, ?, 'discogs') ON CONFLICT(slug) DO NOTHING",
            (genre_name, slug),
        )
        async with db.execute("SELECT id FROM genres WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return int(row["id"])
    except Exception as e:
        logger.warning("Failed to resolve or create genre '%s': %s", genre_name, e)
    return None


async def resolve_or_create_style(
    db: aiosqlite.Connection, style_name: str, genre_id: int
) -> int | None:
    """Find or insert a style record linked to a genre, returning its primary key ID."""
    style_name = style_name.strip()
    if not style_name or not genre_id:
        return None
    slug = slugify(style_name)
    if not slug:
        return None
    try:
        async with db.execute(
            "SELECT id FROM styles WHERE name = ? AND genre_id = ?",
            (style_name, genre_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return int(row["id"])

        await db.execute(
            "INSERT INTO styles (name, slug, genre_id, source) VALUES (?, ?, ?, 'discogs') ON CONFLICT(name, genre_id) DO NOTHING",
            (style_name, slug, genre_id),
        )
        async with db.execute(
            "SELECT id FROM styles WHERE name = ? AND genre_id = ?",
            (style_name, genre_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return int(row["id"])
    except Exception as e:
        logger.warning("Failed to resolve or create style '%s' for genre %d: %s", style_name, genre_id, e)
    return None


async def fetch_musicbrainz_data(
    mb: MusicBrainzClient,
    name: str,
    semaphore: asyncio.Semaphore,
) -> tuple[str | None, dict[str, Any]]:
    """Search MusicBrainz with score filtering and rate limiting."""
    clean = clean_artist_name(name)
    try:
        async with semaphore:
            await asyncio.sleep(1.0)
            results = await mb.search_artist(clean)
            if not results:
                return None, {}

            best = results[0]
            score_raw = best.get("score", 0)
            try:
                score = int(score_raw)
            except (ValueError, TypeError):
                score = 0

            # Require high confidence match (score >= 80)
            if score < 80:
                logger.debug("MusicBrainz match score %d < 80 for '%s', skipping", score, clean)
                return None, {}

            mb_id = best.get("id")
            if not mb_id:
                return None, {}

            await asyncio.sleep(1.0)
            full_data = await mb.get_artist_with_full_relations(mb_id)
            return mb_id, full_data
    except Exception as e:
        logger.warning("MusicBrainz fetch failed for '%s': %s", clean, e)
        return None, {}


async def fetch_discogs_artist(
    discogs: DiscogsClient, discogs_id: int | None, name: str
) -> tuple[int | None, dict[str, Any]]:
    """Retrieve artist info from Discogs, searching by name if ID is missing."""
    if not settings.discogs_token:
        return discogs_id, {}
    try:
        if discogs_id:
            data = await discogs.get_artist(discogs_id)
            return discogs_id, data
        clean = clean_artist_name(name)
        if clean and not clean.startswith("Artist "):
            search_data = await discogs.search_artist(clean)
            results = search_data.get("results", [])
            if results:
                first = results[0]
                matched_id = first.get("id")
                if matched_id:
                    artist_data = await discogs.get_artist(matched_id)
                    return matched_id, artist_data
    except Exception as e:
        logger.warning("Discogs artist lookup failed for '%s' (ID: %s): %s", name, discogs_id, e)
    return discogs_id, {}


async def fetch_discogs_releases(
    discogs: DiscogsClient, discogs_id: int | None, limit: int = 20
) -> list[dict[str, Any]]:
    """Fetch releases for an artist from Discogs."""
    if not discogs_id or not settings.discogs_token:
        return []
    try:
        return await discogs.get_artist_releases(discogs_id, limit=limit)
    except Exception as e:
        logger.warning("Discogs releases fetch failed for discogs_id %s: %s", discogs_id, e)
        return []


async def fetch_lastfm_data(
    lastfm: LastfmClient, name: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch Last.fm artist info and top tracks in parallel."""
    if not settings.lastfm_api_key:
        return {}, []
    clean = clean_artist_name(name)
    info_task = asyncio.create_task(lastfm.get_artist_info(clean))
    tracks_task = asyncio.create_task(lastfm.get_artist_top_tracks(clean, limit=10))

    info: dict[str, Any] = {}
    tracks: list[dict[str, Any]] = []

    try:
        info_res = await info_task
        if isinstance(info_res, dict):
            info = info_res
    except Exception as e:
        logger.warning("Last.fm info fetch failed for '%s': %s", clean, e)

    try:
        tracks_res = await tracks_task
        if isinstance(tracks_res, list):
            tracks = tracks_res
    except Exception as e:
        logger.warning("Last.fm top tracks fetch failed for '%s': %s", clean, e)

    return info, tracks


async def enrich_artist(
    db: aiosqlite.Connection,
    discogs: DiscogsClient,
    lastfm: LastfmClient,
    mb: MusicBrainzClient,
    http: httpx.AsyncClient,
    artist_id: int,
    current_name: str,
    discogs_id: int | None,
    mb_semaphore: asyncio.Semaphore,
    credits_limit: int = 2,
) -> bool:
    """Enrich a single artist record and all associated relational data."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Resolve Discogs data & real name if needed
    active_discogs_id = discogs_id
    discogs_data: dict[str, Any] = {}
    if discogs_id or current_name.startswith("Artist ") or not current_name:
        active_discogs_id, discogs_data = await fetch_discogs_artist(discogs, discogs_id, current_name)

    discogs_name = discogs_data.get("name") or ""
    real_name = current_name
    if (current_name.startswith("Artist ") or not current_name) and discogs_name:
        real_name = clean_artist_name(discogs_name)

    if real_name.startswith("Artist ") or not real_name.strip():
        logger.warning("Skipping artist %d: placeholder name could not be resolved (%s)", artist_id, current_name)
        await db.execute(
            """
            INSERT INTO enrichment_queue (entity_type, entity_id, priority, status, attempts, created_at, updated_at)
            VALUES ('artist', ?, 0, 'failed', 1, ?, ?)
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                status = 'failed',
                attempts = enrichment_queue.attempts + 1,
                updated_at = excluded.updated_at
            """,
            (artist_id, now_iso, now_iso),
        )
        await db.commit()
        return False

    clean_name = clean_artist_name(real_name)

    # Check if artist already has releases imported from dump
    has_releases = False
    orig_slug = ""
    async with db.execute("SELECT slug, (SELECT COUNT(*) FROM releases WHERE artist_id = ?) FROM artists WHERE id = ?", (artist_id, artist_id)) as cursor:
        row = await cursor.fetchone()
        if row:
            orig_slug = row[0] or ""
            has_releases = (row[1] > 0)

    # 2. Fetch external metadata in parallel
    lf_task = asyncio.create_task(fetch_lastfm_data(lastfm, clean_name))
    mb_task = asyncio.create_task(fetch_musicbrainz_data(mb, clean_name, mb_semaphore))
    dz_task = asyncio.create_task(fetch_deezer_image(http, clean_name))
    dc_rel_task = asyncio.create_task(fetch_discogs_releases(discogs, active_discogs_id, limit=20)) if not has_releases else None

    if dc_rel_task:
        results = await asyncio.gather(lf_task, mb_task, dz_task, dc_rel_task, return_exceptions=True)
        releases_data = results[3] if not isinstance(results[3], Exception) else []
    else:
        results = await asyncio.gather(lf_task, mb_task, dz_task, return_exceptions=True)
        releases_data = []

    lf_info, lf_tracks = results[0] if not isinstance(results[0], Exception) else ({}, [])
    mb_id, mb_info = results[1] if not isinstance(results[1], Exception) else (None, {})
    deezer_img = results[2] if not isinstance(results[2], Exception) else ""

    # Do not overwrite real release tracklists with Last.fm top tracks if artist has releases
    if has_releases:
        lf_tracks = []

    # 3. Canonical name and Slug (keep existing slug if already established)
    if has_releases and orig_slug:
        slug = orig_slug
        canonical_name = real_name
    else:
        canonical_name = clean_name
        if lf_info.get("name"):
            canonical_name = lf_info["name"]
        elif mb_info.get("name"):
            canonical_name = mb_info["name"]
        elif discogs_name:
            canonical_name = clean_artist_name(discogs_name)

        slug = slugify(canonical_name)
        if not slug:
            slug = f"artist-{artist_id}"

        # Ensure slug uniqueness against other artists
        async with db.execute("SELECT id FROM artists WHERE slug = ? AND id != ?", (slug, artist_id)) as cursor:
            if await cursor.fetchone():
                slug = f"{slug}-{artist_id}"


    # 4. Bio, Discogs Profile, Stats, Dates, Types, Relations
    bio = (lf_info.get("bio", {}).get("summary") or "").strip()
    discogs_profile = (discogs_data.get("profile") or "").strip()

    listeners = None
    playcount = None
    try:
        if lf_info.get("stats", {}).get("listeners"):
            listeners = int(lf_info["stats"]["listeners"])
        if lf_info.get("stats", {}).get("playcount"):
            playcount = int(lf_info["stats"]["playcount"])
    except (ValueError, TypeError) as e:
        logger.debug("Failed parsing listeners/playcount for '%s': %s", canonical_name, e)

    country = (mb_info.get("country") or "").strip()
    begin_date = (mb_info.get("life-span", {}).get("begin") or "").strip()
    end_date = (mb_info.get("life-span", {}).get("end") or "").strip()
    artist_type = (mb_info.get("type") or "").strip()

    mb_tags_list = [
        t.get("name") for t in mb_info.get("tags", []) if isinstance(t, dict) and t.get("name")
    ]
    mb_relations_list = (
        mb_info.get("relations", []) if isinstance(mb_info.get("relations"), list) else []
    )

    # 5. Image Resolution
    image_url = deezer_img
    if not image_url and lf_info.get("image"):
        for img_obj in reversed(lf_info.get("image", [])):
            url = img_obj.get("#text", "")
            if url and "2a96cbd8b46e442fc41c2b86b821562f" not in url:
                image_url = url
                break
    if not image_url and discogs_data.get("images"):
        images = discogs_data.get("images", [])
        if images and isinstance(images, list):
            image_url = images[0].get("uri") or images[0].get("resource_url") or ""

    # 6. Update artists table
    try:
        await db.execute(
            """
            UPDATE artists SET
                name = ?,
                slug = ?,
                discogs_id = COALESCE(?, discogs_id),
                mbid = COALESCE(?, mbid),
                bio = CASE WHEN ? != '' THEN ? ELSE bio END,
                country = CASE WHEN ? != '' THEN ? ELSE country END,
                begin_date = CASE WHEN ? != '' THEN ? ELSE begin_date END,
                end_date = CASE WHEN ? != '' THEN ? ELSE end_date END,
                artist_type = CASE WHEN ? != '' THEN ? ELSE artist_type END,
                image_url = CASE WHEN ? != '' THEN ? ELSE image_url END,
                lastfm_listeners = COALESCE(?, lastfm_listeners),
                lastfm_playcount = COALESCE(?, lastfm_playcount),
                discogs_profile = CASE WHEN ? != '' THEN ? ELSE discogs_profile END,
                mb_tags = ?,
                mb_relations = ?,
                fetched_at = ?
            WHERE id = ?
            """,
            (
                canonical_name,
                slug,
                active_discogs_id,
                mb_id,
                bio, bio,
                country, country,
                begin_date, begin_date,
                end_date, end_date,
                artist_type, artist_type,
                image_url, image_url,
                listeners,
                playcount,
                discogs_profile, discogs_profile,
                json.dumps(mb_tags_list),
                json.dumps(mb_relations_list),
                now_iso,
                artist_id,
            ),
        )
    except Exception as e:
        logger.exception("Failed to update artist record %d (%s): %s", artist_id, canonical_name, e)
        await db.execute(
            """
            INSERT INTO enrichment_queue (entity_type, entity_id, priority, status, attempts, created_at, updated_at)
            VALUES ('artist', ?, 0, 'failed', 1, ?, ?)
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                status = 'failed',
                attempts = enrichment_queue.attempts + 1,
                updated_at = excluded.updated_at
            """,
            (artist_id, now_iso, now_iso),
        )
        await db.commit()
        return False

    # 7. Releases, Genres, Styles, and Credits
    main_release_id: int | None = None
    if releases_data:
        credits_fetched_count = 0
        for rel in releases_data:
            r_id = rel.get("id")
            if not r_id or not isinstance(r_id, int):
                continue

            r_title = rel.get("title") or "Unknown Release"
            r_year = None
            try:
                if rel.get("year"):
                    r_year = int(rel["year"])
            except (ValueError, TypeError):
                r_year = None

            r_type = (rel.get("type") or "release").capitalize()
            r_format = rel.get("format") or ""
            r_label = rel.get("label") or ""
            r_thumb = rel.get("thumb") or rel.get("cover_image") or ""

            raw_genres = rel.get("genre", [])
            r_genres = raw_genres if isinstance(raw_genres, list) else ([raw_genres] if raw_genres else [])
            raw_styles = rel.get("style", [])
            r_styles = raw_styles if isinstance(raw_styles, list) else ([raw_styles] if raw_styles else [])

            try:
                await db.execute(
                    """
                    INSERT INTO releases (
                        artist_id, discogs_id, title, year, release_type, label, format, cover_url, genres, styles, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artist_id, discogs_id) DO UPDATE SET
                        title = excluded.title,
                        year = COALESCE(excluded.year, releases.year),
                        release_type = CASE WHEN excluded.release_type != '' THEN excluded.release_type ELSE releases.release_type END,
                        label = CASE WHEN excluded.label != '' THEN excluded.label ELSE releases.label END,
                        format = CASE WHEN excluded.format != '' THEN excluded.format ELSE releases.format END,
                        cover_url = CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE releases.cover_url END,
                        genres = excluded.genres,
                        styles = excluded.styles,
                        fetched_at = excluded.fetched_at
                    """,
                    (
                        artist_id,
                        r_id,
                        r_title,
                        r_year,
                        r_type,
                        r_label,
                        r_format,
                        r_thumb,
                        json.dumps(r_genres),
                        json.dumps(r_styles),
                        now_iso,
                    ),
                )
            except Exception as e:
                logger.warning("Failed inserting release %s (Discogs ID %d) for artist %d: %s", r_title, r_id, artist_id, e)
                continue

            # Fetch release row id
            rel_row_id: int | None = None
            async with db.execute(
                "SELECT id FROM releases WHERE artist_id = ? AND discogs_id = ?",
                (artist_id, r_id),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    rel_row_id = int(row["id"])
                    if main_release_id is None:
                        main_release_id = rel_row_id

            # Genre & Style taxonomy linking
            genre_ids: list[int] = []
            for g_name in r_genres:
                g_id = await resolve_or_create_genre(db, str(g_name))
                if g_id:
                    genre_ids.append(g_id)
                    try:
                        await db.execute(
                            "INSERT OR IGNORE INTO artist_genres (artist_id, genre_id) VALUES (?, ?)",
                            (artist_id, g_id),
                        )
                    except Exception as e:
                        logger.warning("Failed linking artist %d to genre %d: %s", artist_id, g_id, e)

            for s_name in r_styles:
                target_genre_id = genre_ids[0] if genre_ids else 1
                s_id = await resolve_or_create_style(db, str(s_name), target_genre_id)
                if s_id:
                    try:
                        await db.execute(
                            "INSERT OR IGNORE INTO artist_styles (artist_id, style_id) VALUES (?, ?)",
                            (artist_id, s_id),
                        )
                    except Exception as e:
                        logger.warning("Failed linking artist %d to style %d: %s", artist_id, s_id, e)

            # Credits for top releases
            if rel_row_id and credits_fetched_count < credits_limit and settings.discogs_token:
                try:
                    rel_detail = await discogs.get_release(r_id)
                    extra_artists = rel_detail.get("extraartists", [])
                    if isinstance(extra_artists, list):
                        for ea in extra_artists:
                            ea_name = (ea.get("name") or "").strip()
                            ea_role = (ea.get("role") or "").strip()
                            ea_id = ea.get("id")
                            if ea_name and ea_role:
                                ea_clean = clean_artist_name(ea_name)
                                ea_slug = slugify(ea_clean)
                                role_lower = ea_role.lower()
                                entity_type = (
                                    "studio"
                                    if any(k in role_lower for k in ["studio", "recorded at", "mixed at", "mastered at"])
                                    else "person"
                                )
                                await db.execute(
                                    """
                                    INSERT INTO credits (
                                        release_id, entity_name, entity_slug, role, entity_type, discogs_id
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                    ON CONFLICT(release_id, entity_name, role) DO UPDATE SET
                                        discogs_id = COALESCE(excluded.discogs_id, credits.discogs_id)
                                    """,
                                    (rel_row_id, ea_clean, ea_slug, ea_role, entity_type, ea_id),
                                )
                    credits_fetched_count += 1
                except Exception as e:
                    logger.warning("Failed to fetch/save credits for release %d: %s", r_id, e)

    # 8. Tracks (from Last.fm top tracks)
    if lf_tracks:
        for idx, trk in enumerate(lf_tracks, start=1):
            t_title = trk.get("name")
            if not t_title:
                continue
            t_mbid = trk.get("mbid") or None
            t_listeners = None
            t_playcount = None
            t_duration = None
            try:
                if trk.get("listeners"):
                    t_listeners = int(trk["listeners"])
                if trk.get("playcount"):
                    t_playcount = int(trk["playcount"])
                if trk.get("duration"):
                    t_duration = int(trk["duration"]) * 1000
            except (ValueError, TypeError) as e:
                logger.debug("Failed parsing track stats for '%s': %s", t_title, e)

            try:
                await db.execute(
                    """
                    INSERT INTO tracks (
                        release_id, mbid, title, position, duration_ms, lastfm_listeners, lastfm_playcount, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(release_id, position) DO UPDATE SET
                        title = excluded.title,
                        mbid = COALESCE(excluded.mbid, tracks.mbid),
                        duration_ms = COALESCE(excluded.duration_ms, tracks.duration_ms),
                        lastfm_listeners = COALESCE(excluded.lastfm_listeners, tracks.lastfm_listeners),
                        lastfm_playcount = COALESCE(excluded.lastfm_playcount, tracks.lastfm_playcount),
                        fetched_at = excluded.fetched_at
                    """,
                    (
                        main_release_id,
                        t_mbid,
                        t_title,
                        idx,
                        t_duration,
                        t_listeners,
                        t_playcount,
                        now_iso,
                    ),
                )
            except Exception as e:
                logger.warning("Failed inserting track '%s' for artist %d: %s", t_title, artist_id, e)

    # 9. Mark status as 'done' in enrichment_queue
    try:
        await db.execute(
            """
            INSERT INTO enrichment_queue (entity_type, entity_id, priority, status, attempts, created_at, updated_at)
            VALUES ('artist', ?, 0, 'done', 1, ?, ?)
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                status = 'done',
                updated_at = excluded.updated_at
            """,
            (artist_id, now_iso, now_iso),
        )
    except Exception as e:
        logger.warning("Failed updating enrichment queue for artist %d: %s", artist_id, e)

    await db.commit()
    logger.info(
        "[OK] Enriched: %s (ID: %d, Listeners: %s, Image: %s, Releases: %d, Tracks: %d)",
        canonical_name,
        artist_id,
        f"{listeners:,}" if listeners else "N/A",
        "YES" if image_url else "NO",
        len(releases_data),
        len(lf_tracks),
    )
    return True


async def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich MusicLab artists database in background.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of artists to enrich in this run.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between artist enrichments in seconds.")
    parser.add_argument("--db", type=str, default="", help="Path to SQLite database (defaults to DATABASE_PATH config).")
    parser.add_argument("--force", action="store_true", help="Re-enrich artists even if already populated.")
    parser.add_argument("--only-without-image", action="store_true", help="Only process artists missing images.")
    parser.add_argument("--queue-only", action="store_true", help="Only process items queued in enrichment_queue.")
    parser.add_argument("--artist-id", type=int, default=None, help="Enrich a single artist by ID.")
    parser.add_argument("--artist-name", type=str, default=None, help="Enrich a single artist by name.")
    parser.add_argument("--credits-limit", type=int, default=2, help="Max releases to fetch detailed credits for.")
    args = parser.parse_args()

    target_db = args.db or settings.database_path
    db_path = os.path.abspath(target_db) if os.path.isabs(target_db) else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", target_db))
    if not os.path.exists(db_path):
        logger.error("Database file not found at %s", db_path)
        return


    logger.info(
        "Opening database at %s (Limit: %d, Delay: %.1fs, Force: %s, QueueOnly: %s)",
        db_path,
        args.limit,
        args.delay,
        args.force,
        args.queue_only,
    )

    discogs = DiscogsClient(token=settings.discogs_token)
    lastfm = LastfmClient(api_key=settings.lastfm_api_key)
    mb = MusicBrainzClient(contact_email=settings.musicbrainz_contact_email)
    http = httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "MusicLab/1.0"})
    mb_semaphore = asyncio.Semaphore(1)

    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row

            artists_to_enrich: list[aiosqlite.Row] = []

            # 1. Direct single-artist query
            if args.artist_id is not None:
                async with db.execute(
                    "SELECT id, name, discogs_id FROM artists WHERE id = ?",
                    (args.artist_id,),
                ) as cursor:
                    artists_to_enrich = await cursor.fetchall()
            elif args.artist_name is not None:
                async with db.execute(
                    "SELECT id, name, discogs_id FROM artists WHERE name LIKE ? LIMIT ?",
                    (f"%{args.artist_name}%", args.limit),
                ) as cursor:
                    artists_to_enrich = await cursor.fetchall()
            elif args.queue_only:
                async with db.execute(
                    """
                    SELECT a.id, a.name, a.discogs_id
                    FROM enrichment_queue q
                    JOIN artists a ON a.id = q.entity_id
                    WHERE q.entity_type = 'artist' AND q.status = 'pending'
                    ORDER BY q.priority DESC, q.id ASC
                    LIMIT ?
                    """,
                    (args.limit,),
                ) as cursor:
                    artists_to_enrich = await cursor.fetchall()
            else:
                # Check if there are pending items in enrichment_queue first
                async with db.execute(
                    """
                    SELECT a.id, a.name, a.discogs_id
                    FROM enrichment_queue q
                    JOIN artists a ON a.id = q.entity_id
                    WHERE q.entity_type = 'artist' AND q.status = 'pending'
                    ORDER BY q.priority DESC, q.id ASC
                    LIMIT ?
                    """,
                    (args.limit,),
                ) as cursor:
                    artists_to_enrich = await cursor.fetchall()

                # If queue has fewer items than limit, pull from artists table
                if len(artists_to_enrich) < args.limit:
                    remaining_limit = args.limit - len(artists_to_enrich)
                    existing_ids = [r["id"] for r in artists_to_enrich]
                    id_filter = f"AND a.id NOT IN ({','.join('?' * len(existing_ids))})" if existing_ids else ""

                    if args.force:
                        query = f"""
                            SELECT a.id, a.name, a.discogs_id
                            FROM artists a
                            WHERE 1=1 {id_filter}
                            ORDER BY a.id ASC
                            LIMIT ?
                        """
                        params = (*existing_ids, remaining_limit)
                    elif args.only_without_image:
                        query = f"""
                            SELECT a.id, a.name, a.discogs_id
                            FROM artists a
                            WHERE (a.image_url = '' OR a.image_url IS NULL) {id_filter}
                            ORDER BY a.id ASC
                            LIMIT ?
                        """
                        params = (*existing_ids, remaining_limit)
                    else:
                        query = f"""
                            SELECT a.id, a.name, a.discogs_id,
                                   (SELECT COUNT(*) FROM artist_genres ag WHERE ag.artist_id = a.id) +
                                   (SELECT COUNT(*) FROM artist_styles ast WHERE ast.artist_id = a.id) as link_count
                            FROM artists a
                            WHERE (
                                a.image_url = '' OR a.image_url IS NULL
                                OR a.lastfm_listeners IS NULL
                                OR a.discogs_profile = '' OR a.discogs_profile IS NULL
                                OR a.name LIKE 'Artist %'
                            ) {id_filter}
                            ORDER BY link_count DESC, a.id ASC
                            LIMIT ?
                        """
                        params = (*existing_ids, remaining_limit)

                    async with db.execute(query, params) as cursor:
                        more_artists = await cursor.fetchall()
                        artists_to_enrich.extend(more_artists)

            total = len(artists_to_enrich)
            logger.info("Found %d artists prioritized for enrichment.", total)

            success_count = 0
            for idx, row in enumerate(artists_to_enrich, start=1):
                a_id = row["id"]
                name = row["name"]
                dc_id = row["discogs_id"]

                try:
                    logger.info("[%d/%d] Processing %s (ID: %d, Discogs ID: %s)...", idx, total, name, a_id, dc_id)
                    success = await enrich_artist(
                        db=db,
                        discogs=discogs,
                        lastfm=lastfm,
                        mb=mb,
                        http=http,
                        artist_id=a_id,
                        current_name=name,
                        discogs_id=dc_id,
                        mb_semaphore=mb_semaphore,
                        credits_limit=args.credits_limit,
                    )
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.exception("[%d/%d] Error enriching artist %s (ID: %d): %s", idx, total, name, a_id, e)

                if idx < total:
                    await asyncio.sleep(args.delay)

            logger.info("Enrichment run finished: %d / %d artists successfully enriched.", success_count, total)

    finally:
        await discogs.close()
        await lastfm.close()
        await mb.close()
        await http.aclose()


if __name__ == "__main__":
    asyncio.run(main())
