from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


# Folder name format: YYYY-MM-DD-HH-MM-SS
FOLDER_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})$")

# Only copy these files names (case-insensitive match)
TARGET_FILES = {"merged.jpg", "primary.jpg", "secondary.jpg","video.mp4"}


def parse_folder_datetime(folder_name: str, use_utc: bool = False) -> datetime:
    """
    Parse datetime from folder name like '2022-11-07-15-09-47'.
    Returns a timezone-aware datetime (UTC if use_utc=True, else local time zone naive->aware).
    """
    m = FOLDER_RE.match(folder_name)
    if not m:
        raise ValueError(f"Folder name does not match pattern YYYY-MM-DD-HH-MM-SS: {folder_name}")

    y, mo, d, h, mi, s = map(int, m.groups())
    dt = datetime(y, mo, d, h, mi, s)

    # Filesystem timestamps are epoch-based; interpret dt either as local time or UTC.
    if use_utc:
        return dt.replace(tzinfo=timezone.utc)

    # Local-time interpretation: store tz-aware using local offset at runtime.
    # This avoids guessing DST rules manually.
    local_tz = datetime.now().astimezone().tzinfo
    return dt.replace(tzinfo=local_tz)


def ensure_unique_path(dest_path: Path) -> Path:
    """
    If dest_path exists, append -N before the suffix to avoid overwriting.
    """
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent

    i = 1
    while True:
        candidate = parent / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def set_fs_times(path: Path, dt: datetime) -> None:
    """
    Set filesystem access/modification time (atime/mtime) to dt.
    """
    ts = dt.timestamp()
    os.utime(path, (ts, ts))


def update_exif_datetime(path: Path, dt: datetime) -> bool:
    """
    Optional: Update EXIF DateTime tags (DateTimeOriginal, DateTimeDigitized, DateTime).
    Returns True if updated, False if piexif not installed or operation failed.
    """
    try:
        import piexif  # pip install piexif
    except ImportError:
        return False

    try:
        exif_dict = piexif.load(str(path))
        exif_str = dt.strftime("%Y:%m:%d %H:%M:%S").encode("ascii")

        # 0th IFD: DateTime
        exif_dict.setdefault("0th", {})
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_str

        # Exif IFD: DateTimeOriginal + DateTimeDigitized
        exif_dict.setdefault("Exif", {})
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_str
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_str

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, str(path))
        return True
    except Exception:
        return False


def main(
    source_dir: Path,
    dest_dir: Path,
    *,
    use_utc: bool = False,
    write_exif: bool = False,
) -> None:
    source_dir = source_dir.resolve()
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    if not source_dir.is_dir():
        raise SystemExit(f"Source directory does not exist or is not a directory: {source_dir}")

    copied = 0
    skipped = 0

    for entry in sorted(source_dir.iterdir()):
        if not entry.is_dir():
            continue

        folder_name = entry.name
        if not FOLDER_RE.match(folder_name):
            skipped += 1
            continue

        try:
            dt = parse_folder_datetime(folder_name, use_utc=use_utc)
        except ValueError:
            skipped += 1
            continue

        for child in entry.iterdir():
            if not child.is_file():
                continue

            if child.name.lower() not in TARGET_FILES:
                continue

            new_name = f"{folder_name}-{child.name}"
            out_path = ensure_unique_path(dest_dir / new_name)

            # Copy file contents + metadata (we will overwrite timestamps afterward)
            shutil.copy2(child, out_path)

            # Set filesystem time based on folder datetime
            set_fs_times(out_path, dt)

            # Optionally update EXIF tags as well
            if write_exif:
                updated = update_exif_datetime(out_path, dt)
                if not updated:
                    # Not fatal; EXIF update is best-effort
                    pass

            copied += 1

    print(f"Done. Copied: {copied}, Skipped folders (non-matching pattern): {skipped}")
    print(f"Output folder: {dest_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect merged/primary/secondary JPGs into one folder and fix timestamps based on folder name."
    )
    parser.add_argument("source", help="Source directory containing timestamp-named subfolders.")
    parser.add_argument("dest", help="Destination directory to receive renamed images.")
    parser.add_argument(
        "--utc",
        action="store_true",
        help="Interpret folder datetime as UTC (default: interpret as local time).",
    )
    parser.add_argument(
        "--exif",
        action="store_true",
        help="Also write EXIF datetime tags (requires: pip install piexif).",
    )

    args = parser.parse_args()
    main(Path(args.source), Path(args.dest), use_utc=args.utc, write_exif=args.exif)
