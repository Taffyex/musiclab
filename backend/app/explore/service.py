"""Business logic for the explore module."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone

import aiosqlite
import httpx

from app.common.exceptions import NotFoundError, ExternalAPIError
from app.common.utils import safe_json_dict, safe_json_list, slugify
from app.discogs.client import DiscogsClient
from app.explore.schemas import (
    ArtistDetail, ArtistSummary, Credit, CreditEntity, ExploreFilters,
    Genre, GenreTree, ReleaseDetail, ReleaseWithArtist, Style,
    FavoriteItem, UserFavorites, TrackSummary
)
from app.lastfm.client import LastfmClient
from app.musicbrainz.client import MusicBrainzClient

logger = logging.getLogger(__name__)

# Reusable SQL fragments — single source of truth for genre/style subqueries
_GENRES_SQL = """(SELECT json_group_array(g.name) FROM genres g JOIN artist_genres ag ON ag.genre_id = g.id WHERE ag.artist_id = {alias}.id) as genres"""
_STYLES_SQL = """(SELECT json_group_array(s.name) FROM styles s JOIN artist_styles ast ON ast.style_id = s.id WHERE ast.artist_id = {alias}.id) as styles"""


def _clean_artist_name(name: str) -> str:
    """Strip Discogs numeric suffixes like 'Artist (2)' -> 'Artist'."""
    return re.sub(r"\s*\(\d+\)$", "", name).strip()


async def _fetch_deezer_artist_image(name: str) -> str:
    """Fetch high-res artist image from Deezer public search."""
    clean = _clean_artist_name(name)
    try:
        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "MusicLab/1.0"}) as client:
            r = await client.get("https://api.deezer.com/search/artist", params={"q": clean})
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    return (
                        data[0].get("picture_xl")
                        or data[0].get("picture_big")
                        or data[0].get("picture_medium")
                        or ""
                    )
    except Exception:
        logger.debug("Deezer artist image lookup failed for %s", name)
    return ""


async def _fetch_deezer_track_preview(artist: str, track_title: str) -> tuple[str | None, str]:
    """Fetch 30-sec preview audio URL and album cover from Deezer."""
    clean_artist = _clean_artist_name(artist)
    clean_track = re.sub(r"\(.*?\)|\[.*?\]", "", track_title).strip()
    try:
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "MusicLab/1.0"}) as client:
            r = await client.get(
                "https://api.deezer.com/search",
                params={"q": f"{clean_artist} {clean_track}", "limit": 1},
            )
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    preview = data[0].get("preview")
                    cover = (
                        data[0].get("album", {}).get("cover_big")
                        or data[0].get("album", {}).get("cover_medium")
                        or ""
                    )
                    return preview, cover
    except Exception:
        pass
    return None, ""


class ExploreService:
    """Service for exploring genres, styles, and artists."""

    def __init__(
        self,
        db: aiosqlite.Connection,
        discogs: DiscogsClient,
        lastfm: LastfmClient,
        musicbrainz: MusicBrainzClient,
    ) -> None:
        self._db = db
        self._discogs = discogs
        self._lastfm = lastfm
        self._musicbrainz = musicbrainz

    async def get_genre_tree(self) -> list[GenreTree]:
        """Return all genres with their nested styles."""
        genres = {}
        async with self._db.execute("SELECT id, name, slug, source FROM genres ORDER BY name") as cursor:
            async for row in cursor:
                g_id, name, slug, source = row
                genres[g_id] = GenreTree(
                    genre=Genre(id=g_id, name=name, slug=slug, source=source),
                    styles=[]
                )
        
        async with self._db.execute("SELECT id, name, slug, genre_id, source FROM styles ORDER BY name") as cursor:
            async for row in cursor:
                s_id, name, slug, genre_id, source = row
                if genre_id in genres:
                    genres[genre_id].styles.append(
                        Style(id=s_id, name=name, slug=slug, genre_id=genre_id, genre_name=genres[genre_id].genre.name)
                    )
        
        for g in genres.values():
            g.genre.style_count = len(g.styles)
            
        return list(genres.values())

    async def _get_artists_by_taxonomy(
        self, slug: str, filters: ExploreFilters, *, is_style: bool = False
    ) -> tuple[list[ArtistSummary], int]:
        """Shared implementation for get_artists_by_genre and get_artists_by_style."""
        table = "styles" if is_style else "genres"
        join_table = "artist_styles" if is_style else "artist_genres"
        join_col = "style_id" if is_style else "genre_id"
        label = "Style" if is_style else "Genre"

        async with self._db.execute(f"SELECT id FROM {table} WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise NotFoundError(f"{label} {slug} not found")
            taxonomy_id = row[0]

        valid_columns = {"listeners": "a.lastfm_listeners", "scrobbles": "a.lastfm_playcount", "name": "a.name"}
        if filters.sort_by not in valid_columns:
            raise ValueError(f"Invalid sort_by: {filters.sort_by}")
        column = valid_columns[filters.sort_by]
        
        if filters.sort_order not in ("asc", "desc"):
            raise ValueError(f"Invalid sort_order: {filters.sort_order}")
        direction = "ASC" if filters.sort_order == "asc" else "DESC"

        # Exclude placeholder names ('Artist 1234') from genre and style exploration
        query = f"""
            SELECT a.id, a.name, a.slug, a.image_url, a.lastfm_listeners, a.lastfm_playcount,
                   {_GENRES_SQL.format(alias='a')},
                   {_STYLES_SQL.format(alias='a')}
            FROM artists a
            JOIN {join_table} j ON a.id = j.artist_id
            WHERE j.{join_col} = ? AND a.name NOT LIKE 'Artist %' AND a.name != ''
            ORDER BY
                CASE WHEN a.image_url != '' AND a.image_url IS NOT NULL THEN 0 ELSE 1 END,
                CASE WHEN {column} IS NOT NULL AND {column} > 0 THEN 0 ELSE 1 END,
                {column} {direction},
                a.name ASC
            LIMIT ? OFFSET ?
        """
        offset = (filters.page - 1) * filters.per_page

        artists = []
        async with self._db.execute(query, (taxonomy_id, filters.per_page, offset)) as cursor:
            async for row in cursor:
                a_id, name, art_slug, image_url, listeners, playcount, g_json, s_json = row
                artists.append(ArtistSummary(
                    id=a_id, name=name, slug=art_slug, image_url=image_url or "",
                    lastfm_listeners=listeners, lastfm_playcount=playcount,
                    genres=safe_json_list(g_json),
                    styles=safe_json_list(s_json),
                    already_in_lidarr=False,
                ))

        async with self._db.execute(
            f"SELECT COUNT(*) FROM {join_table} j JOIN artists a ON a.id = j.artist_id WHERE j.{join_col} = ? AND a.name NOT LIKE 'Artist %' AND a.name != ''",
            (taxonomy_id,)
        ) as cursor:
            total = (await cursor.fetchone())[0]

        return artists, total

    async def get_artists_by_genre(self, genre_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by genre."""
        return await self._get_artists_by_taxonomy(genre_slug, filters, is_style=False)

    async def get_artists_by_style(self, style_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by style."""
        return await self._get_artists_by_taxonomy(style_slug, filters, is_style=True)

    async def enrich_and_cache_artist(
        self, artist_name: str, existing_id: int | None = None, existing_slug: str | None = None
    ) -> ArtistDetail:
        """Enrich artist from APIs and cache."""
        clean_name = _clean_artist_name(artist_name)
        
        # Parallel fetch across Last.fm, MusicBrainz, Discogs, and Deezer
        lf_task = asyncio.create_task(self._lastfm.get_artist_info(clean_name))
        mb_task = asyncio.create_task(self._musicbrainz.search_artist(clean_name))
        dc_task = asyncio.create_task(self._discogs.search_artist(clean_name))
        deezer_task = asyncio.create_task(_fetch_deezer_artist_image(clean_name))
        
        try:
            lf_info = await lf_task
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch lastfm info for %s", clean_name)
            lf_info = {}
            
        try:
            mb_search = await mb_task
            mb_id = mb_search[0].get("id") if mb_search else None
            mb_info = await self._musicbrainz.get_artist_with_full_relations(mb_id) if mb_id else {}
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch mb info for %s", clean_name)
            mb_info = {}
            mb_id = None
            
        try:
            dc_search = await dc_task
            dc_results = dc_search.get("results", []) if dc_search else []
            dc_id = dc_results[0].get("id") if dc_results else None
            dc_cover = dc_results[0].get("cover_image", "") if dc_results else ""
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch discogs info for %s", clean_name)
            dc_id = None
            dc_cover = ""

        try:
            deezer_img = await deezer_task
        except Exception:
            deezer_img = ""
            
        # Determine best canonical name
        canonical_name = clean_name
        if lf_info.get("name"):
            canonical_name = lf_info["name"]
        elif mb_info.get("name"):
            canonical_name = mb_info["name"]
        elif dc_results and dc_results[0].get("title"):
            canonical_name = _clean_artist_name(dc_results[0]["title"])
            
        slug = existing_slug or slugify(canonical_name)

        bio = lf_info.get("bio", {}).get("summary", "")
        listeners = int(lf_info.get("stats", {}).get("listeners", 0)) or None
        playcount = int(lf_info.get("stats", {}).get("playcount", 0)) or None
        
        country = mb_info.get("country", "")
        begin_date = mb_info.get("life-span", {}).get("begin", "")
        end_date = mb_info.get("life-span", {}).get("end", "")
        artist_type = mb_info.get("type", "")
        
        mb_tags = [t.get("name") for t in mb_info.get("tags", [])]
        mb_relations = mb_info.get("relations", [])
        
        # Determine image URL: Deezer > Last.fm > Discogs
        image_url = deezer_img
        if not image_url and lf_info.get("image"):
            images = lf_info.get("image", [])
            for img_obj in reversed(images):
                url = img_obj.get("#text", "")
                if url and "2a96cbd8b46e442fc41c2b86b821562f" not in url:
                    image_url = url
                    break
        if not image_url and dc_cover and "spacer.gif" not in dc_cover:
            image_url = dc_cover

        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Insert / Update artists table
        if existing_id is not None:
            artist_id = existing_id
            try:
                await self._db.execute(
                    """
                    UPDATE artists SET
                        discogs_id = COALESCE(?, discogs_id),
                        mbid = COALESCE(?, mbid),
                        bio = CASE WHEN ? != '' AND (bio IS NULL OR bio = '') THEN ? ELSE bio END,
                        country = CASE WHEN ? != '' THEN ? ELSE country END,
                        begin_date = CASE WHEN ? != '' THEN ? ELSE begin_date END,
                        end_date = CASE WHEN ? != '' THEN ? ELSE end_date END,
                        artist_type = CASE WHEN ? != '' THEN ? ELSE artist_type END,
                        image_url = CASE WHEN ? != '' THEN ? ELSE image_url END,
                        lastfm_listeners = COALESCE(?, lastfm_listeners),
                        lastfm_playcount = COALESCE(?, lastfm_playcount),
                        mb_tags = CASE WHEN ? != '[]' THEN ? ELSE mb_tags END,
                        mb_relations = CASE WHEN ? != '[]' THEN ? ELSE mb_relations END,
                        fetched_at = ?
                    WHERE id = ?
                    """,
                    (
                        dc_id, mb_id, bio, bio, country, country, begin_date, begin_date,
                        end_date, end_date, artist_type, artist_type, image_url, image_url,
                        listeners, playcount,
                        json.dumps(mb_tags), json.dumps(mb_tags),
                        json.dumps(mb_relations), json.dumps(mb_relations),
                        now_iso, artist_id
                    )
                )
                await self._db.commit()
            except Exception:
                logger.exception("Failed to update existing artist id=%d", artist_id)
        else:
            try:
                await self._db.execute(
                    """
                    INSERT INTO artists (
                        name, slug, discogs_id, mbid, bio, country, begin_date, end_date,
                        artist_type, image_url, lastfm_listeners, lastfm_playcount,
                        mb_tags, mb_relations, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        name=excluded.name,
                        discogs_id=COALESCE(excluded.discogs_id, artists.discogs_id),
                        mbid=COALESCE(excluded.mbid, artists.mbid),
                        bio=CASE WHEN excluded.bio != '' THEN excluded.bio ELSE artists.bio END,
                        country=CASE WHEN excluded.country != '' THEN excluded.country ELSE artists.country END,
                        begin_date=CASE WHEN excluded.begin_date != '' THEN excluded.begin_date ELSE artists.begin_date END,
                        end_date=CASE WHEN excluded.end_date != '' THEN excluded.end_date ELSE artists.end_date END,
                        artist_type=CASE WHEN excluded.artist_type != '' THEN excluded.artist_type ELSE artists.artist_type END,
                        image_url=CASE WHEN excluded.image_url != '' THEN excluded.image_url ELSE artists.image_url END,
                        lastfm_listeners=COALESCE(excluded.lastfm_listeners, artists.lastfm_listeners),
                        lastfm_playcount=COALESCE(excluded.lastfm_playcount, artists.lastfm_playcount),
                        mb_tags=excluded.mb_tags,
                        mb_relations=excluded.mb_relations,
                        fetched_at=excluded.fetched_at
                    """,
                    (
                        canonical_name, slug, dc_id, mb_id, bio, country, begin_date, end_date,
                        artist_type, image_url, listeners, playcount,
                        json.dumps(mb_tags), json.dumps(mb_relations), now_iso
                    )
                )
                await self._db.commit()
            except Exception:
                logger.exception("Failed to insert enriched artist: %s", canonical_name)
                
            async with self._db.execute("SELECT id, image_url FROM artists WHERE slug = ?", (slug,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise NotFoundError(f"Artist {canonical_name} could not be cached.")
                artist_id = row[0]
                if not image_url and row[1]:
                    image_url = row[1]
                
        # Only fetch Discogs releases if artist has 0 releases in DB
        async with self._db.execute("SELECT COUNT(*) FROM releases WHERE artist_id = ?", (artist_id,)) as c:
            already_has_releases = (await c.fetchone())[0] > 0
            
        if dc_id and not already_has_releases:

            try:
                releases_data = await self._discogs.get_artist_releases(dc_id, limit=30)
                all_genres = set()
                all_styles = set()
                
                for rel in releases_data:
                    r_id = rel.get("id")
                    r_title = rel.get("title", "Unknown Release")
                    r_year = rel.get("year")
                    r_type = rel.get("type", "release").capitalize()
                    r_format = rel.get("format", "")
                    r_label = rel.get("label", "")
                    r_thumb = rel.get("thumb", "") or rel.get("cover_image", "")
                    r_genres = rel.get("genre", []) if isinstance(rel.get("genre"), list) else []
                    r_styles = rel.get("style", []) if isinstance(rel.get("style"), list) else []
                    
                    all_genres.update(r_genres)
                    all_styles.update(r_styles)
                    
                    if r_id:
                        await self._db.execute(
                            """
                            INSERT INTO releases (
                                artist_id, discogs_id, title, year, release_type, label, format, cover_url, genres, styles, fetched_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(artist_id, discogs_id) DO UPDATE SET
                                title=excluded.title,
                                year=COALESCE(excluded.year, releases.year),
                                release_type=excluded.release_type,
                                label=excluded.label,
                                format=excluded.format,
                                cover_url=CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE releases.cover_url END,
                                genres=excluded.genres,
                                styles=excluded.styles,
                                fetched_at=excluded.fetched_at
                            """,
                            (
                                artist_id, r_id, r_title, r_year, r_type, r_label, r_format,
                                r_thumb, json.dumps(r_genres), json.dumps(r_styles), now_iso
                            )
                        )
                
                # Link genres
                for genre_name in all_genres:
                    genre_slug = slugify(genre_name)
                    await self._db.execute(
                        "INSERT OR IGNORE INTO genres (name, slug, source) VALUES (?, ?, 'discogs')",
                        (genre_name, genre_slug)
                    )
                    async with self._db.execute("SELECT id FROM genres WHERE slug = ?", (genre_slug,)) as c:
                        g_row = await c.fetchone()
                        if g_row:
                            await self._db.execute(
                                "INSERT OR IGNORE INTO artist_genres (artist_id, genre_id) VALUES (?, ?)",
                                (artist_id, g_row[0])
                            )
                
                # Link styles
                for style_name in all_styles:
                    style_slug = slugify(style_name)
                    for genre_name in all_genres:
                        genre_slug = slugify(genre_name)
                        async with self._db.execute("SELECT id FROM genres WHERE slug = ?", (genre_slug,)) as c:
                            g_row = await c.fetchone()
                            if g_row:
                                await self._db.execute(
                                    "INSERT OR IGNORE INTO styles (name, slug, genre_id, source) VALUES (?, ?, ?, 'discogs')",
                                    (style_name, style_slug, g_row[0])
                                )
                                async with self._db.execute("SELECT id FROM styles WHERE slug = ? AND genre_id = ?", (style_slug, g_row[0])) as sc:
                                    s_row = await sc.fetchone()
                                    if s_row:
                                        await self._db.execute(
                                            "INSERT OR IGNORE INTO artist_styles (artist_id, style_id) VALUES (?, ?)",
                                            (artist_id, s_row[0])
                                        )
                                break
                
                await self._db.commit()
            except Exception:
                logger.exception("Failed to populate releases and genre/style mappings for %s", canonical_name)

        # Populate full artist detail with releases, top tracks, and similar artists
        releases = await self.get_artist_releases(slug)
        top_tracks = await self.get_artist_top_tracks(slug)
        similar = await self.get_similar_artists(slug)

        return ArtistDetail(
            id=artist_id, name=canonical_name, slug=slug, bio=bio,
            discogs_profile="", discogs_id=dc_id, mbid=mb_id,
            country=country, begin_date=begin_date, end_date=end_date,
            artist_type=artist_type, image_url=image_url or "",
            lastfm_listeners=listeners, lastfm_playcount=playcount,
            mb_tags=mb_tags, mb_relations=mb_relations,
            releases=releases, top_tracks=top_tracks, similar_artists=similar
        )

    async def get_artist_detail(self, artist_slug: str) -> ArtistDetail:
        """Get full artist profile with on-demand enrichment if missing or incomplete."""
        query = f"""
            SELECT id, name, slug, bio, discogs_profile, discogs_id, mbid,
                   country, begin_date, end_date,
                   artist_type, image_url, lastfm_listeners, lastfm_playcount,
                   {_GENRES_SQL.format(alias='artists')},
                   {_STYLES_SQL.format(alias='artists')},
                   mb_tags, mb_relations, fetched_at
            FROM artists WHERE slug = ?
        """
        async with self._db.execute(query, (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            name = artist_slug.replace('-', ' ').title()
            return await self.enrich_and_cache_artist(name)
            
        a_id, name, slug, bio, dp, dc_id, mb_id, country, bd, ed, atype, img, listeners, playcount, g_json, s_json, mb_tags_json, mb_rels_json, fetched = row
        
        # If artist is a placeholder name or has no bio & no image & no listener stats, enrich immediately!
        is_placeholder = name.startswith("Artist ") or not name
        is_incomplete = (not bio and (listeners is None or listeners == 0) and not img)
        
        if is_placeholder:
            # If placeholder has discogs_id, look up real name from Discogs
            if dc_id:
                try:
                    dc_data = await self._discogs.get_artist(dc_id)
                    real_name = dc_data.get("name")
                    if real_name:
                        return await self.enrich_and_cache_artist(real_name, existing_id=a_id, existing_slug=slug)
                except Exception:
                    logger.debug("Failed to resolve placeholder artist %s via Discogs", name)
            return await self.enrich_and_cache_artist(name, existing_id=a_id, existing_slug=slug)
        elif is_incomplete:
            return await self.enrich_and_cache_artist(name, existing_id=a_id, existing_slug=slug)
            
        # Refresh in background if older than 7 days
        if fetched:
            try:
                fetched_time = datetime.fromisoformat(fetched.replace('Z', '+00:00'))
                if fetched_time.tzinfo is None:
                    fetched_time = fetched_time.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - fetched_time > timedelta(days=7):
                    task = asyncio.create_task(self.enrich_and_cache_artist(name, existing_id=a_id, existing_slug=slug))
                    task.add_done_callback(lambda t: logger.exception("Background enrich failed") if t.exception() else None)
            except Exception:
                pass

            
        # Populate releases, top tracks, and similar artists
        releases = await self.get_artist_releases(slug)
        top_tracks = await self.get_artist_top_tracks(slug)
        similar = await self.get_similar_artists(slug)

        return ArtistDetail(
            id=a_id, name=name, slug=slug, bio=bio or "", discogs_profile=dp or "",
            discogs_id=dc_id, mbid=mb_id,
            country=country or "", begin_date=bd or "", end_date=ed or "", artist_type=atype or "",
            image_url=img or "", lastfm_listeners=listeners, lastfm_playcount=playcount,
            genres=safe_json_list(g_json),
            styles=safe_json_list(s_json),
            mb_tags=safe_json_list(mb_tags_json),
            mb_relations=safe_json_list(mb_rels_json),
            releases=releases,
            top_tracks=top_tracks,
            similar_artists=similar,
            already_in_lidarr=False
        )

    async def get_similar_artists(self, artist_slug: str) -> list[ArtistSummary]:
        """Fetch similar artists with images and listener stats."""
        async with self._db.execute("SELECT name FROM artists WHERE slug = ?", (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            artist_name = row[0] if row else artist_slug.replace('-', ' ')
            
        clean_name = _clean_artist_name(artist_name)
        try:
            similar = await self._lastfm.get_similar_artists(clean_name, limit=10)
            res = []
            for s in similar:
                s_name = s.get("name")
                if not s_name:
                    continue
                s_slug = slugify(s_name)
                s_img = ""
                images = s.get("image", [])
                if images:
                    for img_obj in reversed(images):
                        url = img_obj.get("#text", "")
                        if url and "2a96cbd8b46e442fc41c2b86b821562f" not in url:
                            s_img = url
                            break
                
                # Check DB for existing artist
                async with self._db.execute(
                    "SELECT id, image_url, lastfm_listeners, lastfm_playcount FROM artists WHERE slug = ?", (s_slug,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        res.append(ArtistSummary(
                            id=row[0], name=s_name, slug=s_slug,
                            image_url=row[1] or s_img,
                            lastfm_listeners=row[2],
                            lastfm_playcount=row[3]
                        ))
                    else:
                        res.append(ArtistSummary(
                            id=0, name=s_name, slug=s_slug, image_url=s_img,
                            lastfm_listeners=None, lastfm_playcount=None
                        ))
            return res
        except (httpx.HTTPError, ExternalAPIError):
            logger.exception("Failed to fetch similar artists for %s", artist_slug)
            return []

    async def search_artists(self, q: str) -> list[ArtistSummary]:
        """Search artists by name from DB with MusicBrainz fallback."""
        artists = []
        like_query = f"%{q}%"
        async with self._db.execute(
            f"""SELECT id, name, slug, image_url, lastfm_listeners, lastfm_playcount,
                      {_GENRES_SQL.format(alias='artists')},
                      {_STYLES_SQL.format(alias='artists')}
               FROM artists WHERE name LIKE ? AND name NOT LIKE 'Artist %'
               ORDER BY 
                  CASE WHEN image_url != '' AND image_url IS NOT NULL THEN 0 ELSE 1 END,
                  lastfm_listeners DESC 
               LIMIT 20""",
            (like_query,)
        ) as cursor:
            async for row in cursor:
                g_json, s_json = row[6], row[7]
                artists.append(ArtistSummary(
                    id=row[0], name=row[1], slug=row[2], image_url=row[3] or "",
                    lastfm_listeners=row[4], lastfm_playcount=row[5],
                    genres=safe_json_list(g_json),
                    styles=safe_json_list(s_json),
                    already_in_lidarr=False
                ))
        
        if not artists:
            try:
                mb_search = await self._musicbrainz.search_artist(q, limit=5)
                for item in mb_search:
                    name = item.get("name")
                    if name:
                        artists.append(ArtistSummary(
                            id=0, name=name, slug=slugify(name), image_url="",
                            lastfm_listeners=0, lastfm_playcount=0,
                            genres=[], styles=[], already_in_lidarr=False
                        ))
            except Exception:
                logger.exception("MusicBrainz search fallback failed for %s", q)
                
        return artists

    async def get_artist_releases(self, artist_slug: str) -> list[ReleaseDetail]:
        """Get artist releases from DB or Discogs on-demand."""
        async with self._db.execute("SELECT id FROM artists WHERE slug = ?", (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return []
            a_id = row[0]

        releases = []
        async with self._db.execute(
            """SELECT r.id, r.title, r.year, r.release_type, r.label, r.format, r.cover_url, r.genres, r.styles,
                      COALESCE(ra.role, 'primary') AS artist_role
               FROM releases r
               LEFT JOIN release_artists ra ON ra.release_id = r.id AND ra.artist_id = ?
               WHERE r.artist_id = ? OR ra.artist_id = ?
               GROUP BY r.id
               ORDER BY (artist_role = 'primary') DESC, r.year DESC
               LIMIT 1000""",
            (a_id, a_id, a_id),
        ) as cursor:
            async for row in cursor:
                role_val = row[9] if row[9] in ("primary", "secondary", "track") else "primary"
                releases.append(ReleaseDetail(
                    id=row[0], title=row[1], year=row[2], release_type=row[3] or "Release",
                    label=row[4] or "", format=row[5] or "",
                    cover_url=row[6] or "", genres=safe_json_list(row[7]), styles=safe_json_list(row[8]),
                    credits=[], artist_role=role_val,
                ))
                
        if releases:
            return releases

            
        # If no releases in DB, fetch from Discogs on demand
        async with self._db.execute("SELECT id, name, discogs_id FROM artists WHERE slug = ?", (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return []
            a_id, a_name, dc_id = row
            
        if not dc_id:
            try:
                dc_search = await self._discogs.search_artist(_clean_artist_name(a_name))
                results = dc_search.get("results", [])
                if results:
                    dc_id = results[0].get("id")
                    if dc_id:
                        await self._db.execute("UPDATE artists SET discogs_id = ? WHERE id = ?", (dc_id, a_id))
                        await self._db.commit()
            except Exception:
                pass
                
        if dc_id:
            try:
                releases_data = await self._discogs.get_artist_releases(dc_id, limit=30)
                now_iso = datetime.now(timezone.utc).isoformat()
                for rel in releases_data:
                    r_id = rel.get("id")
                    r_title = rel.get("title", "Unknown Release")
                    r_year = rel.get("year")
                    r_type = rel.get("type", "release").capitalize()
                    r_format = rel.get("format", "")
                    r_label = rel.get("label", "")
                    r_thumb = rel.get("thumb", "") or rel.get("cover_image", "")
                    r_genres = rel.get("genre", []) if isinstance(rel.get("genre"), list) else []
                    r_styles = rel.get("style", []) if isinstance(rel.get("style"), list) else []
                    
                    if r_id:
                        await self._db.execute(
                            """
                            INSERT INTO releases (
                                artist_id, discogs_id, title, year, release_type, label, format, cover_url, genres, styles, fetched_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(artist_id, discogs_id) DO UPDATE SET
                                title=excluded.title,
                                year=COALESCE(excluded.year, releases.year),
                                cover_url=CASE WHEN excluded.cover_url != '' THEN excluded.cover_url ELSE releases.cover_url END
                            """,
                            (
                                a_id, r_id, r_title, r_year, r_type, r_label, r_format,
                                r_thumb, json.dumps(r_genres), json.dumps(r_styles), now_iso
                            )
                        )
                await self._db.commit()
                
                # Re-query
                async with self._db.execute(
                    """SELECT r.id, r.title, r.year, r.release_type, r.label, r.format, r.cover_url, r.genres, r.styles
                       FROM releases r WHERE r.artist_id = ? ORDER BY r.year DESC""",
                    (a_id,)
                ) as cursor:
                    async for row in cursor:
                        releases.append(ReleaseDetail(
                            id=row[0], title=row[1], year=row[2], release_type=row[3] or "Release",
                            label=row[4] or "", format=row[5] or "",
                            cover_url=row[6] or "", genres=safe_json_list(row[7]), styles=safe_json_list(row[8]), credits=[]
                        ))
            except Exception:
                logger.exception("Failed to fetch releases for %s", a_name)
                
        return releases

    async def get_release_credits(self, release_id: int) -> list[Credit]:
        """Get credits for a release from DB."""
        credits_list = []
        async with self._db.execute(
            "SELECT id, entity_name, entity_slug, role, entity_type FROM credits WHERE release_id = ?", (release_id,)
        ) as cursor:
            async for row in cursor:
                credits_list.append(Credit(
                    id=row[0], entity_name=row[1], entity_slug=row[2], role=row[3], entity_type=row[4]
                ))
        return credits_list

    async def get_credit_entity(self, entity_slug: str) -> CreditEntity:
        """Get all releases for a producer/engineer/studio from DB."""
        name = ""
        entity_type = ""
        releases = []
        roles_set = set()
        async with self._db.execute(
            """SELECT c.entity_name, c.entity_type, c.role, r.id, r.title, r.year, r.cover_url, a.name, a.slug
               FROM credits c
               JOIN releases r ON c.release_id = r.id
               JOIN artists a ON r.artist_id = a.id
               WHERE c.entity_slug = ?""", (entity_slug,)
        ) as cursor:
            async for row in cursor:
                name = row[0]
                entity_type = row[1]
                roles_set.add(row[2])
                releases.append(ReleaseWithArtist(
                    release_id=row[3], title=row[4], year=row[5], cover_url=row[6] or "", artist_name=row[7], artist_slug=row[8], role=row[2]
                ))
        
        if not name:
            raise NotFoundError(f"Credit entity {entity_slug} not found")
            
        return CreditEntity(
            name=name, slug=entity_slug, entity_type=entity_type,
            roles=list(roles_set), release_count=len(releases), releases=releases
        )

    async def get_user_favorites(self, user_id: int) -> UserFavorites:
        """Fetch all favorites for a user, resolving entity names via JOINs."""
        artists = []
        async with self._db.execute(
            """SELECT a.name, a.slug, a.image_url, f.entity_id
               FROM favorites f JOIN artists a ON f.entity_id = a.id
               WHERE f.user_id = ? AND f.entity_type = 'artist'
               ORDER BY f.created_at DESC""", (user_id,)
        ) as cursor:
            async for row in cursor:
                artists.append(FavoriteItem(
                    entity_type="artist", entity_id=row[3],
                    name=row[0], slug=row[1], image_url=row[2] or ""
                ))

        genres = []
        async with self._db.execute(
            """SELECT g.name, g.slug, f.entity_id
               FROM favorites f JOIN genres g ON f.entity_id = g.id
               WHERE f.user_id = ? AND f.entity_type = 'genre'
               ORDER BY f.created_at DESC""", (user_id,)
        ) as cursor:
            async for row in cursor:
                genres.append(FavoriteItem(
                    entity_type="genre", entity_id=row[2],
                    name=row[0], slug=row[1]
                ))

        styles = []
        async with self._db.execute(
            """SELECT s.name, s.slug, f.entity_id
               FROM favorites f JOIN styles s ON f.entity_id = s.id
               WHERE f.user_id = ? AND f.entity_type = 'style'
               ORDER BY f.created_at DESC""", (user_id,)
        ) as cursor:
            async for row in cursor:
                styles.append(FavoriteItem(
                    entity_type="style", entity_id=row[2],
                    name=row[0], slug=row[1]
                ))

        return UserFavorites(artists=artists, genres=genres, styles=styles)

    async def add_favorite(self, user_id: int, entity_type: str, entity_id: int) -> None:
        """Add a favorite. No-op if the pair already exists (UNIQUE constraint)."""
        await self._db.execute(
            "INSERT OR IGNORE INTO favorites (user_id, entity_type, entity_id) VALUES (?, ?, ?)",
            (user_id, entity_type, entity_id)
        )
        await self._db.commit()

    async def remove_favorite(self, user_id: int, entity_type: str, entity_id: int) -> None:
        """Remove a favorite. Silent if it doesn't exist."""
        await self._db.execute(
            "DELETE FROM favorites WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
            (user_id, entity_type, entity_id)
        )
        await self._db.commit()

    async def get_artist_top_tracks(self, artist_slug: str, limit: int = 10) -> list[TrackSummary]:
        """Get top tracks with 30s playable audio previews and playcounts."""
        async with self._db.execute("SELECT name FROM artists WHERE slug = ?", (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            artist_name = row[0] if row else artist_slug.replace('-', ' ')
            
        clean_name = _clean_artist_name(artist_name)
        tracks = []
        
        try:
            top_tracks_raw = await self._lastfm.get_artist_top_tracks(clean_name, limit=limit)
            
            # Fetch Deezer 30s preview URLs in parallel
            preview_tasks = [
                _fetch_deezer_track_preview(clean_name, t.get("name", ""))
                for t in top_tracks_raw
            ]
            previews = await asyncio.gather(*preview_tasks, return_exceptions=True)
            
            for i, t in enumerate(top_tracks_raw):
                title = t.get("name", "")
                listeners = int(t.get("listeners", 0)) or None
                playcount = int(t.get("playcount", 0)) or None
                
                preview_url = None
                cover_url = ""
                if i < len(previews) and isinstance(previews[i], tuple):
                    preview_url, cover_url = previews[i]
                    
                tracks.append(TrackSummary(
                    id=i + 1,
                    title=title,
                    position=i + 1,
                    duration_ms=None,
                    lastfm_listeners=listeners,
                    lastfm_playcount=playcount,
                    preview_url=preview_url,
                    cover_url=cover_url
                ))
        except Exception:
            logger.exception("Failed to fetch top tracks for %s", artist_slug)
        
        return tracks
