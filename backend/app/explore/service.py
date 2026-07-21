"""Business logic for the explore module."""

from __future__ import annotations

import asyncio
import httpx
import json
import logging
from datetime import datetime, timedelta, timezone

import aiosqlite

from app.common.exceptions import NotFoundError, ExternalAPIError
from app.common.utils import slugify
from app.discogs.client import DiscogsClient
from app.explore.schemas import (
    ArtistDetail, ArtistSummary, Credit, CreditEntity, ExploreFilters,
    Genre, GenreTree, ReleaseDetail, ReleaseWithArtist, Style,
    FavoriteItem, UserFavorites
)
from app.lastfm.client import LastfmClient
from app.musicbrainz.client import MusicBrainzClient

logger = logging.getLogger(__name__)

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

        column = {"listeners": "a.lastfm_listeners", "scrobbles": "a.lastfm_playcount", "name": "a.name"}.get(filters.sort_by, "a.lastfm_listeners")
        direction = "ASC" if filters.sort_order == "asc" else "DESC"

        query = f"""
            SELECT a.id, a.name, a.slug, a.image_url, a.lastfm_listeners, a.lastfm_playcount,
                   (SELECT json_group_array(g.name) FROM genres g JOIN artist_genres ag ON ag.genre_id = g.id WHERE ag.artist_id = a.id) as genres,
                   (SELECT json_group_array(s.name) FROM styles s JOIN artist_styles ast ON ast.style_id = s.id WHERE ast.artist_id = a.id) as styles
            FROM artists a
            JOIN {join_table} j ON a.id = j.artist_id
            WHERE j.{join_col} = ?
            ORDER BY {column} {direction}
            LIMIT ? OFFSET ?
        """
        offset = (filters.page - 1) * filters.per_page

        artists = []
        async with self._db.execute(query, (taxonomy_id, filters.per_page, offset)) as cursor:
            async for row in cursor:
                a_id, name, art_slug, image_url, listeners, playcount, g_json, s_json = row
                artists.append(ArtistSummary(
                    id=a_id, name=name, slug=art_slug, image_url=image_url,
                    lastfm_listeners=listeners, lastfm_playcount=playcount,
                    genres=json.loads(g_json) if g_json else [],
                    styles=json.loads(s_json) if s_json else [],
                    already_in_lidarr=False,
                ))

        async with self._db.execute(f"SELECT COUNT(*) FROM {join_table} WHERE {join_col} = ?", (taxonomy_id,)) as cursor:
            total = (await cursor.fetchone())[0]

        return artists, total

    async def get_artists_by_genre(self, genre_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by genre."""
        return await self._get_artists_by_taxonomy(genre_slug, filters, is_style=False)

    async def get_artists_by_style(self, style_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by style."""
        return await self._get_artists_by_taxonomy(style_slug, filters, is_style=True)

    async def enrich_and_cache_artist(self, artist_name: str) -> ArtistDetail:
        """Enrich artist from APIs and cache."""
        slug = slugify(artist_name)
        
        # Parallel fetch
        lf_task = asyncio.create_task(self._lastfm.get_artist_info(artist_name))
        mb_task = asyncio.create_task(self._musicbrainz.search_artist(artist_name))
        
        try:
            lf_info = await lf_task
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch lastfm info for %s", artist_name)
            lf_info = {}
        try:
            mb_search = await mb_task
            mb_id = mb_search[0].get("id") if mb_search else None
            mb_info = await self._musicbrainz.get_artist_with_full_relations(mb_id) if mb_id else {}
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch mb info for %s", artist_name)
            mb_info = {}
            mb_id = None
            
        bio = lf_info.get("bio", {}).get("summary", "")
        listeners = int(lf_info.get("stats", {}).get("listeners", 0))
        playcount = int(lf_info.get("stats", {}).get("playcount", 0))
        
        country = mb_info.get("country", "")
        begin_date = mb_info.get("life-span", {}).get("begin", "")
        end_date = mb_info.get("life-span", {}).get("end", "")
        artist_type = mb_info.get("type", "")
        
        mb_tags = [t.get("name") for t in mb_info.get("tags", [])]
        mb_relations = mb_info.get("relations", [])
        
        # Discogs search to get id and image
        try:
            dc_search = await self._discogs.search_artist(artist_name)
            dc_results = dc_search.get("results", [])
            if dc_results:
                dc_id = dc_results[0].get("id")
                # Sometimes cover_image is there, sometimes we need to fetch artist
                image_url = dc_results[0].get("cover_image", "")
                if not image_url and dc_id:
                    artist_data = await self._discogs.get_artist(dc_id)
                    images = artist_data.get("images", [])
                    if images:
                        image_url = images[0].get("resource_url", "")
            else:
                dc_id = None
                image_url = ""
        except (httpx.HTTPError, ExternalAPIError):
            logger.warning("Failed to fetch discogs info for %s", artist_name)
            dc_id = None
            image_url = ""
            
        # Insert
        try:
            await self._db.execute(
                """
                INSERT INTO artists (
                    name, slug, discogs_id, mbid, bio, country, begin_date, end_date,
                    artist_type, image_url, lastfm_listeners, lastfm_playcount,
                    mb_tags, mb_relations, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    discogs_id=excluded.discogs_id,
                    mbid=excluded.mbid,
                    bio=excluded.bio,
                    country=excluded.country,
                    begin_date=excluded.begin_date,
                    end_date=excluded.end_date,
                    artist_type=excluded.artist_type,
                    image_url=excluded.image_url,
                    lastfm_listeners=excluded.lastfm_listeners,
                    lastfm_playcount=excluded.lastfm_playcount,
                    mb_tags=excluded.mb_tags,
                    mb_relations=excluded.mb_relations,
                    fetched_at=excluded.fetched_at
                """,
                (
                    artist_name, slug, dc_id, mb_id, bio, country, begin_date, end_date,
                    artist_type, image_url, listeners, playcount,
                    json.dumps(mb_tags), json.dumps(mb_relations), datetime.now(timezone.utc).isoformat()
                )
            )
            await self._db.commit()
        except Exception:
            logger.exception("Failed to insert enriched artist: %s", artist_name)
            
        async with self._db.execute("SELECT id FROM artists WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise NotFoundError(f"Artist {artist_name} could not be cached.")
            artist_id = row[0]
            
        return ArtistDetail(
            id=artist_id, name=artist_name, slug=slug, bio=bio,
            country=country, begin_date=begin_date, end_date=end_date,
            artist_type=artist_type, image_url=image_url,
            lastfm_listeners=listeners, lastfm_playcount=playcount,
            mb_tags=mb_tags, mb_relations=mb_relations
        )

    async def get_artist_detail(self, artist_slug: str) -> ArtistDetail:
        """Get full artist profile."""
        query = """
            SELECT id, name, slug, bio, discogs_profile, country, begin_date, end_date,
                   artist_type, image_url, lastfm_listeners, lastfm_playcount,
                   (SELECT json_group_array(g.name) FROM genres g JOIN artist_genres ag ON ag.genre_id = g.id WHERE ag.artist_id = artists.id) as genres,
                   (SELECT json_group_array(s.name) FROM styles s JOIN artist_styles ast ON ast.style_id = s.id WHERE ast.artist_id = artists.id) as styles,
                   mb_tags, mb_relations, fetched_at
            FROM artists WHERE slug = ?
        """
        async with self._db.execute(query, (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            # Try to enrich using name if we can reverse slug, but we don't know the exact name.
            # Best effort: use title cased space-separated slug.
            name = artist_slug.replace('-', ' ').title()
            return await self.enrich_and_cache_artist(name)
            
        a_id, name, slug, bio, dp, country, bd, ed, atype, img, listeners, playcount, g_json, s_json, mb_tags_json, mb_rels_json, fetched = row
        
        fetched_time = datetime.fromisoformat(fetched.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - fetched_time > timedelta(days=1):
            # Refresh async
            asyncio.create_task(self.enrich_and_cache_artist(name))
            
        return ArtistDetail(
            id=a_id, name=name, slug=slug, bio=bio, discogs_profile=dp,
            country=country, begin_date=bd, end_date=ed, artist_type=atype,
            image_url=img, lastfm_listeners=listeners, lastfm_playcount=playcount,
            genres=json.loads(g_json) if g_json else [],
            styles=json.loads(s_json) if s_json else [],
            mb_tags=json.loads(mb_tags_json) if mb_tags_json else [],
            mb_relations=json.loads(mb_rels_json) if mb_rels_json else [],
            already_in_lidarr=False
        )

    async def get_similar_artists(self, artist_slug: str) -> list[ArtistSummary]:
        """Get similar artists (stub)."""
        name = artist_slug.replace('-', ' ')
        try:
            similar = await self._lastfm.get_similar_artists(name, limit=10)
            res = []
            for s in similar:
                s_name = s.get("name")
                s_img = ""
                images = s.get("image", [])
                if images:
                    s_img = images[-1].get("#text", "")
                res.append(ArtistSummary(
                    id=0, name=s_name, slug=slugify(s_name), image_url=s_img,
                    lastfm_listeners=int(s.get("match", 0) * 1000) # mock
                ))
            return res
        except Exception:
            return []

    async def search_artists(self, q: str) -> list[ArtistSummary]:
        """Search artists by name from DB."""
        artists = []
        like_query = f"%{q}%"
        async with self._db.execute(
            """SELECT id, name, slug, image_url, lastfm_listeners, lastfm_playcount,
                      (SELECT json_group_array(g.name) FROM genres g JOIN artist_genres ag ON ag.genre_id = g.id WHERE ag.artist_id = artists.id) as genres,
                      (SELECT json_group_array(s.name) FROM styles s JOIN artist_styles ast ON ast.style_id = s.id WHERE ast.artist_id = artists.id) as styles
               FROM artists WHERE name LIKE ? ORDER BY lastfm_listeners DESC LIMIT 20""",
            (like_query,)
        ) as cursor:
            async for row in cursor:
                g_json, s_json = row[6], row[7]
                artists.append(ArtistSummary(
                    id=row[0], name=row[1], slug=row[2], image_url=row[3],
                    lastfm_listeners=row[4], lastfm_playcount=row[5],
                    genres=json.loads(g_json) if g_json else [],
                    styles=json.loads(s_json) if s_json else [],
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
                pass
                
        return artists

    async def get_artist_releases(self, artist_slug: str) -> list[ReleaseDetail]:
        """Get artist releases from DB."""
        releases = []
        async with self._db.execute(
            """SELECT r.id, r.title, r.year, r.release_type, r.label, r.format, r.cover_url, r.genres, r.styles
               FROM releases r JOIN artists a ON r.artist_id = a.id
               WHERE a.slug = ? ORDER BY r.year DESC""",
            (artist_slug,)
        ) as cursor:
            async for row in cursor:
                releases.append(ReleaseDetail(
                    id=row[0], title=row[1], year=row[2], release_type=row[3], label=row[4], format=row[5],
                    cover_url=row[6] or "", genres=json.loads(row[7]) if row[7] else [], styles=json.loads(row[8]) if row[8] else [], credits=[]
                ))
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
