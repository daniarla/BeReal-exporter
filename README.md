# BeReal Image Date Corrector

This script reformats the export from [BeReal GDPR Explorer](https://berealgdprviewer.eu/) so it can be cleanly integrated into a local photo backup or archive.

The BeReal GDPR Explorer exports images in a folder-per-post structure that is **not suitable for most photo libraries**. This script converts that structure into a single flat folder, with correctly named files and embedded timestamps.

If you also want to correct the **Windows “Date Created”** field, use [Bulk Rename Utility](https://www.bulkrenameutility.co.uk/) after running this script.

---

## What the script does

Given a directory structure like:

```
bereal-memories-all/
├── 2022-11-07-15-09-47/
│   ├── merged.jpg
│   ├── primary.jpg
│   └── secondary.jpg
├── 2022-11-08-09-31-12/
│   ├── merged.jpg
│   ├── primary.jpg
│   └── secondary.jpg
```

The script will:

1. Copy all images into **one output folder**
2. Rename each image to include the folder timestamp  
   Example:

```
2022-11-07-15-09-47-merged.jpg
```

3. Fix filesystem timestamps (modified / accessed)
4. **Optionally** embed correct EXIF metadata (`Date Taken`)

---

## Folder name format (required)

Each subfolder **must** follow this exact pattern:

```
YYYY-MM-DD-HH-MM-SS
```

Example:

```
2022-11-07-15-09-47
```

Folders that do not match this format are skipped.

---

## Supported image names

Only the following files are copied (case-insensitive):

- `merged.jpg`
- `primary.jpg`
- `secondary.jpg`

All other files are ignored.

---

## Requirements

- Python **3.9+**
- Optional (recommended): `piexif` for EXIF metadata

Install EXIF support:

```bash
pip install piexif
```

---

## Usage

### Basic usage (filesystem timestamps only)

```bash
python bereal-date-correcter.py "SOURCE_FOLDER" "DESTINATION_FOLDER"
```

Example (Windows):

```bash
python bereal-date-correcter.py ^
  "C:\Users\vukan\Desktop\bereal-memories-all" ^
  "C:\Users\vukan\Desktop\bereal-final"
```

### Also fix EXIF metadata (recommended)

```bash
python bereal-date-correcter.py "SOURCE" "DEST" --exif
```

This updates:

- `DateTimeOriginal`
- `DateTimeDigitized`
- `DateTime`

Required for correct sorting in:

- Windows Photos
- Google Photos
- Lightroom
- macOS Photos

### Treat folder timestamps as UTC

```bash
python bereal-date-correcter.py "SOURCE" "DEST" --utc
```

Use this only if the timestamps were generated in UTC (e.g. server-side exports).

### Combine both options

```bash
python bereal-date-correcter.py "SOURCE" "DEST" --exif --utc
```

---

## Notes

- Windows does **not** allow reliable modification of the “Date Created” field via Python
- Files are never overwritten; name collisions are resolved automatically
- EXIF writing is skipped gracefully if `piexif` is not installed
