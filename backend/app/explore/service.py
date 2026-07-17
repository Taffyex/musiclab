"""Business logic for the explore module."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

import aiosqlite

from app.common.exceptions import NotFoundError
from app.discogs.client import DiscogsClient
from app.explore.schemas import (
    ArtistDetail, ArtistSummary, Credit, CreditEntity, ExploreFilters,
    Genre, GenreTree, ReleaseDetail, ReleaseWithArtist, Style
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

    def _slugify(self, text: str) -> str:
        """Convert a string to a URL-friendly slug."""
        return text.lower().replace(' ', '-').replace('/', '-').replace(',', '').replace('&', 'and')

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

    async def get_artists_by_genre(self, genre_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by genre."""
        # Find genre
        async with self._db.execute("SELECT id FROM genres WHERE slug = ?", (genre_slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise NotFoundError(f"Genre {genre_slug} not found")
            genre_id = row[0]
            
        # Simplified query for cached artists
        query = """
            SELECT a.id, a.name, a.slug, a.image_url, a.lastfm_listeners, a.lastfm_playcount, a.genres, a.styles
            FROM artists a
            JOIN artist_genres ag ON a.id = ag.artist_id
            WHERE ag.genre_id = ?
        """
        order_by = "a.lastfm_listeners DESC"
        if filters.sort_by == "scrobbles":
            order_by = "a.lastfm_playcount DESC"
        elif filters.sort_by == "name":
            order_by = "a.name ASC"
            
        if filters.sort_order == "asc":
            order_by = order_by.replace("DESC", "ASC")
            
        offset = (filters.page - 1) * filters.per_page
        query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        
        artists = []
        async with self._db.execute(query, (genre_id, filters.per_page, offset)) as cursor:
            async for row in cursor:
                a_id, name, slug, image_url, listeners, playcount, g_json, s_json = row
                artists.append(ArtistSummary(
                    id=a_id, name=name, slug=slug, image_url=image_url,
                    lastfm_listeners=listeners, lastfm_playcount=playcount,
                    genres=json.loads(g_json) if g_json else [],
                    styles=json.loads(s_json) if s_json else [],
                    already_in_lidarr=False # TODO: implement lidarr check
                ))
                
        # Count
        count_query = "SELECT COUNT(*) FROM artist_genres WHERE genre_id = ?"
        async with self._db.execute(count_query, (genre_id,)) as cursor:
            total = (await cursor.fetchone())[0]
            
        return artists, total

    async def get_artists_by_style(self, style_slug: str, filters: ExploreFilters) -> tuple[list[ArtistSummary], int]:
        """Get artists by style."""
        async with self._db.execute("SELECT id FROM styles WHERE slug = ?", (style_slug,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise NotFoundError(f"Style {style_slug} not found")
            style_id = row[0]
            
        query = """
            SELECT a.id, a.name, a.slug, a.image_url, a.lastfm_listeners, a.lastfm_playcount, a.genres, a.styles
            FROM artists a
            JOIN artist_styles ast ON a.id = ast.artist_id
            WHERE ast.style_id = ?
        """
        order_by = "a.lastfm_listeners DESC"
        if filters.sort_by == "scrobbles":
            order_by = "a.lastfm_playcount DESC"
        elif filters.sort_by == "name":
            order_by = "a.name ASC"
            
        if filters.sort_order == "asc":
            order_by = order_by.replace("DESC", "ASC")
            
        offset = (filters.page - 1) * filters.per_page
        query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
        
        artists = []
        async with self._db.execute(query, (style_id, filters.per_page, offset)) as cursor:
            async for row in cursor:
                a_id, name, slug, image_url, listeners, playcount, g_json, s_json = row
                artists.append(ArtistSummary(
                    id=a_id, name=name, slug=slug, image_url=image_url,
                    lastfm_listeners=listeners, lastfm_playcount=playcount,
                    genres=json.loads(g_json) if g_json else [],
                    styles=json.loads(s_json) if s_json else [],
                    already_in_lidarr=False
                ))
                
        count_query = "SELECT COUNT(*) FROM artist_styles WHERE style_id = ?"
        async with self._db.execute(count_query, (style_id,)) as cursor:
            total = (await cursor.fetchone())[0]
            
        return artists, total

    async def enrich_and_cache_artist(self, artist_name: str) -> ArtistDetail:
        """Enrich artist from APIs and cache."""
        slug = self._slugify(artist_name)
        
        # Parallel fetch
        lf_task = asyncio.create_task(self._lastfm.get_artist_info(artist_name))
        mb_task = asyncio.create_task(self._musicbrainz.search_artist(artist_name))
        
        try:
            lf_info = await lf_task
        except Exception:
            logger.warning("Failed to fetch lastfm info for %s", artist_name)
            lf_info = {}
            
        try:
            mb_search = await mb_task
            mb_id = mb_search[0]["id"] if mb_search else None
            mb_info = await self._musicbrainz.get_artist_with_full_relations(mb_id) if mb_id else {}
        except Exception:
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
                image_url = dc_results[0].get("cover_image", "")
            else:
                dc_id = None
                image_url = ""
        except Exception:
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
                    bio=excluded.bio, lastfm_listeners=excluded.lastfm_listeners,
                    lastfm_playcount=excluded.lastfm_playcount, fetched_at=excluded.fetched_at
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
                   genres, styles, mb_tags, mb_relations, fetched_at
            FROM artists WHERE slug = ?
        """
        async with self._db.execute(query, (artist_slug,)) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            # Try to enrich using name = unslugified
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
                    id=0, name=s_name, slug=self._slugify(s_name), image_url=s_img,
                    lastfm_listeners=int(s.get("match", 0) * 1000) # mock
                ))
            return res
        except Exception:
            return []

    async def get_artist_releases(self, artist_slug: str) -> list[ReleaseDetail]:
        """Get artist releases (stub)."""
        # We would normally query the releases table, or Discogs
        # For now, return empty list
        return []

    async def get_release_credits(self, release_id: int) -> list[Credit]:
        """Get credits for a release (stub)."""
        return []

    async def get_credit_entity(self, entity_slug: str) -> CreditEntity:
        """Get all releases for a producer/engineer/studio (stub)."""
        return CreditEntity(name=entity_slug, slug=entity_slug, entity_type="person")
