"""Downloader script for Discogs and MusicBrainz dumps to a specified directory."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import tarfile
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Direct URLs for latest dumps
DISCOGS_ARTISTS_URL = "https://data.discogs.com/?download=data%2F2026%2Fdiscogs_20260101_artists.xml.gz"
DISCOGS_RELEASES_URL = "https://data.discogs.com/?download=data%2F2026%2Fdiscogs_20260101_releases.xml.gz"


def get_latest_musicbrainz_url() -> str:
    """Fetch the latest MusicBrainz export folder name dynamically."""
    try:
        req = urllib.request.Request("https://data.metabrainz.org/pub/musicbrainz/data/fullexport/LATEST", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            latest_dir = resp.read().decode("utf-8").strip()
            if latest_dir:
                url = f"https://data.metabrainz.org/pub/musicbrainz/data/fullexport/{latest_dir}/mbdump.tar.bz2"
                logger.info(f"Resolved latest MusicBrainz URL: {url}")
                return url
    except Exception as e:
        logger.warning(f"Could not resolve dynamic MusicBrainz URL: {e}")
    # Fallback to hardcoded recent folder
    return "https://data.metabrainz.org/pub/musicbrainz/data/fullexport/20260801-002250/mbdump.tar.bz2"


def download_file(url: str, dest_path: Path, min_size_mb: int = 100) -> None:
    """Download a file with progress logging, skipping if file already exists and is complete."""
    if dest_path.exists() and dest_path.stat().st_size > min_size_mb * 1024 * 1024:
        logger.info(f"File already exists ({dest_path.stat().st_size / 1048576:.1f} MB), skipping: {dest_path.name}")
        return

    logger.info(f"Starting download: {url} -> {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    def progress_callback(blocks_transferred, block_size, total_size):
        if total_size > 0:
            downloaded = blocks_transferred * block_size
            percent = downloaded / total_size * 100
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            sys.stdout.write(f"\rDownloading {dest_path.name}: {percent:.1f}% ({downloaded_mb:.1f} / {total_mb:.1f} MB)")
            sys.stdout.flush()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req) as response, open(tmp_path, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if total_size > 0:
                    percent = downloaded / total_size * 100
                    sys.stdout.write(f"\rDownloading {dest_path.name}: {percent:.1f}% ({downloaded / 1048576:.1f} / {total_size / 1048576:.1f} MB)")
                else:
                    sys.stdout.write(f"\rDownloading {dest_path.name}: {downloaded / 1048576:.1f} MB")
                sys.stdout.flush()

        sys.stdout.write("\n")
        tmp_path.rename(dest_path)
        logger.info(f"Successfully downloaded: {dest_path.name}")
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        logger.error(f"Failed to download {url}: {e}")
        raise


def extract_tar_bz2(archive_path: Path, extract_dir: Path) -> None:
    """Extract a tar.bz2 archive to destination folder."""
    if extract_dir.exists() and any(extract_dir.iterdir()):
        logger.info(f"Extraction directory already contains files, skipping: {extract_dir}")
        return

    logger.info(f"Extracting {archive_path.name} to {extract_dir}...")
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:bz2") as tar:
        tar.extractall(path=extract_dir)

    logger.info(f"Extraction complete: {extract_dir}")


def main():
    parser = argparse.ArgumentParser(description="Download Discogs and MusicBrainz dumps to target folder.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=r"D:\VibeCheck",
        help="Directory to save downloads and extracted files (default: D:\\VibeCheck)",
    )
    parser.add_argument("--skip-musicbrainz", action="store_true", help="Skip downloading MusicBrainz dump")
    parser.add_argument("--skip-discogs", action="store_true", help="Skip downloading Discogs dumps")

    args = parser.parse_args()
    target_dir = Path(args.output_dir)

    logger.info(f"Target download directory: {target_dir}")

    # Discogs downloads
    if not args.skip_discogs:
        discogs_artists = target_dir / "discogs_artists.xml.gz"
        discogs_releases = target_dir / "discogs_releases.xml.gz"

        download_file(DISCOGS_ARTISTS_URL, discogs_artists)
        download_file(DISCOGS_RELEASES_URL, discogs_releases)

    # MusicBrainz download & extract
    if not args.skip_musicbrainz:
        mb_archive = target_dir / "mbdump.tar.bz2"
        mb_extract = target_dir / "mbdump"

        mb_url = get_latest_musicbrainz_url()
        download_file(mb_url, mb_archive)
        extract_tar_bz2(mb_archive, mb_extract)

    logger.info("\n=== Download & Setup Complete ===")
    logger.info(f"All dump files are stored in: {target_dir}")
    logger.info("You can now run the import scripts pointing to this folder!")


if __name__ == "__main__":
    main()
