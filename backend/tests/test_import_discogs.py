"""Unit and integration tests for Discogs dump importer."""

from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.import_discogs import ImportConfig, run_import
from scripts.verify_import import run_checks


def _write_gz(path: Path, content: str) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)


@pytest.fixture
def synthetic_dumps(tmp_path: Path):
    """Generate small synthetic Discogs XML dumps covering edge cases."""
    artists_xml = """<?xml version="1.0" encoding="UTF-8"?>
<artists>
  <artist>
    <id>1</id>
    <name>Persuader, The (2)</name>
    <profile>Electronic artist [a=Jesper Dahlbäck] [b]active[/b] since [url=http://example.com]1994[/url].</profile>
  </artist>
  <artist>
    <id>2</id>
    <name>Johannes Heil</name>
    <profile>Techno producer.</profile>
  </artist>
  <artist>
    <id>3</id>
    <name>Hans Zimmer</name>
    <profile>Soundtrack composer.</profile>
  </artist>
  <artist>
    <id>4</id>
    <name>Björk</name>
    <profile>Icelandic artist.</profile>
  </artist>
  <artist>
    <id>5</id>
    <name>Bjork</name>
    <profile>Colliding slug artist.</profile>
  </artist>
  <artist>
    <id>194</id>
    <name>Various</name>
    <profile>Various Artists.</profile>
  </artist>
</artists>
"""

    releases_xml = """<?xml version="1.0" encoding="UTF-8"?>
<releases>
  <!-- Release 101: Non-main release of master 1000 seen first -->
  <release id="101" status="Accepted">
    <title>Stockholm Reissue</title>
    <artists><artist><id>1</id><name>The Persuader</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Deep House</style></styles>
    <master_id is_main_release="false">1000</master_id>
    <tracklist>
      <track><title>Side A</title></track>
      <track><position>A1</position><title>Östermalm</title><duration>4:45</duration></track>
    </tracklist>
  </release>

  <!-- Release 102: Main release of master 1000 seen second (should WIN) -->
  <release id="102" status="Accepted">
    <title>Stockholm</title>
    <artists><artist><id>1</id><name>The Persuader</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Deep House</style></styles>
    <formats><format name="Vinyl"><descriptions><description>Album</description></descriptions></format></formats>
    <master_id is_main_release="true">1000</master_id>
    <tracklist>
      <track><title>This Side</title></track>
      <track><position>A1</position><title>Östermalm</title><duration>4:45</duration></track>
      <track><position>B1</position><title>Vasastaden</title><duration>6:11</duration>
        <extraartists>
          <artist><id>2</id><name>Johannes Heil</name><role>Remix</role></artist>
        </extraartists>
      </track>
    </tracklist>
  </release>

  <!-- Release 103: Second release for Persuader to reach min_releases=2 (EP) -->
  <release id="103" status="Accepted">
    <title>Persuader EP</title>
    <artists><artist><id>1</id><name>The Persuader</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Deep House</style></styles>
    <formats><format name="Vinyl"><descriptions><description>EP</description></descriptions></format></formats>
    <tracklist>
      <track><position>A1</position><title>Track One</title><duration>5:00</duration></track>
      <track><position>A2</position><title>Track Two</title><duration>5:00</duration></track>
    </tracklist>
  </release>

  <!-- Release 104: Hans Zimmer Soundtrack 1 -->
  <release id="104" status="Accepted">
    <title>Inception OST</title>
    <artists><artist><id>3</id><name>Hans Zimmer</name></artist></artists>
    <genres><genre>Stage &amp; Screen</genre></genres>
    <styles><style>Soundtrack</style><style>Score</style></styles>
    <formats><format name="CD"><descriptions><description>Album</description></descriptions></format></formats>
    <tracklist>
      <track><position>1</position><title>Time</title><duration>4:35</duration></track>
    </tracklist>
  </release>

  <!-- Release 105: Hans Zimmer Soundtrack 2 (reaches min_releases=2) -->
  <release id="105" status="Accepted">
    <title>Interstellar OST</title>
    <artists><artist><id>3</id><name>Hans Zimmer</name></artist></artists>
    <genres><genre>Stage &amp; Screen</genre></genres>
    <styles><style>Soundtrack</style></styles>
    <tracklist>
      <track><position>1</position><title>Cornfield Chase</title><duration>2:06</duration></track>
    </tracklist>
  </release>

  <!-- Release 106 & 107: Björk (2 releases) -->
  <release id="106" status="Accepted">
    <title>Debut</title>
    <artists><artist><id>4</id><name>Björk</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Trip Hop</style></styles>
    <tracklist><track><position>1</position><title>Human Behaviour</title></track></tracklist>
  </release>
  <release id="107" status="Accepted">
    <title>Post</title>
    <artists><artist><id>4</id><name>Björk</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Trip Hop</style></styles>
    <tracklist><track><position>1</position><title>Army of Me</title></track></tracklist>
  </release>

  <!-- Release 108 & 109: Other Bjork (2 releases) -->
  <release id="108" status="Accepted">
    <title>Other Album 1</title>
    <artists><artist><id>5</id><name>Bjork</name></artist></artists>
    <genres><genre>Rock</genre></genres>
    <styles><style>Post-Punk</style></styles>
    <tracklist><track><position>1</position><title>Song 1</title></track></tracklist>
  </release>
  <release id="109" status="Accepted">
    <title>Other Album 2</title>
    <artists><artist><id>5</id><name>Bjork</name></artist></artists>
    <genres><genre>Rock</genre></genres>
    <styles><style>Post-Punk</style></styles>
    <tracklist><track><position>1</position><title>Song 2</title></track></tracklist>
  </release>

  <!-- Release 110: Various Artists compilation with a qualifying track artist (Persuader) -->
  <release id="110" status="Accepted">
    <title>Best of Electronic</title>
    <artists><artist><id>194</id><name>Various</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <styles><style>Deep House</style></styles>
    <formats><format name="CD"><descriptions><description>Compilation</description></descriptions></format></formats>
    <tracklist>
      <track><position>1</position><title>Special Cut</title>
        <artists><artist><id>1</id><name>The Persuader</name></artist></artists>
      </track>
    </tracklist>
  </release>

  <!-- Release 111: Various Artists compilation with NO qualifying artists (should be SKIPPED) -->
  <release id="111" status="Accepted">
    <title>Unknown Compilation</title>
    <artists><artist><id>194</id><name>Various</name></artist></artists>
    <genres><genre>Electronic</genre></genres>
    <tracklist>
      <track><position>1</position><title>Track by Unknown</title>
        <artists><artist><id>9999</id><name>Random Guy</name></artist></artists>
      </track>
    </tracklist>
  </release>
</releases>
"""

    art_path = tmp_path / "artists.xml.gz"
    rel_path = tmp_path / "releases.xml.gz"
    _write_gz(art_path, artists_xml)
    _write_gz(rel_path, releases_xml)
    return art_path, rel_path


def test_synthetic_discogs_import(tmp_path: Path, synthetic_dumps):
    art_path, rel_path = synthetic_dumps
    db_path = tmp_path / "test_import.db"

    cfg = ImportConfig(
        artists_path=str(art_path),
        releases_path=str(rel_path),
        db_path=str(db_path),
        min_releases=2,
        require_genre=True,
        fresh=True,
    )

    stats = run_import(cfg)
    assert stats.artists_imported >= 3
    assert stats.releases_imported > 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Master deduplication: Release 102 (main) kept, Release 101 (non-main) skipped
    rel_101 = cur.execute("SELECT * FROM releases WHERE discogs_id = 101").fetchone()
    rel_102 = cur.execute("SELECT * FROM releases WHERE discogs_id = 102").fetchone()
    assert rel_101 is None, "Non-main release 101 should not be imported when main 102 exists"
    assert rel_102 is not None, "Main release 102 should be imported"
    assert rel_102["master_id"] == 1000
    assert rel_102["is_main_release"] == 1

    # 2. Display name cleaned & bio markup cleaned
    persuader = cur.execute("SELECT * FROM artists WHERE discogs_id = 1").fetchone()
    assert persuader is not None
    assert persuader["name"] == "Persuader, The"
    assert "(2)" not in persuader["name"]
    assert "[a=" not in persuader["bio"]
    assert "[b]" not in persuader["bio"]
    assert "Jesper Dahlbäck" in persuader["bio"]

    # 3. Track-level credits & heading skipping
    tracks = cur.execute("SELECT * FROM tracks WHERE release_id = ? ORDER BY position", (rel_102["id"],)).fetchall()
    assert len(tracks) == 2, "Heading track 'This Side' should be omitted"
    assert tracks[0]["position"] == 1
    assert tracks[1]["position"] == 2

    # Credit for Johannes Heil on track 2
    credits = cur.execute("SELECT * FROM credits WHERE release_id = ?", (rel_102["id"],)).fetchall()
    assert len(credits) == 1
    assert credits[0]["entity_name"] == "Johannes Heil"
    assert credits[0]["role"] == "Remix"

    # 4. Release type classification
    assert rel_102["release_type"] == "Album"
    rel_103 = cur.execute("SELECT * FROM releases WHERE discogs_id = 103").fetchone()
    assert rel_103["release_type"] == "EP"

    # 5. Hans Zimmer Soundtrack stays on Hans Zimmer (not Various Artists)
    zimmer = cur.execute("SELECT * FROM artists WHERE discogs_id = 3").fetchone()
    assert zimmer is not None
    zimmer_rel = cur.execute("SELECT * FROM releases WHERE discogs_id = 104").fetchone()
    assert zimmer_rel["artist_id"] == zimmer["id"], "Soundtrack should stay with Hans Zimmer"
    assert zimmer_rel["release_type"] == "Soundtrack"

    # 6. Various Artists (id 194) excluded, synthetic -1 used
    va_194 = cur.execute("SELECT * FROM artists WHERE discogs_id = 194").fetchone()
    assert va_194 is None

    va_rel = cur.execute("SELECT * FROM releases WHERE discogs_id = 110").fetchone()
    assert va_rel is not None
    assert va_rel["artist_id"] == -1
    assert va_rel["release_type"] == "Compilation"

    # VA release 111 with unknown artist should be skipped
    unwanted_va = cur.execute("SELECT * FROM releases WHERE discogs_id = 111").fetchone()
    assert unwanted_va is None

    # 7. Release artists links
    va_links = cur.execute("SELECT * FROM release_artists WHERE release_id = ?", (va_rel["id"],)).fetchall()
    linked_aids = {l["artist_id"] for l in va_links}
    assert -1 in linked_aids
    assert persuader["id"] in linked_aids

    # 8. Slug disambiguation
    bjork1 = cur.execute("SELECT slug FROM artists WHERE discogs_id = 4").fetchone()
    bjork2 = cur.execute("SELECT slug FROM artists WHERE discogs_id = 5").fetchone()
    assert bjork1["slug"] != bjork2["slug"]
    assert "bjork" in bjork1["slug"]
    assert "bjork" in bjork2["slug"]

    # 9. Style hierarchy
    deep_house_parent = cur.execute(
        "SELECT g.name FROM styles s JOIN genres g ON g.id = s.genre_id WHERE s.name = 'Deep House'"
    ).fetchone()
    assert deep_house_parent is not None
    assert deep_house_parent[0] == "Electronic"

    conn.close()

    # 10. Run verify_import script on this generated DB
    assert run_checks(str(db_path), profile="tiny") is True
