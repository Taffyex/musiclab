# MusicLab Dataset Ingestion & Similarity Plan (Expanded)

> Status: approved direction, pre-implementation. Last revised: 2026-10-04.
> This document captures the expanded plan for turning MusicLab from a Discogs-enriched
> browse app into a multi-dataset hybrid similarity engine with a 24/7 data factory.

## 0. Ground truth (what actually exists today)

- `backend/app` modules: auth, cache, common, discogs, discovery, enrichment, explore,
  lastfm, lidarr, llm, musicbrainz, settings. The `enrichment` service already exists and
  exposes `enrich_artist_page`, `enrich_release_page`, `enrich_search` (used by routes).
- `backend/scripts`: `enrich_db.py` (713 lines, heavy in-place enrichment, To-Be-Deleted
  in favor of the enrichment service), `import_discogs.py` (1048 lines, one-time, works),
  `import_musicbrainz.py` (398 lines, one-time, works), `download_dumps.py` (1MB basic
  fetcher, replace with multi-source jobs), `verify_import.py` (checks + coverage, extend).
- `backend/app/config.py`: single `database_path`, no `data_root`, no per-layer DB config.
- Databases: `backend/data/musiclab.db` and `data/musiclab.db` both exist (dupe state).
- Import profile: full (`releases` 7.5M, `artists` 4.9M, `master_releases`, `taxonomy`,
  `credits` 12-18M, `discogs_styles` 623).
- Script debt: `enrich_db.py` contains its own `enrichment` module (2 copies),
  low-level repeated code, and 2 side-effect-at-import calls at line 712-713.
- Windows: `.venv` has deps; plan tested on Windows 11 laptop first.

## 1. Direction (one line)

Take ALL datasets (musicbrainz full + discogs full + acousticbrainz + listenbrainz +
listenbrainz full listens + everynoise + wikidata + coverartarchive + MPD), house them
in one ATTACHed SQLite layer cluster, and build a hybrid scoring engine on top.


## 2. Multi-DB layer architecture

Lives in `backend/data/` (config `data_root`):

| Layer DB | Owner | Content | Sync strategy |
|---|---|---|---|
| `musiclab.db` (core) | import_discogs + verify | artists, releases, master_releases, taxonomy, credits, discogs_styles | rebuilt from Discogs dumps on demand |
| `mb.db` | import_mb_spine + link_mbids | mb_artist, mb_recording, mb_release, mb_url_link, mb_tag, mb_*, linker outputs | rebuilt from MB dumps |
| `ab.db` | import_acousticbrainz | ab_recording_features, ab_artist_profile | built from AB dumps (37.4GB) |
| `lb.db` | import_listenbrainz | lb_user_artist, artist_popularity, artist_colisten, lb_user_recording | built from LB dumps |
| `enao.db` | scrape_everynoise | enao_genre, enao_genre_artist, enao_xy | build once, then monthly |
| `wikidata.db` | import_wikidata | wd_qid, wd_artist (origin, formed, genres, labels, members, P18) | built from SPARQL dumps |
| `user.db` | the app | user_artist, artist_track_user, search_history, user_settings | **never** overwritten by factory sync |
| `vectors.db` | similarity pipeline | vector_blob table (artist_mbid, kind, blob) | built in-place by the pipeline |

**Core rule:** all layer DBs except `user.db` are factory-built, read-only at sync time.
Sync = file swap, `user.db` untouched.

**Rationale for ATTACH (not one big DB):** rebuilds are per-layer, one bad import does
not lock the whole cluster; a rebuild of `ab.db` does not require re-linking artists;
sync file swaps are atomic per file.


## 3. Phase 0a: multi-DB plumbing (unblocks everything)

**1. `backend/app/common/layers.py`** (new):
- `LAYER_CONFIG: dict[str, LayerDefinition]` with `name`, `filename`, `readonly`,
  `owner`, `description`.
- `open_layer(layer: str, *, readonly: bool = False, attach: bool = False)` → aiosqlite
  or sqlite3 Connection with `ATTACH` for all other layer DBs when `attach=True`.
- `open_all_layers(readonly=True)` → one Connection with every layer ATTACHed.
- `user.db` is the only writable-at-runtime layer. All other layers are opened readonly
  by the API at runtime (enforce `PRAGMA query_only`).

**2. `backend/app/config.py` changes**:
- `data_root: Path = backend/data/` field (env override `MUSICLAB_DATA_ROOT`).
- `layer_paths: dict[str, Path]` derived from `data_root` + `LAYER_CONFIG`.
- Keep `database_path` for backward compat (aliases `musiclab.db`).

**3. `backend/app/enrichment/layers.py`** (new):
- `import mathlib_exports`  re-exports of `open_layer`, `open_all_layers`,
  `LAYER_CONFIG`, `layer_path` from `backend/app/common/layers.py`.
- `layer_writable(layer: str)` runtime guard for scripts.
- `db_file_swap_rebuild(layer: str, builder: Callable[[], None], target: str)` 
  rebuild helper: build into `<target>.rebuild`, then os.replace onto the live file
  after `builder()` completes.

**4. `backend/app/user/__init__.py`** (new):
- `user.py`: user_artist, artist_track_user, search_history, user_settings.
- The user-layer is the only layer the API writes to. Scripts that want to write to it
  go through `layer_writable("user")` guard.

**5. `backend/scripts/rebuild_layers.py`** (new):
- Reads `LAYER_CONFIG`, one CLI arg `--layers a,b,c`, `--all`.
- Calls the layer's builder (import_* script), then `os.replace` onto the live file.
- Prints coverage at the end via `verify_import.py`.
- Allows `--dry-run` (print what it would rebuild, run nothing).

**6. `backend/app/user/__init__.py`** side note: `user.py` must be importable without the
API (no FastAPI deps) so the rebuild scripts can use it.

**7. tests**: `backend/tests/test_layers.py` 
- test `open_layer("core")` gives a live connection.
- test `open_layer("core", readonly=True)` enforces `query_only`.
- test `open_all_layers()` ATTACHes every file and can query across them.
- test `db_file_swap_rebuild()` does not corrupt the live file on failure.

**8. `backend/app/user/user.py`**:
- Re-exports of `search_history` + `user_settings` (via `backend/app/user`).


## 4. Phase 0b: homelab factory + sync + laptop swap

### Factory build scripts

| Script | Layer | Read | Write |
|---|---|---|---|
| `import_discogs.py` (existing) | core | discogs dumps | musiclab.db |
| `import_mb_spine.py` (new) | mb | MB artist/entity dump | mb.db |
| `import_mb_tags.py` (new) | mb | MB tag dump | mb.db |
| `link_mbids.py` (new) | mb | discogs artist_mbid + MB artist dump | mb.db (artist_mbid) |
| `import_acousticbrainz.py` (new) | ab | AB dumps (37.4GB) | ab.db |
| `import_listenbrainz.py` (new) | lb | LB dumps | lb.db |
| `scrape_everynoise.py` (new) | enao | everynoise HTTP | enao.db |
| `import_wikidata.py` (new) | wikidata | WD SPARQL dump | wikidata.db |
| `build_vectors.py` (new) | vectors | all layers | vectors.db |
| `verify_import.py` (existing, extend) | all | all layers | coverage JSON |

### Sync transport

Windows laptop is the primary target (verify on Windows first). Two transports:

- **Local sync** (same machine / same disk): `scripts/sync_layers.py --all` copies
  each layer file from `data_root` to the local `backend/data/` via `os.replace`.
- **Remote sync** (second machine, e.g. homelab NAS): `scripts/sync_layers.py --remote
  --host <host> --root <path> --layers a,b,c`  rsync over SSH (Windows uses OpenSSH
  bundled client), then `os.replace` locally.

`user.db` is **excluded from sync**. Every sync prints a coverage report via
`verify_import.py` for the touched layers.

### Homelab (Linux NAS)

Target: Linux NAS with `docker` + `docker compose`. The factory ships as
`docker-compose.yml` + `docker/factory.Dockerfile` (python image + uv + venvs).
Two services:

- `factory-build`: long-running build scripts (discogs, mb, ab, lb, enao, wikidata,
  vectors), each with its own restart policy + a `build_state` JSON that tracks last
  success, coverage, row counts, and a state file per layer.
- `factory-sync`: runs `sync_layers.py --remote` on a schedule (cron-style) into a
  NAS-side `data_root`, then `os.replace` onto the NAS-side `backend/data`.

Note: the NAS writes to its own `backend/data`  the laptop never reads the NAS
`backend/data` directly. The NAS is a publisher (or a remote sync source); the laptop
is the consumer via `sync_layers.py --remote`.

### `user.db` isolation test

- `scripts/sync_layers.py` + tests: `test_sync_layers.py` 
  - test sync excludes `user.db`.
  - test `os.replace` path is atomic (live file not corrupted mid-swap).
  - test `--dry-run` does not move anything.


## 5. Phase 0c: MB spine + linker + tags + genre

### `import_mb_spine.py`

Reuses the existing `import_musicbrainz.py` parser (`import_musicbrainz.py` is the
working MB importer; do not rewrite it). New script `import_mb_spine.py`:

- Reads the MB artist dump.
- Writes `mb.db`: `artist_mbid` (source discogs/mb dump), `mb_artist` (mbid, name,
  discogs_id, mb_artist_id, discogs_name), `mb_artist_tag`, `mb_artist_genre`,
  `mb_release`, `mb_recording`.
- Ends by invoking `link_mbids.py` (see below).

### `link_mbids.py`

Reuses `import_musicbrainz.py` helpers. Writes `mb.db`:

- `mb_artist.mbid`  matched discogs id → MB id.
- `mb_artist.mbid_source`  `discogs`, `mb`.
- `mb_artist.mbid` is the **primary key for the layer**; `mb_artist.discogs_id` is the
  join key back into `musiclab.db` (`artist.discogs_id`).

Cover rows are `mb_artist` (discogs side). Matched rows carry `discogs_id = mb_artist_id`.

- **MB side data**: `mb_artist` carries `name`, `mbid`, `discogs_id`, `discogs_name`,
  `disambiguation`, `type`, `country`, `begin_date`, `end_date`, `aliases`, `real_name`,
  `isni`, `ipi`.
- **Discogs side data**: `artist_mbid` in `musiclab.db` (created by `link_mbids.py` via
  `mb.db` import)  this is the primary column the app reads at runtime.

### `import_mb_tags.py`

- Reads the MB tag dump (tags.csv from the MB tag import).
- Writes `mb.db`: `mb_tag` (tags.csv), `mb_artist_tag` (artist_tag.csv),
  `mb_artist_genre` (artist_genre.csv), `mb_release_tag`, `mb_release_genre`,
  `mb_recording_tag` (if the tag dump has recording-level tags).

### `enao` (EveryNoise)

`scrape_everynoise.py`: reads everynoise.com genre pages. Writes `enao.db`:
- `enao_genre(genre_key, genre_name, xy_x, xy_y, color, exemplar_artist_keys)`
- `enao_genre_artist(genre_key, artist_key, rank)`

### Wikidata

`import_wikidata.py`: reads the WD SPARQL dump (via SPARQL query or WD dumps). Writes
`wikidata.db`:
- `wd_qid(artist_mbid, wd_qid)`
- `wd_artist(wd_qid, name, origin_country, formed_year, genres, labels, members,
  member_mbid, image_url)`

### Discogs genres (Discogs release styles)

`musiclab.db` has `discogs_styles` (623 styles) + `taxonomy` release → styles. This is
already the genre backbone for the app. EveryNoise is the x/y 2D map + exemplar list
for genre pages. Wikidata genres are a smaller subset (broad-genre only).

### How the app reads genres at runtime

- Primary: `discogs_styles` (from `musiclab.db`).
- EveryNoise page view (genre map page) reads `enao.db`.
- Wikidata genres are only used for the artist page detail view (broad-genre only).


## 6. Phase 1: artist_mbid linker + verify_import coverage

### Linker (in mb.db, but the runtime column is in musiclab.db)

`musiclab.db.artist_mbid` is what the app reads. The linker writes it in two steps:

1. `import_mb_spine.py` writes `mb.db` (discogs-side rows: `mb_artist.discogs_id` →
   `mb_artist.mbid`), then invokes `link_mbids.py`.
2. `link_mbids.py` reads `mb.db.mb_artist`, matches on `discogs_id`, and writes
   `musiclab.db.artist_mbid` (join key: `artist.discogs_id`).

So the app reads `musiclab.db.artist_mbid` at runtime and joins into `mb.db` via
`mb_artist.mbid`. **`mb.db` is the only layer that has MB IDs; every other layer joins
into it via `mb_artist.mbid` / `mb_release.mbid` / `mb_recording.mbid`.**

### verify_import.py coverage

`verify_import.py` outputs a coverage JSON for every layer:

| Layer | Metric |
|---|---|
| core | artists, releases, taxonomy rows, credits rows, discogs_styles rows |
| mb | mb_artist rows, mb_release rows, mb_recording rows, mb_tag rows, linker coverage (% artists with mbid) |
| ab | ab_recording_features rows, ab_artist_profile rows, % artists with acoustic profile |
| lb | lb_user_artist rows, artist_popularity rows, artist_colisten rows, % artists with popularity |
| enao | enao_genre rows, enao_genre_artist rows, % artists with ENAO genre |
| wikidata | wd_artist rows, % artists with WD QID |
| vectors | vector_blob rows by kind, % artists with each vector kind |

`rebuild_layers.py` prints this coverage JSON after each rebuild so the operator knows
exactly how far each layer got.

### Artist ID runtime map

At runtime the app joins layers via `musiclab.db.artist_mbid` → `mb.db.mb_artist.mbid`.
The other layers all key on MBID:
- `ab.db.ab_artist_profile.artist_mbid`
- `lb.db.artist_popularity.artist_mbid`
- `enao.db.enao_genre_artist.artist_mbid`
- `wikidata.db.wd_artist.artist_mbid`
- `vectors.db.vector_blob.artist_mbid`

### Discogs master releases (Discogs is the release backbone)

`musiclab.db` carries `master_releases` + `releases` (the Discogs dump) + `taxonomy`
(release → styles) + `credits` (release → artist/role). The MB `mb_release` layer is a
smaller subset: only releases that map to `master_releases` (MB release ID join into
`musiclab.db.releases.discogs_master_id`). Every other release-level layer (AB, LB)
joins via `mb_release.mbid`.

### Every layer is a rebuild target

Any layer can be rebuilt independently. The only rule: **the `musiclab.db` core rebuild
does not lock the other layers**  an artist MIGHT be rebuilt with a new discogs ID but
the other layers keep their MBIDs.

