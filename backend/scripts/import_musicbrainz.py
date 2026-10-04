"""Import MusicBrainz data dump into MusicLab's SQLite database."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

STARTUP_MSG = """
MusicBrainz data dump:
  Full dump: https://data.metabrainz.org/pub/musicbrainz/data/fullexport/
  (Pick the latest date, download mbdump.tar.bz2)

Extract with:
  tar xjf mbdump.tar.bz2

Then run:
  python scripts/import_musicbrainz.py --dump-dir ./mbdump/
"""

def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-")

def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite and return connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def read_tsv(file_path: Path):
    """Read a tab-separated Postgres COPY file, yielding rows."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return
    
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            # Postgres COPY uses tab as delimiter, \\N for NULL
            yield [None if col == "\\N" else col for col in line.rstrip("\r\n").split("\t")]

def parse_date(year: str | None, month: str | None, day: str | None) -> str | None:
    """Construct a YYYY-MM-DD date string from components."""
    if not year:
        return None
    res = year
    if month:
        res += f"-{month.zfill(2)}"
        if day:
            res += f"-{day.zfill(2)}"
    return res

def ensure_tracks_table(conn: sqlite3.Connection) -> None:
    """Ensure the tracks table exists in the schema."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            release_id INTEGER NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
            mbid TEXT,
            title TEXT NOT NULL,
            position INTEGER,
            duration_ms INTEGER,
            UNIQUE(release_id, position)
        )
    """)
    conn.commit()

def process_musicbrainz_dump(dump_dir: Path, db_path: Path, batch_size: int) -> None:
    """Run the comprehensive import pipeline."""
    logger.info(f"Connecting to database at {db_path}")
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    ensure_tracks_table(conn)
    
    # ---------------------------------------------------------
    # Step 1 — Load lookup tables into memory
    # ---------------------------------------------------------
    logger.info("Step 1: Loading lookup tables...")
    artist_types: Dict[str, str] = {}
    for row in read_tsv(dump_dir / "artist_type"):
        if len(row) >= 2:
            artist_types[row[0]] = row[1]
            
    link_types: Dict[str, str] = {}
    for row in read_tsv(dump_dir / "link_type"):
        if len(row) >= 7:
            # entity_type0='artist' AND entity_type1='artist'
            if row[4] == 'artist' and row[5] == 'artist':
                link_types[row[0]] = row[6]
                
    links: Dict[str, str] = {}
    for row in read_tsv(dump_dir / "link"):
        if len(row) >= 2:
            links[row[0]] = row[1]

    # ---------------------------------------------------------
    # Step 2 — Match MB artists to existing DB artists
    # ---------------------------------------------------------
    logger.info("Step 2: Matching MB artists to existing DB artists...")
    cursor.execute("SELECT id, name, slug FROM artists")
    existing_artists_by_name = {}
    existing_artists_by_slug = {}
    for row in cursor:
        db_id = row["id"]
        if row["name"]:
            existing_artists_by_name[row["name"].lower()] = db_id
        if row["slug"]:
            existing_artists_by_slug[row["slug"]] = db_id

    mb_artist_to_db_artist: Dict[str, int] = {}
    artist_updates: List[Tuple] = []
    
    count = 0
    for row in read_tsv(dump_dir / "artist"):
        if len(row) < 12:
            continue
            
        mb_id = row[0]
        gid = row[1]
        name = row[2]
        if not name:
            continue
            
        # Try exact name match then slug match
        db_artist_id = existing_artists_by_name.get(name.lower())
        if not db_artist_id:
            db_artist_id = existing_artists_by_slug.get(slugify(name))
            
        if db_artist_id:
            type_id = row[10]
            country = row[11]  # using 'area' column as country info
            begin_date = parse_date(row[4], row[5], row[6]) if len(row) > 6 else None
            end_date = parse_date(row[7], row[8], row[9]) if len(row) > 9 else None
            artist_type = artist_types.get(type_id) if type_id else None
            
            mb_artist_to_db_artist[mb_id] = db_artist_id
            artist_updates.append((gid, artist_type, country, begin_date, end_date, db_artist_id))
            
        count += 1
        if count % 100000 == 0:
            logger.info(f"  Processed {count} artists...")

    logger.info(f"  Found {len(artist_updates)} matching artists to update.")
    for i in range(0, len(artist_updates), batch_size):
        cursor.executemany("""
            UPDATE artists 
            SET mbid = ?, artist_type = ?, country = ?, begin_date = ?, end_date = ?
            WHERE id = ?
        """, artist_updates[i:i+batch_size])
    conn.commit()

    # ---------------------------------------------------------
    # Step 3 — Build artist_credit -> artist mapping
    # ---------------------------------------------------------
    logger.info("Step 3: Building artist_credit -> artist mapping...")
    artist_credit_to_db_artists = defaultdict(list)
    count = 0
    for row in read_tsv(dump_dir / "artist_credit_name"):
        if len(row) >= 3:
            ac_id = row[0]
            mb_artist_id = row[2]
            if mb_artist_id in mb_artist_to_db_artist:
                artist_credit_to_db_artists[ac_id].append(mb_artist_to_db_artist[mb_artist_id])
        
        count += 1
        if count % 100000 == 0:
            logger.info(f"  Processed {count} artist credits...")

    # ---------------------------------------------------------
    # Step 4 — Match MB releases to existing DB releases
    # ---------------------------------------------------------
    logger.info("Step 4: Matching MB releases to existing DB releases...")
    cursor.execute("SELECT id, title, artist_id FROM releases")
    existing_releases = {}
    for row in cursor:
        if row["title"]:
            key = (slugify(row["title"]), row["artist_id"])
            existing_releases[key] = row["id"]

    mb_release_to_db_release: Dict[str, int] = {}
    release_updates: List[Tuple] = []
    
    count = 0
    for row in read_tsv(dump_dir / "release"):
        if len(row) < 4:
            continue
            
        rel_id = row[0]
        gid = row[1]
        name = row[2]
        ac_id = row[3]
        
        if not name or not ac_id:
            continue
            
        db_artist_ids = artist_credit_to_db_artists.get(ac_id, [])
        for db_artist_id in db_artist_ids:
            key = (slugify(name), db_artist_id)
            if key in existing_releases:
                db_rel_id = existing_releases[key]
                mb_release_to_db_release[rel_id] = db_rel_id
                release_updates.append((gid, db_rel_id))
                break  # Matched this release, avoid duplicate updates
                
        count += 1
        if count % 100000 == 0:
            logger.info(f"  Processed {count} releases...")
            
    logger.info(f"  Found {len(release_updates)} matching releases to update.")
    for i in range(0, len(release_updates), batch_size):
        cursor.executemany("UPDATE releases SET mbid = ? WHERE id = ?", release_updates[i:i+batch_size])
    conn.commit()

    # ---------------------------------------------------------
    # Step 5 — Import tracks
    # ---------------------------------------------------------
    logger.info("Step 5: Importing tracks...")
    
    logger.info("  Loading medium to release mapping...")
    medium_to_release: Dict[str, int] = {}
    for row in read_tsv(dump_dir / "medium"):
        if len(row) >= 2:
            medium_id = row[0]
            rel_id = row[1]
            if rel_id in mb_release_to_db_release:
                medium_to_release[medium_id] = mb_release_to_db_release[rel_id]
                
    logger.info("  Loading recording to GID mapping...")
    recording_to_gid: Dict[str, str] = {}
    for row in read_tsv(dump_dir / "recording"):
        if len(row) >= 2:
            recording_to_gid[row[0]] = row[1]

    logger.info("  Processing tracks...")
    track_inserts: List[Tuple] = []
    tracks_imported = 0
    count = 0
    for row in read_tsv(dump_dir / "track"):
        if len(row) < 9:
            continue
            
        recording_id = row[2]
        medium_id = row[3]
        position = row[4]
        name = row[6]
        length = row[8]
        
        db_rel_id = medium_to_release.get(medium_id)
        if db_rel_id:
            mbid = recording_to_gid.get(recording_id)
            duration_ms = length if length else None
            # release_id, mbid, title, position, duration_ms
            track_inserts.append((db_rel_id, mbid, name, position, duration_ms))
            tracks_imported += 1
            
        count += 1
        if count % 100000 == 0:
            logger.info(f"  Processed {count} tracks...")
            if len(track_inserts) >= batch_size:
                cursor.executemany("""
                    INSERT OR IGNORE INTO tracks 
                    (release_id, mbid, title, position, duration_ms) 
                    VALUES (?, ?, ?, ?, ?)
                """, track_inserts)
                conn.commit()
                track_inserts.clear()

    if track_inserts:
        cursor.executemany("""
            INSERT OR IGNORE INTO tracks 
            (release_id, mbid, title, position, duration_ms) 
            VALUES (?, ?, ?, ?, ?)
        """, track_inserts)
        conn.commit()
        track_inserts.clear()

    logger.info(f"  Imported {tracks_imported} tracks.")

    # ---------------------------------------------------------
    # Step 6 — Import artist-to-artist relations
    # ---------------------------------------------------------
    logger.info("Step 6: Importing artist relations...")
    
    db_artist_relations = defaultdict(list)
    count = 0
    for row in read_tsv(dump_dir / "l_artist_artist"):
        if len(row) < 4:
            continue
            
        link_id = row[1]
        entity0 = row[2]
        entity1 = row[3]
        
        db_artist0 = mb_artist_to_db_artist.get(entity0)
        db_artist1 = mb_artist_to_db_artist.get(entity1)
        
        if db_artist0 and db_artist1:
            link_type_id = links.get(link_id)
            link_name = link_types.get(link_type_id)
            if link_name:
                db_artist_relations[db_artist0].append({
                    "target_artist_id": db_artist1,
                    "relation": link_name,
                    "direction": "forward"
                })
                db_artist_relations[db_artist1].append({
                    "target_artist_id": db_artist0,
                    "relation": link_name,
                    "direction": "backward"
                })
                
        count += 1
        if count % 100000 == 0:
            logger.info(f"  Processed {count} artist-artist relations...")

    logger.info(f"  Found relations for {len(db_artist_relations)} artists. Updating database...")
    relation_updates = []
    
    # Process in chunks to respect SQLite parameter limits
    artist_ids = list(db_artist_relations.keys())
    chunk_size = 500
    for i in range(0, len(artist_ids), chunk_size):
        chunk = artist_ids[i:i+chunk_size]
        placeholders = ','.join('?' * len(chunk))
        
        cursor.execute(f"SELECT id, mb_relations FROM artists WHERE id IN ({placeholders})", chunk)
        for row in cursor:
            db_id = row["id"]
            existing_rels = []
            if row["mb_relations"]:
                try:
                    existing_rels = json.loads(row["mb_relations"])
                except json.JSONDecodeError:
                    pass
                    
            new_rels = db_artist_relations[db_id]
            existing_rels.extend(new_rels)
            
            # Simple deduplication by converting dicts to strings temporarily
            seen = set()
            deduped = []
            for r in existing_rels:
                r_str = json.dumps(r, sort_keys=True)
                if r_str not in seen:
                    seen.add(r_str)
                    deduped.append(r)
            
            relation_updates.append((json.dumps(deduped), db_id))
            
    for i in range(0, len(relation_updates), batch_size):
        cursor.executemany("UPDATE artists SET mb_relations = ? WHERE id = ?", relation_updates[i:i+batch_size])
    conn.commit()

    logger.info("Import Summary:")
    logger.info(f"  Artists matched: {len(artist_updates)}")
    logger.info(f"  Releases matched: {len(release_updates)}")
    logger.info(f"  Tracks imported: {tracks_imported}")
    logger.info(f"  Artists with relations updated: {len(relation_updates)}")
    logger.info("Import complete.")

def main() -> None:
    print(STARTUP_MSG)
    
    parser = argparse.ArgumentParser(
        description="Import MusicBrainz data dump into MusicLab's SQLite database."
    )
    parser.add_argument(
        "--dump-dir",
        type=Path,
        required=True,
        help="Path to extracted mbdump directory"
    )
    parser.add_argument("--db", type=Path, default=Path("data/musiclab.db"), help="Path to SQLite database")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch insert size (default: 1000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    if not args.dump_dir.exists() or not args.dump_dir.is_dir():
        logger.error(f"Dump directory does not exist: {args.dump_dir}")
        sys.exit(1)
        
    if not args.db.parent.exists():
        logger.error(f"Database directory does not exist: {args.db.parent}")
        sys.exit(1)
        
    try:
        process_musicbrainz_dump(args.dump_dir, args.db, args.batch_size)
    except Exception as e:
        logger.exception("An error occurred during import:")
        sys.exit(1)

if __name__ == "__main__":
    main()
