"""Verification script for MusicLab Discogs imported database.

Validates schema constraints, canonical deduplication, release type detection,
taxonomy hierarchy, artist slugging, credits linking, and SQLite integrity.
Exits with 0 if all tests pass, or 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_import")


def run_checks(db_path: str, profile: str = "full", skip_integrity: bool = False) -> bool:
    """Run all verification checks on the database. Returns True if all pass."""
    logger.info("Opening database at %s (profile=%s)...", db_path, profile)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    failures: list[str] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        if passed:
            logger.info("  [PASS] %s%s", name, f" ({detail})" if detail else "")
        else:
            logger.error("  [FAIL] %s: %s", name, detail)
            failures.append(f"{name}: {detail}")

    # Check 1: SQLite Integrity & Foreign Keys
    cur.execute("PRAGMA foreign_keys=ON")
    fk_errors = cur.execute("PRAGMA foreign_key_check").fetchall()
    check("Foreign key check", len(fk_errors) == 0, f"{len(fk_errors)} violations")

    if not skip_integrity:
        integrity = cur.execute("PRAGMA integrity_check").fetchone()
        integrity_ok = integrity and integrity[0] == "ok"
        check("Integrity check", bool(integrity_ok), str(integrity[0] if integrity else "failed"))

    # Check 2: Table Counts
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    required_tables = [
        "artists", "releases", "tracks", "credits", "genres", "styles",
        "artist_genres", "artist_styles", "release_artists", "cache_entries", "enrichment_queue"
    ]
    missing = [t for t in required_tables if t not in tables]
    check("Required tables exist", len(missing) == 0, f"missing: {missing}")

    counts = {}
    for t in required_tables:
        if t in tables:
            counts[t] = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        else:
            counts[t] = 0

    logger.info("Table row counts: %s", counts)
    check("Artists populated", counts.get("artists", 0) > 0, f"count={counts.get('artists')}")
    check("Releases populated", counts.get("releases", 0) > 0, f"count={counts.get('releases')}")
    check("Tracks populated", counts.get("tracks", 0) > 0, f"count={counts.get('tracks')}")

    # Check 3: Master Canonical Deduplication (0 duplicate masters)
    dup_masters = cur.execute(
        """SELECT master_id, COUNT(*) as cnt
           FROM releases
           WHERE master_id IS NOT NULL
           GROUP BY master_id
           HAVING cnt > 1"""
    ).fetchall()
    check("No duplicate masters", len(dup_masters) == 0, f"{len(dup_masters)} duplicate masters found")

    # Check 4: Release Types
    type_counts = dict(cur.execute("SELECT release_type, COUNT(*) FROM releases GROUP BY release_type").fetchall())
    logger.info("Release type distribution: %s", type_counts)
    if profile != "tiny":
        check("Album release type detected", type_counts.get("Album", 0) > 0, f"Album={type_counts.get('Album', 0)}")
        check("Single release type detected", type_counts.get("Single", 0) > 0, f"Single={type_counts.get('Single', 0)}")
        check("EP release type detected", type_counts.get("EP", 0) > 0, f"EP={type_counts.get('EP', 0)}")
        check("Compilation release type detected", type_counts.get("Compilation", 0) > 0, f"Compilation={type_counts.get('Compilation', 0)}")
        if profile == "full":
            check("Soundtrack release type detected", type_counts.get("Soundtrack", 0) > 0, f"Soundtrack={type_counts.get('Soundtrack', 0)}")

    # Check 5: Artist Names & Slugs
    disambig_pat = re.compile(r"\s*\(\d+\)$")
    candidates = [r[0] for r in cur.execute("SELECT name FROM artists WHERE name LIKE '%)'").fetchall()]
    disambig_names = sum(1 for n in candidates if disambig_pat.search(n))
    check("Disambiguation numbers stripped from display names", disambig_names == 0, f"{disambig_names} found")

    empty_slugs = cur.execute("SELECT COUNT(*) FROM artists WHERE slug IS NULL OR slug = ''").fetchone()[0]
    check("No empty artist slugs", empty_slugs == 0, f"{empty_slugs} found")

    temp_slugs = cur.execute("SELECT COUNT(*) FROM artists WHERE slug LIKE '~tmp~%'").fetchone()[0]
    check("No temporary artist slugs remain", temp_slugs == 0, f"{temp_slugs} found")

    # Check 6: Various Artists
    va_194 = cur.execute("SELECT COUNT(*) FROM artists WHERE discogs_id = 194").fetchone()[0]
    check("Discogs Various Artists (id=194) excluded", va_194 == 0, f"{va_194} found")

    va_special = cur.execute("SELECT id, name, slug FROM artists WHERE id = -1").fetchone()
    check("Synthetic Various Artists id=-1 exists", va_special is not None, str(dict(va_special) if va_special else None))

    # Check 7: Release Artists Links
    unlinked_releases = cur.execute(
        """SELECT COUNT(*) FROM releases r
           WHERE NOT EXISTS (
               SELECT 1 FROM release_artists ra WHERE ra.release_id = r.id
           )"""
    ).fetchone()[0]
    check("All releases linked in release_artists", unlinked_releases == 0, f"{unlinked_releases} unlinked releases")

    # Check 8: Track Positions
    dup_positions = cur.execute(
        """SELECT release_id, position, COUNT(*) FROM tracks
           GROUP BY release_id, position HAVING COUNT(*) > 1"""
    ).fetchall()
    check("No duplicate track positions per release", len(dup_positions) == 0, f"{len(dup_positions)} duplicate positions")

    # Check 9: Credit Slugs Match Artist Slugs
    credit_slug_mismatches = cur.execute(
        """SELECT COUNT(*) FROM credits c
           JOIN artists a ON a.discogs_id = c.discogs_id
           WHERE c.discogs_id IS NOT NULL AND a.slug != c.entity_slug"""
    ).fetchone()[0]
    check("Credit entity_slug matches artist slug for imported artists", credit_slug_mismatches == 0, f"{credit_slug_mismatches} mismatches")

    # Check 10: Taxonomy Parentage (argmax logic)
    sample_styles = cur.execute(
        """SELECT s.name as style_name, g.name as genre_name
           FROM styles s JOIN genres g ON g.id = s.genre_id
           WHERE s.name IN ('Deep House', 'Techno', 'Post-Punk', 'Soul', 'Disco')"""
    ).fetchall()
    style_parents = {r["style_name"]: r["genre_name"] for r in sample_styles}
    logger.info("Sample style parents: %s", style_parents)
    if "Deep House" in style_parents:
        check("Deep House under Electronic", style_parents["Deep House"] == "Electronic", style_parents["Deep House"])
    if "Techno" in style_parents:
        check("Techno under Electronic", style_parents["Techno"] == "Electronic", style_parents["Techno"])
    if "Post-Punk" in style_parents:
        check("Post-Punk under Rock", style_parents["Post-Punk"] == "Rock", style_parents["Post-Punk"])
    if "Soul" in style_parents:
        check("Soul under Funk / Soul", style_parents["Soul"] in ("Funk / Soul", "Soul"), style_parents["Soul"])

    # Check 11: Index on releases(discogs_id)
    plan = cur.execute("EXPLAIN QUERY PLAN SELECT id FROM releases WHERE discogs_id = 12345").fetchall()
    plan_desc = " ".join(str(p[-1]) for p in plan)
    uses_index = "USING INDEX" in plan_desc or "COVERING INDEX" in plan_desc
    check("Releases discogs_id uses index", uses_index, plan_desc)

    # Check 12: Import Marker & Enrichment Queue
    if profile != "tiny":
        marker = cur.execute("SELECT value FROM cache_entries WHERE key = 'import:discogs_dump'").fetchone()
        check("Import marker recorded in cache_entries", marker is not None, marker[0] if marker else "missing")

        queue_count = counts.get("enrichment_queue", 0)
        check("Enrichment queue seeded", queue_count > 0, f"queue_count={queue_count}")

    conn.close()

    if failures:
        logger.error("Verification FAILED with %d error(s):", len(failures))
        for f in failures:
            logger.error("  - %s", f)
        return False

    logger.info("All verification checks PASSED successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify MusicLab imported SQLite database.")
    parser.add_argument("db", help="Path to SQLite database to verify")
    parser.add_argument("--profile", choices=["tiny", "bench", "full"], default="full", help="Validation profile")
    parser.add_argument("--skip-integrity", action="store_true", help="Skip full PRAGMA integrity_check page scan")
    args = parser.parse_args()

    success = run_checks(args.db, profile=args.profile, skip_integrity=args.skip_integrity)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
