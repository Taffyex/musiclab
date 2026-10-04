"""MusicLab Discogs XML dump importer (fast full-info import).

Strategy: 3 passes over the dumps.
  Pass 1: stream releases dump (minimal fields), detect master mains,
      count releases per artist (at most once per release), accumulate
      style-to-genre co-occurrence matrix, keep artists with >= --min-releases.
  Pass 2: stream artists dump, import qualifying artist profiles with cleaned
      names and markdown bio cleanup; resolve slug collisions by prominence.
  Pass 3: stream releases dump again, import canonical releases with full info:
      deduplicated master handling, release types (Album, Single, EP, Compilation,
      Soundtrack), sequential track positions, track & release credits,
      multi-artist links via release_artists, genre/style taxonomy.
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import json
import logging
import os
import re
import sqlite3
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Dict, Iterator, List, Optional, Set, Tuple

from lxml import etree

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_DISAMBIGUATION_RE = re.compile(r"\s*\(\d+\)$")
_TRACK_POS_DIGITS_RE = re.compile(r"(\d+)")
_BBCODE_TAG_RE = re.compile(r"\[/?(?:b|i|u|strong|em)\]", re.IGNORECASE)
_BBCODE_NAMED_RE = re.compile(r"\[(?:a|l|r|m)=([^\]]+)\]", re.IGNORECASE)
_BBCODE_NUM_RE = re.compile(r"\[[alrm]\d+\]", re.IGNORECASE)
_BBCODE_URL_RE = re.compile(r"\[url=([^\]]+)\](.*?)\[/url\]", re.IGNORECASE)
_BBCODE_URL_RAW_RE = re.compile(r"\[url\](.*?)\[/url\]", re.IGNORECASE)

JUNK_ARTIST_NAMES = {"unknown artist", "no artist", "anonymous", "none", "unknown"}
COMPILATION_ARTIST_NAMES = {"various", "various artists", "soundtrack", "original soundtrack"}
STUDIO_ROLE_HINTS = ("studio", "recorded at", "mastered at", "mixed at")

BULK_INDEXES = [
    "idx_artists_slug", "idx_releases_artist", "idx_tracks_release",
    "idx_credits_entity_slug", "idx_credits_role", "idx_credits_discogs",
    "idx_artist_genres_genre", "idx_artist_styles_style",
    "idx_release_artists_artist", "idx_release_artists_release",
    "idx_releases_discogs", "idx_artists_discogs",
]

INDEX_DDL = {
    "idx_artists_slug": "CREATE INDEX IF NOT EXISTS idx_artists_slug ON artists(slug)",
    "idx_artists_discogs": "CREATE INDEX IF NOT EXISTS idx_artists_discogs ON artists(discogs_id)",
    "idx_releases_artist": "CREATE INDEX IF NOT EXISTS idx_releases_artist ON releases(artist_id)",
    "idx_releases_discogs": "CREATE INDEX IF NOT EXISTS idx_releases_discogs ON releases(discogs_id)",
    "idx_tracks_release": "CREATE INDEX IF NOT EXISTS idx_tracks_release ON tracks(release_id)",
    "idx_credits_entity_slug": "CREATE INDEX IF NOT EXISTS idx_credits_entity_slug ON credits(entity_slug)",
    "idx_credits_role": "CREATE INDEX IF NOT EXISTS idx_credits_role ON credits(role)",
    "idx_credits_discogs": "CREATE INDEX IF NOT EXISTS idx_credits_discogs ON credits(discogs_id)",
    "idx_artist_genres_genre": "CREATE INDEX IF NOT EXISTS idx_artist_genres_genre ON artist_genres(genre_id)",
    "idx_artist_styles_style": "CREATE INDEX IF NOT EXISTS idx_artist_styles_style ON artist_styles(style_id)",
    "idx_release_artists_artist": "CREATE INDEX IF NOT EXISTS idx_release_artists_artist ON release_artists(artist_id)",
    "idx_release_artists_release": "CREATE INDEX IF NOT EXISTS idx_release_artists_release ON release_artists(release_id)",
}


@dataclasses.dataclass
class ImportConfig:
    artists_path: str
    releases_path: str
    db_path: str
    min_releases: int = 2
    require_genre: bool = True
    batch_size: int = 10000
    limit: int = 0
    artists_limit: int = 0
    qualifiers_cache: str = ""
    skip_pass1: bool = False
    no_finalize: bool = False
    fresh: bool = False


@dataclasses.dataclass
class ImportStats:
    pass1_scanned: int = 0
    pass1_canonical: int = 0
    qualifying_artists: int = 0
    artists_imported: int = 0
    releases_imported: int = 0
    tracks_imported: int = 0
    credits_imported: int = 0
    links_imported: int = 0
    total_seconds: float = 0.0


@lru_cache(maxsize=65536)
def slugify(text: str) -> str:
    """Cached URL-friendly slug."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")


@lru_cache(maxsize=65536)
def clean_artist_name(name: str) -> str:
    """Strip Discogs disambiguation numbers (cached), handling repeated suffixes."""
    if not name:
        return ""
    while _DISAMBIGUATION_RE.search(name):
        name = _DISAMBIGUATION_RE.sub("", name).strip()
    return name


def clean_bio_markup(text: str) -> str:
    """Clean Discogs bbcode tags into readable text."""
    if not text:
        return ""
    s = _BBCODE_TAG_RE.sub("", text)
    s = _BBCODE_NAMED_RE.sub(r"\1", s)
    s = _BBCODE_NUM_RE.sub("", s)
    s = _BBCODE_URL_RE.sub(r"\2 (\1)", s)
    s = _BBCODE_URL_RAW_RE.sub(r"\1", s)
    return s.strip()


@lru_cache(maxsize=8192)
def cached_genre_json(genres: tuple[str, ...]) -> str:
    """Serialize a genre tuple once per distinct combo (cached)."""
    return json.dumps(list(genres))


@lru_cache(maxsize=8192)
def cached_style_json(styles: tuple[str, ...]) -> str:
    """Serialize a style tuple once per distinct combo (cached)."""
    return json.dumps(list(styles))


@lru_cache(maxsize=65536)
def parse_duration_ms(duration_str: str) -> Optional[int]:
    """Convert '3:45' duration strings to milliseconds (cached)."""
    if not duration_str:
        return None
    try:
        parts = duration_str.strip().split(":")
        if len(parts) == 2:
            minutes, seconds = int(parts[0]), int(parts[1])
            return (minutes * 60 + seconds) * 1000
        elif len(parts) == 3:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return (hours * 3600 + minutes * 60 + seconds) * 1000
    except (ValueError, TypeError):
        pass
    return None


def get_db(db_path: str, bulk: bool = False) -> sqlite3.Connection:
    """Open SQLite connection, optionally tuned for bulk import."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if bulk:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-256000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA locking_mode=EXCLUSIVE")
        conn.execute("PRAGMA foreign_keys=OFF")
    return conn


def _child_text(elem, tag: str) -> str:
    child = elem.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text


def canonical_master(elem) -> tuple[Optional[int], bool]:
    """Shared master-canonicalization: returns (master_id, is_main)."""
    master_elem = elem.find("master_id")
    if master_elem is None or not master_elem.text:
        return (None, False)
    try:
        return (int(master_elem.text), master_elem.get("is_main_release") == "true")
    except (ValueError, TypeError):
        return (None, False)


def is_eligible(elem, require_genre: bool) -> bool:
    """Shared eligibility rule for Pass 1 and Pass 3."""
    status = elem.get("status")
    if status not in (None, "", "Accepted"):
        return False
    if require_genre and elem.find("genres/genre") is None:
        return False
    return True


def fast_iter(file_path: str, tag: str, limit: int = 0) -> Iterator[Tuple[etree._Element, float]]:
    """lxml streaming iterator yielding (element, progress_ratio)."""
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 1
    is_gz = file_path.endswith(".gz")

    raw_f = open(file_path, "rb")
    stream = gzip.GzipFile(fileobj=raw_f) if is_gz else raw_f

    try:
        context = etree.iterparse(stream, events=("end",), tag=tag, huge_tree=True)
        yielded = 0
        for _, elem in context:
            offset = raw_f.tell()
            ratio = min(offset / max(file_size, 1), 1.0)
            yield elem, ratio
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
            yielded += 1
            if limit and yielded >= limit:
                break
        del context
    finally:
        if is_gz:
            stream.close()
        raw_f.close()


def ensure_schema(db: sqlite3.Connection, schema_path: str) -> None:
    """Create base tables from schema.sql + release_artists (idempotent)."""
    if os.path.exists(schema_path):
        with open(schema_path, encoding="utf-8") as f:
            db.executescript(f.read())
    else:
        logger.warning("schema.sql not found at %s; creating minimal tables", schema_path)

    db.execute(
        """CREATE TABLE IF NOT EXISTS release_artists (
            release_id INTEGER NOT NULL, artist_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'primary',
            PRIMARY KEY (release_id, artist_id, role))"""
    )
    db.commit()

    for ddl in (
        "ALTER TABLE releases ADD COLUMN master_id INTEGER",
        "ALTER TABLE releases ADD COLUMN is_main_release BOOLEAN DEFAULT 0",
        "ALTER TABLE releases ADD COLUMN country TEXT DEFAULT ''",
    ):
        try:
            db.execute(ddl)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
    db.commit()


def ensure_special_artists(db: sqlite3.Connection) -> int:
    """Ensure synthetic Various Artists entry (id=-1); return its DB id."""
    cur = db.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO artists (id, name, slug, discogs_id, bio)
           VALUES (-1, 'Various Artists', 'various-artists', -1,
                   'Compilations, Soundtracks, and Video Game OSTs.')"""
    )
    db.commit()
    cur.execute("SELECT id FROM artists WHERE discogs_id = -1")
    row = cur.fetchone()
    return int(row["id"]) if row else -1


def drop_bulk_indexes(db: sqlite3.Connection) -> None:
    """Drop hot-path indexes before import; recreated in finalize."""
    for name in BULK_INDEXES:
        db.execute(f"DROP INDEX IF EXISTS {name}")
    db.commit()


def finalize_db(db: sqlite3.Connection, marker_info: Optional[dict] = None) -> None:
    """Recreate indexes, ANALYZE, foreign_key_check, integrity check, WAL checkpoint."""
    logger.info("Rebuilding indexes...")
    for _name, ddl in INDEX_DDL.items():
        db.execute(ddl)
    db.commit()

    logger.info("Running ANALYZE...")
    db.execute("ANALYZE")
    db.commit()

    db.execute("PRAGMA foreign_keys=ON")
    fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        logger.error("Foreign key check failed with %d violations! First few: %s", len(fk_errors), fk_errors[:5])
        raise RuntimeError(f"Database foreign key violations: {len(fk_errors)}")
    else:
        logger.info("Foreign key check: OK (0 violations)")

    row = db.execute("PRAGMA integrity_check").fetchone()
    logger.info("Integrity check: %s", row[0] if row else "unknown")
    if not row or row[0] != "ok":
        raise RuntimeError(f"Integrity check failed: {row}")

    if marker_info:
        db.execute(
            """INSERT OR REPLACE INTO cache_entries (key, value, expires_at)
               VALUES ('import:discogs_dump', ?, '9999-12-31T23:59:59')""",
            (json.dumps(marker_info),)
        )
        db.commit()

    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA locking_mode=NORMAL")
    db.execute("SELECT 1")
    db.commit()


def pass1_count_releases(
    releases_path: str, min_releases: int, require_genre: bool, limit: int
) -> Tuple[Set[int], Set[int], Dict[str, str], dict]:
    """Pass 1: scan releases; returns (qualifying_ids, mains_set, style_to_genre, stats)."""
    logger.info("Pass 1: scanning releases (minimal fields & mains detection)...")
    t0 = time.monotonic()
    counts: Dict[int, int] = {}
    mains: Set[int] = set()
    style_genre_counts: Dict[str, Counter[str]] = defaultdict(Counter)

    n = 0
    canonical = 0
    sk_ineligible = 0

    for elem, ratio in fast_iter(releases_path, "release", limit=limit):
        n += 1
        if n % 100000 == 0:
            dt = time.monotonic() - t0
            rate = n / max(dt, 0.1)
            pct = ratio * 100.0
            eta_s = (1.0 - ratio) / max(ratio, 0.0001) * dt if ratio > 0.01 else 0
            logger.info("Pass 1: %d releases (%.1f%%, %.0f rel/s, ETA %.0fm)...", n, pct, rate, eta_s / 60)

        if not is_eligible(elem, require_genre):
            sk_ineligible += 1
            continue

        mid, is_main = canonical_master(elem)
        if mid is not None and is_main:
            mains.add(mid)

        canonical += 1

        genres = [g.text.strip() for g in elem.findall("genres/genre") if g.text]
        styles = [s.text.strip() for s in elem.findall("styles/style") if s.text]
        if genres and styles:
            for s in styles:
                for g in genres:
                    style_genre_counts[s][g] += 1

        rel_artists: Set[int] = set()

        artists_el = elem.find("artists")
        if artists_el is not None:
            for a in artists_el.findall("artist"):
                aid_text = a.findtext("id")
                if not aid_text:
                    continue
                nm = a.findtext("name")
                if nm:
                    ln = nm.strip().lower()
                    if ln in JUNK_ARTIST_NAMES or (ln.startswith("[") and ln.endswith("]")):
                        continue
                try:
                    aid = int(aid_text)
                    if aid != 194:
                        rel_artists.add(aid)
                except ValueError:
                    continue

        for ea_group in elem.findall("extraartists"):
            for ea in ea_group.findall("artist"):
                aid_text = ea.findtext("id")
                if not aid_text:
                    continue
                try:
                    aid = int(aid_text)
                    if aid != 194:
                        rel_artists.add(aid)
                except ValueError:
                    continue

        tracklist_el = elem.find("tracklist")
        if tracklist_el is not None:
            for trk in tracklist_el.findall("track"):
                trk_artists = trk.find("artists")
                if trk_artists is not None:
                    for ta in trk_artists.findall("artist"):
                        aid_text = ta.findtext("id")
                        if aid_text:
                            try:
                                aid = int(aid_text)
                                if aid != 194:
                                    rel_artists.add(aid)
                            except ValueError:
                                pass

        for aid in rel_artists:
            counts[aid] = counts.get(aid, 0) + 1

    qual = {aid for aid, c in counts.items() if c >= min_releases}

    style_to_genre: Dict[str, str] = {}
    for style, g_counts in style_genre_counts.items():
        if g_counts:
            best_genre = g_counts.most_common(1)[0][0]
            style_to_genre[style] = best_genre

    dt = time.monotonic() - t0
    stats = {
        "scanned": n,
        "canonical": canonical,
        "skipped_ineligible": sk_ineligible,
        "mains_count": len(mains),
        "qualifying_count": len(qual),
        "seconds": round(dt, 1),
        "per_second": round(n / max(dt, 0.1), 1),
    }
    logger.info("Pass 1 done: %d scanned -> %d qualifying artists, %d main masters in %.1fs.",
                n, len(qual), len(mains), dt)
    return qual, mains, style_to_genre, stats


def pass2_import_artists(
    artists_path: str,
    db: sqlite3.Connection,
    qual: Set[int],
    batch_size: int,
    limit: int,
    pass1_counts: Optional[Dict[int, int]] = None,
) -> int:
    """Pass 2: import qualifying artist profiles with temporary slugs, then resolve slugs."""
    logger.info("Pass 2: importing artist profiles...")
    t0 = time.monotonic()
    n = 0
    imported = 0
    batch: List[tuple] = []

    for elem, ratio in fast_iter(artists_path, "artist", limit=limit):
        n += 1
        if n % 100000 == 0:
            dt = time.monotonic() - t0
            logger.info("Pass 2: %d artists scanned (%.1f%%, %d imported)...", n, ratio * 100.0, imported)

        aid_text = elem.findtext("id")
        if not aid_text:
            continue
        try:
            aid = int(aid_text)
        except ValueError:
            continue

        if aid not in qual or aid == 194:
            continue

        raw_name = _child_text(elem, "name").strip()
        if not raw_name:
            continue
        clean_name = clean_artist_name(raw_name)
        if not clean_name or clean_name.lower() in JUNK_ARTIST_NAMES:
            continue
        if clean_name.startswith("[") and clean_name.endswith("]"):
            continue

        raw_bio = _child_text(elem, "profile").strip()
        clean_bio = clean_bio_markup(raw_bio)

        img = ""
        images = elem.find("images")
        if images is not None:
            first = images.find("image")
            if first is not None:
                img = first.get("uri", "") or first.get("uri150", "") or ""

        temp_slug = f"~tmp~{aid}"
        batch.append((clean_name, temp_slug, aid, clean_bio, raw_bio, img))
        imported += 1

        if len(batch) >= batch_size:
            db.executemany(
                """INSERT OR IGNORE INTO artists (name, slug, discogs_id, bio, discogs_profile, image_url)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                batch,
            )
            db.commit()
            batch = []

    if batch:
        db.executemany(
            """INSERT OR IGNORE INTO artists (name, slug, discogs_id, bio, discogs_profile, image_url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            batch,
        )
        db.commit()

    logger.info("Pass 2: imported %d profiles. Resolving slugs...", imported)
    _resolve_artist_slugs(db, pass1_counts or {})

    dt = time.monotonic() - t0
    logger.info("Pass 2 done: %d artist profiles finalized in %.1fs.", imported, dt)
    return imported


def _resolve_artist_slugs(db: sqlite3.Connection, pass1_counts: Dict[int, int]) -> None:
    """Resolve temporary artist slugs into unique, prominence-sorted URL slugs."""
    cur = db.cursor()
    cur.execute("SELECT id, name, discogs_id FROM artists WHERE slug LIKE '~tmp~%'")
    rows = cur.fetchall()
    if not rows:
        return

    slug_groups: Dict[str, List[Tuple[int, str, int, int]]] = defaultdict(list)
    for r in rows:
        a_id = int(r["id"])
        name = str(r["name"])
        discogs_id = int(r["discogs_id"])
        cnt = pass1_counts.get(discogs_id, 0)
        base = slugify(name) or f"artist-{discogs_id}"
        if base == "various-artists":
            base = f"artist-{discogs_id}"
        slug_groups[base].append((a_id, name, discogs_id, cnt))

    cur.execute("SELECT slug FROM artists WHERE slug NOT LIKE '~tmp~%'")
    existing_slugs: Set[str] = {r[0] for r in cur.fetchall()}

    slug_updates: List[Tuple[str, int]] = []
    for base, candidates in slug_groups.items():
        candidates.sort(key=lambda x: (-x[3], x[2]))
        for idx, (a_id, _name, discogs_id, _cnt) in enumerate(candidates):
            if idx == 0 and base not in existing_slugs:
                final_slug = base
            else:
                final_slug = f"{base}-{discogs_id}"
                counter = 2
                while final_slug in existing_slugs:
                    final_slug = f"{base}-{discogs_id}-{counter}"
                    counter += 1
            existing_slugs.add(final_slug)
            slug_updates.append((final_slug, a_id))

    cur.executemany("UPDATE artists SET slug = ? WHERE id = ?", slug_updates)
    db.commit()
    logger.info("Resolved slugs for %d artists.", len(slug_updates))


def setup_taxonomy(
    db: sqlite3.Connection, style_to_genre: Dict[str, str]
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Insert genres and styles using argmax parentage; returns (gid_cache, sid_cache)."""
    cur = db.cursor()

    # Seed canonical genres and styles from genre_seed.json if available
    seed_path = os.path.join(os.path.dirname(__file__), "..", "app", "explore", "genre_seed.json")
    canonical_style_map: Dict[str, str] = {}
    if os.path.exists(seed_path):
        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_data = json.load(f)
            for g_item in seed_data.get("genres", []):
                g_name = g_item.get("name")
                for s_name in g_item.get("styles", []):
                    canonical_style_map[s_name] = g_name
        except Exception as e:
            logger.warning("Could not read genre_seed.json: %s", e)

    all_genres = sorted(
        {g for g in style_to_genre.values() if g}
        | set(canonical_style_map.values())
        | {"Electronic", "Rock", "Pop", "Hip Hop", "Jazz", "Funk / Soul", "Classical"}
    )
    for g in all_genres:
        slug = slugify(g)
        if slug:
            cur.execute("INSERT OR IGNORE INTO genres (name, slug, source) VALUES (?, ?, 'discogs')", (g, slug))

    db.commit()

    cur.execute("SELECT id, name FROM genres")
    gid_cache = {row["name"]: int(row["id"]) for row in cur.fetchall()}

    # Merge canonical mapping with data-driven argmax mapping
    final_style_to_genre = dict(style_to_genre)
    final_style_to_genre.update(canonical_style_map)

    default_gid = gid_cache.get("Electronic", 1)
    for style, genre in final_style_to_genre.items():
        gid = gid_cache.get(genre, default_gid)
        s_slug = slugify(style)
        if s_slug:
            cur.execute(
                "INSERT OR IGNORE INTO styles (name, slug, genre_id, source) VALUES (?, ?, ?, 'discogs')",
                (style, s_slug, gid),
            )


    db.commit()

    cur.execute("SELECT id, name FROM styles")
    sid_cache = {row["name"]: int(row["id"]) for row in cur.fetchall()}
    logger.info("Taxonomy initialized: %d genres, %d styles.", len(gid_cache), len(sid_cache))
    return gid_cache, sid_cache


def _release_type(
    descriptions: Set[str], genres_lower: List[str], styles_lower: List[str],
    is_various: bool, track_count: int
) -> str:
    """Accurately classify release_type based on formats, descriptions, and tracks."""
    if (
        "soundtrack" in descriptions
        or "score" in descriptions
        or "soundtrack" in styles_lower
        or "score" in styles_lower
        or "stage & screen" in genres_lower
    ):
        return "Soundtrack"

    if "compilation" in descriptions or is_various or "compilation" in styles_lower:
        return "Compilation"

    if "single" in descriptions or "maxi-single" in descriptions:
        return "Single"

    if "ep" in descriptions or "mini-album" in descriptions:
        return "EP"

    if "album" in descriptions or "lp" in descriptions:
        return "Album"

    if track_count > 0:
        if track_count <= 3:
            return "Single"
        elif track_count <= 6:
            return "EP"

    return "Album"


def _release_meta(elem) -> Tuple[str, str, str, str, Set[str]]:
    """Extract country, label, format string, cover URL, and format descriptions."""
    country = _child_text(elem, "country").strip()

    labels_el = elem.find("labels")
    lab = ""
    if labels_el is not None:
        for lb in labels_el.findall("label"):
            if lb.get("name"):
                lab = lb.get("name")
                break

    descriptions: Set[str] = set()
    fmts: List[str] = []
    fmts_el = elem.find("formats")
    if fmts_el is not None:
        for fm in fmts_el.findall("format"):
            fn = fm.get("name", "").strip()
            if fn:
                fmts.append(fn)
            for d in fm.findall("descriptions/description"):
                if d.text:
                    descriptions.add(d.text.strip().lower())

    fmt = ", ".join(fmts)

    cover = ""
    imgs_el = elem.find("images")
    if imgs_el is not None:
        fi = imgs_el.find("image")
        if fi is not None:
            cover = fi.get("uri", "") or ""

    return country, lab, fmt, cover, descriptions


def _collect_tracks_and_credits(
    elem, rid: int, track_batch: list, credit_batch: list, slug_by_aid: Dict[int, str]
) -> Tuple[int, List[Tuple[int, str]]]:
    """Collect tracks with sequential positions (1..N) and extra artists credits."""
    track_el = elem.find("tracklist")
    track_aids: List[Tuple[int, str]] = []
    added_tracks = 0

    if track_el is not None:
        pos = 1
        for t in track_el.findall("track"):
            tt = (t.findtext("title") or "").strip()
            tp = (t.findtext("position") or "").strip()
            dur = (t.findtext("duration") or "").strip()
            has_sub = t.find("sub_tracks") is not None

            if not tp and not dur and not has_sub:
                continue


            dur_ms = parse_duration_ms(dur)
            track_batch.append((rid, tt or f"Track {pos}", pos, dur_ms))
            pos += 1
            added_tracks += 1

            ta_el = t.find("artists")
            if ta_el is not None:
                for ta in ta_el.findall("artist"):
                    tat = ta.findtext("id")
                    if tat:
                        try:
                            track_aids.append((int(tat), "track"))
                        except ValueError:
                            pass

            for ea in t.findall("extraartists/artist"):
                _append_credit(ea, rid, credit_batch, slug_by_aid)

            sub = t.find("sub_tracks")
            if sub is not None:
                for st in sub.findall("track"):
                    st_artists = st.find("artists")
                    if st_artists is not None:
                        for sta in st_artists.findall("artist"):
                            stat = sta.findtext("id")
                            if stat:
                                try:
                                    track_aids.append((int(stat), "track"))
                                except ValueError:
                                    pass
                    for stea in st.findall("extraartists/artist"):
                        _append_credit(stea, rid, credit_batch, slug_by_aid)

    for ea in elem.findall("extraartists/artist"):
        _append_credit(ea, rid, credit_batch, slug_by_aid)

    return added_tracks, track_aids


def _append_credit(
    ea_el, rid: int, credit_batch: list, slug_by_aid: Dict[int, str]
) -> None:
    en = (ea_el.findtext("name") or "").strip()
    er = (ea_el.findtext("role") or "").strip()
    if not en or not er:
        return

    clean_en = clean_artist_name(en)
    eid = None
    es = ea_el.findtext("id")
    if es:
        try:
            eid = int(es)
        except ValueError:
            pass

    if eid is not None and eid in slug_by_aid:
        eslug = slug_by_aid[eid]
    else:
        eslug = slugify(clean_en)
        if eid is not None:
            eslug = f"{eslug}-{eid}"

    if not eslug:
        return

    rl = er.lower()
    et = "studio" if any(h in rl for h in STUDIO_ROLE_HINTS) else "person"
    credit_batch.append((rid, clean_en, eslug, er, et, eid))


def _commit_batch(
    db: sqlite3.Connection,
    rel_batch: list,
    credit_batch: list,
    track_batch: list,
    link_batch: list,
    ag_set: set,
    as_set: set,
    gid_cache: Dict[str, int],
    sid_cache: Dict[str, int],
) -> None:
    """Flush one batch of releases, tracks, credits, links, and genre/style associations."""
    if not rel_batch:
        return

    cur = db.cursor()
    cur.executemany(
        """INSERT OR IGNORE INTO releases (artist_id, discogs_id, master_id, is_main_release,
            title, year, country, release_type, label, format, cover_url, genres, styles)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rel_batch,
    )

    ids = sorted({r[1] for r in rel_batch})
    rmap: Dict[int, int] = {}
    for i in range(0, len(ids), 900):
        chunk = ids[i : i + 900]
        ph = ",".join("?" for _ in chunk)
        cur.execute(f"SELECT discogs_id, id FROM releases WHERE discogs_id IN ({ph})", chunk)
        for row in cur.fetchall():
            rmap[row["discogs_id"]] = row["id"]

    if track_batch:
        tracks = [(rmap[t[0]], t[1], t[2], t[3]) for t in track_batch if t[0] in rmap]
        cur.executemany(
            "INSERT OR IGNORE INTO tracks (release_id, title, position, duration_ms) VALUES (?, ?, ?, ?)",
            tracks,
        )

    if credit_batch:
        credits = [(rmap[c[0]], c[1], c[2], c[3], c[4], c[5]) for c in credit_batch if c[0] in rmap]
        cur.executemany(
            """INSERT OR IGNORE INTO credits (release_id, entity_name, entity_slug, role, entity_type, discogs_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            credits,
        )

    if link_batch:
        links = [(rmap[l[0]], l[1], l[2]) for l in link_batch if l[0] in rmap]
        cur.executemany(
            "INSERT OR IGNORE INTO release_artists (release_id, artist_id, role) VALUES (?, ?, ?)",
            links,
        )

    if ag_set:
        ag = [(aid, gid_cache[g]) for aid, g in ag_set if g in gid_cache]
        cur.executemany("INSERT OR IGNORE INTO artist_genres (artist_id, genre_id) VALUES (?, ?)", ag)

    if as_set:
        ast = [(aid, sid_cache[s]) for aid, s in as_set if s in sid_cache]
        cur.executemany("INSERT OR IGNORE INTO artist_styles (artist_id, style_id) VALUES (?, ?)", ast)

    db.commit()


def pass3_import_all(
    releases_path: str,
    db: sqlite3.Connection,
    mains: Set[int],
    various_id: int,
    batch_size: int,
    limit: int,
    require_genre: bool,
    gid_cache: Dict[str, int],
    sid_cache: Dict[str, int],
) -> Tuple[int, int, int, int]:
    """Pass 3: import canonical releases, tracks, credits, and artist links."""
    cur = db.cursor()
    cur.execute("SELECT discogs_id, id, slug FROM artists WHERE discogs_id IS NOT NULL")
    amap: Dict[int, int] = {}
    slug_by_aid: Dict[int, str] = {}
    for row in cur.fetchall():
        did = int(row["discogs_id"])
        aid = int(row["id"])
        amap[did] = aid
        slug_by_aid[did] = str(row["slug"])

    logger.info("Pass 3: loaded %d artists into memory map.", len(amap))

    # Hot index on releases(discogs_id) for fast batch mapping
    db.execute("CREATE INDEX IF NOT EXISTS idx_releases_discogs ON releases(discogs_id)")
    db.commit()

    fallback_seen: Set[int] = set()
    n = 0
    t0 = time.monotonic()
    n_rel = 0
    n_trk = 0
    n_crd = 0
    n_lnk = 0

    rel_batch: list = []
    credit_batch: list = []
    track_batch: list = []
    link_batch: list = []
    ag_set: set = set()
    as_set: set = set()

    for elem, ratio in fast_iter(releases_path, "release", limit=limit):
        n += 1
        if n % 100000 == 0:
            dt = time.monotonic() - t0
            rate = n / max(dt, 0.1)
            pct = ratio * 100.0
            eta_s = (1.0 - ratio) / max(ratio, 0.0001) * dt if ratio > 0.01 else 0
            logger.info("Pass 3: %d scanned (%.1f%%, %d releases, %.0f rel/s, ETA %.0fm)...",
                        n, pct, n_rel, rate, eta_s / 60)

        if not is_eligible(elem, require_genre):
            continue

        mid, is_main = canonical_master(elem)
        if mid is not None:
            if mid in mains:
                if not is_main:
                    continue
            else:
                if mid in fallback_seen:
                    continue
                fallback_seen.add(mid)

        genres = [g.text.strip() for g in elem.findall("genres/genre") if g.text]
        styles = [s.text.strip() for s in elem.findall("styles/style") if s.text]
        if not genres:
            continue

        rid_s = elem.get("id")
        if not rid_s:
            continue
        try:
            rid = int(rid_s)
        except ValueError:
            continue

        aids: List[Tuple[int, str]] = []
        is_various = False
        primary_db: Optional[int] = None

        artists_el = elem.find("artists")
        if artists_el is not None:
            for idx, a in enumerate(artists_el.findall("artist")):
                nm = (a.findtext("name") or "").strip().lower()
                if nm in COMPILATION_ARTIST_NAMES:
                    is_various = True
                at = a.findtext("id")
                if at:
                    try:
                        aid = int(at)
                    except ValueError:
                        continue
                    if aid == 194:
                        is_various = True
                        continue
                    role = "primary" if idx == 0 else "secondary"
                    aids.append((aid, role))
                    if primary_db is None and aid in amap:
                        primary_db = amap[aid]

        title = _child_text(elem, "title").strip()
        if not title:
            title = "Untitled"

        country, lab, fmt, cover, descriptions = _release_meta(elem)
        genres_lower = [x.lower() for x in genres]
        styles_lower = [x.lower() for x in styles]

        if is_various:
            primary_db = various_id

        # Non-VA releases where no listed release-level artist qualified are skipped
        if not primary_db:
            continue

        # For Various Artists releases: only import if at least one track artist or release artist qualifies
        if primary_db == various_id:
            has_qualifying_artist = any(aid in amap for aid, _ in aids)
            if not has_qualifying_artist:
                tracklist_el = elem.find("tracklist")
                if tracklist_el is not None:
                    for trk in tracklist_el.findall("track"):
                        ta_el = trk.find("artists")
                        if ta_el is not None:
                            for ta in ta_el.findall("artist"):
                                at = ta.findtext("id")
                                if at:
                                    try:
                                        if int(at) in amap:
                                            has_qualifying_artist = True
                                            break
                                    except ValueError:
                                        pass
                        if has_qualifying_artist:
                            break
            if not has_qualifying_artist:
                continue

        # Collect tracks and credits
        added_tracks, track_aids = _collect_tracks_and_credits(
            elem, rid, track_batch, credit_batch, slug_by_aid
        )
        n_trk += added_tracks

        rtype = _release_type(descriptions, genres_lower, styles_lower, is_various, added_tracks)

        rel_year = _extract_year(_child_text(elem, "released"))
        rel_batch.append((
            primary_db, rid, mid, 1 if is_main else 0, title, rel_year,
            country, rtype, lab, fmt, cover,
            cached_genre_json(tuple(genres)), cached_style_json(tuple(styles)),
        ))
        n_rel += 1

        seen_links: Set[Tuple[int, str]] = set()

        if primary_db != various_id:
            seen_links.add((primary_db, "primary"))
            link_batch.append((rid, primary_db, "primary"))
            n_lnk += 1

        for aid, role in aids:
            dbid = amap.get(aid)
            if dbid is not None and (dbid, role) not in seen_links:
                seen_links.add((dbid, role))
                link_batch.append((rid, dbid, role))
                n_lnk += 1

        for aid, role in track_aids:
            dbid = amap.get(aid)
            if dbid is not None and (dbid, role) not in seen_links:
                seen_links.add((dbid, role))
                link_batch.append((rid, dbid, role))
                n_lnk += 1

        if primary_db == various_id and (various_id, "primary") not in seen_links:
            seen_links.add((various_id, "primary"))
            link_batch.append((rid, various_id, "primary"))
            n_lnk += 1

        for dbid, _role in seen_links:
            if dbid != various_id:
                for g in genres:
                    ag_set.add((dbid, g))
                for s in styles:
                    as_set.add((dbid, s))

        if len(rel_batch) >= batch_size:
            _commit_batch(
                db, rel_batch, credit_batch, track_batch, link_batch,
                ag_set, as_set, gid_cache, sid_cache
            )
            n_crd += len(credit_batch)
            rel_batch, credit_batch, track_batch, link_batch = [], [], [], []
            ag_set, as_set = set(), set()

    if rel_batch:
        n_crd += len(credit_batch)
        _commit_batch(
            db, rel_batch, credit_batch, track_batch, link_batch,
            ag_set, as_set, gid_cache, sid_cache
        )

    dt = time.monotonic() - t0
    logger.info("Pass 3 done: %d releases, %d tracks, %d credits, %d links in %.1fs.",
                n_rel, n_trk, n_crd, n_lnk, dt)
    return n_rel, n_trk, n_crd, n_lnk


def _extract_year(released: str) -> Optional[int]:
    if not released:
        return None
    m = _YEAR_RE.search(released)
    return int(m.group()) if m else None


def seed_enrichment_queue(db: sqlite3.Connection) -> int:
    """Seed enrichment_queue prioritizing artists with the most releases."""
    logger.info("Seeding enrichment_queue from imported release links...")
    cur = db.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO enrichment_queue (entity_type, entity_id, priority)
           SELECT 'artist', artist_id, MIN(COUNT(*), 1000)
           FROM release_artists
           WHERE artist_id > 0
           GROUP BY artist_id"""
    )
    db.commit()
    count = cur.execute("SELECT COUNT(*) FROM enrichment_queue").fetchone()[0]
    logger.info("Enrichment queue seeded with %d artists.", count)
    return count


def run_import(cfg: ImportConfig) -> ImportStats:
    """Main programmatic import runner."""
    t_start = time.monotonic()
    stats = ImportStats()

    db_path = os.path.abspath(cfg.db_path)
    if cfg.fresh and os.path.exists(db_path):
        logger.info("Fresh import requested: removing existing %s", db_path)
        for ext in ("", "-wal", "-shm"):
            p = db_path + ext
            if os.path.exists(p):
                os.remove(p)

    if not cfg.fresh and os.path.exists(db_path):
        with sqlite3.connect(db_path) as check_conn:
            has_releases = check_conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='releases'"
            ).fetchone()
            if has_releases:
                rel_cnt = check_conn.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
                if rel_cnt > 0:
                    raise RuntimeError(
                        f"Database at {db_path} already contains {rel_cnt} releases! Use --fresh to overwrite."
                    )

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")

    db = get_db(db_path, bulk=True)
    try:
        ensure_schema(db, schema_path)
        various_id = ensure_special_artists(db)
        drop_bulk_indexes(db)

        qual: Set[int]
        mains: Set[int]
        style_to_genre: Dict[str, str]
        p1_stats: dict = {}
        pass1_counts: Dict[int, int] = {}

        can_use_cache = (
            cfg.skip_pass1
            and cfg.qualifiers_cache
            and os.path.exists(cfg.qualifiers_cache)
        )

        if can_use_cache:
            with open(cfg.qualifiers_cache, encoding="utf-8") as f:
                cdata = json.load(f)
            if cdata.get("version") == 2 and cdata.get("min_releases") == cfg.min_releases:
                qual = set(cdata["qualifiers"])
                mains = set(cdata["mains"])
                style_to_genre = cdata.get("style_to_genre", {})
                pass1_counts = {int(k): v for k, v in cdata.get("counts", {}).items()}
                logger.info("Loaded Cache v2: %d qualifiers, %d mains.", len(qual), len(mains))
            else:
                logger.warning("Cache invalid or parameter mismatch. Rerunning Pass 1.")
                can_use_cache = False

        if not can_use_cache:
            qual, mains, style_to_genre, p1_stats = pass1_count_releases(
                cfg.releases_path, cfg.min_releases, cfg.require_genre, cfg.limit
            )
            stats.pass1_scanned = p1_stats.get("scanned", 0)
            stats.pass1_canonical = p1_stats.get("canonical", 0)

            if cfg.qualifiers_cache and not cfg.limit:
                cache_payload = {
                    "version": 2,
                    "min_releases": cfg.min_releases,
                    "require_genre": cfg.require_genre,
                    "qualifiers": sorted(qual),
                    "mains": sorted(mains),
                    "style_to_genre": style_to_genre,
                }
                with open(cfg.qualifiers_cache, "w", encoding="utf-8") as f:
                    json.dump(cache_payload, f)
                logger.info("Saved Pass 1 qualifiers cache v2 to %s", cfg.qualifiers_cache)

        stats.qualifying_artists = len(qual)
        if not qual:
            logger.warning("No qualifying artists found. Exiting.")
            return stats

        # Pass 2: Artists & Slugs
        imported_artists = pass2_import_artists(
            cfg.artists_path, db, qual, cfg.batch_size, cfg.artists_limit, pass1_counts
        )
        stats.artists_imported = imported_artists

        # Taxonomy Setup
        gid_cache, sid_cache = setup_taxonomy(db, style_to_genre)

        # Pass 3: Releases, Tracks, Credits, Links
        n_rel, n_trk, n_crd, n_lnk = pass3_import_all(
            cfg.releases_path, db, mains, various_id, cfg.batch_size,
            cfg.limit, cfg.require_genre, gid_cache, sid_cache,
        )
        stats.releases_imported = n_rel
        stats.tracks_imported = n_trk
        stats.credits_imported = n_crd
        stats.links_imported = n_lnk

        if not cfg.no_finalize:
            seed_enrichment_queue(db)
            marker = {
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "min_releases": cfg.min_releases,
                "artists": imported_artists,
                "releases": n_rel,
                "tracks": n_trk,
                "credits": n_crd,
            }
            finalize_db(db, marker_info=marker)
    finally:
        db.close()


    stats.total_seconds = time.monotonic() - t_start
    logger.info("Import completed successfully in %.1fs.", stats.total_seconds)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="MusicLab Discogs importer v2 (fast full-info).")
    parser.add_argument("--artists", required=True, help="Path to Discogs artists XML dump")
    parser.add_argument("--releases", required=True, help="Path to Discogs releases XML dump")
    parser.add_argument("--db", default="D:/VibeCheck/musiclab_full.db", help="Target SQLite DB")
    parser.add_argument("--min-releases", type=int, default=2)
    parser.add_argument("--no-require-genre", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10000)
    parser.add_argument("--limit", type=int, default=0, help="Cap releases scanned (benchmark)")
    parser.add_argument("--artists-limit", type=int, default=0, help="Cap artists scanned")
    parser.add_argument("--benchmark", type=int, default=0, help="Shortcut: --limit N --artists-limit N*2, fresh")
    parser.add_argument("--qualifiers-cache", default="", help="JSON cache for pass-1 IDs")
    parser.add_argument("--skip-pass1", action="store_true", help="Load qualifiers from cache")
    parser.add_argument("--no-finalize", action="store_true", help="Skip index rebuild/ANALYZE")
    parser.add_argument("--fresh", action="store_true", help="Delete target DB before importing")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    limit = args.benchmark or args.limit
    artists_limit = (args.benchmark * 2) if args.benchmark else args.artists_limit
    fresh = args.fresh or bool(args.benchmark)

    cfg = ImportConfig(
        artists_path=args.artists,
        releases_path=args.releases,
        db_path=args.db,
        min_releases=args.min_releases,
        require_genre=not args.no_require_genre,
        batch_size=args.batch_size,
        limit=limit,
        artists_limit=artists_limit,
        qualifiers_cache=args.qualifiers_cache,
        skip_pass1=args.skip_pass1,
        no_finalize=args.no_finalize,
        fresh=fresh,
    )

    run_import(cfg)


if __name__ == "__main__":
    main()
