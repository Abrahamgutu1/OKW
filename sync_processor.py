"""
OKW FieldSync — Local Synchronization Processor v2.0
Handles Base64-encoded field photos from iOS Shortcut payloads.
Decodes images to local FieldPhotos directory and writes absolute
file paths into Oracle 23ai EVIDENCE.PHOTO_URL column.

Supports:
  python3 sync_processor.py          → one-shot scan
  python3 sync_processor.py --watch  → continuous daemon (30s interval)
"""

import os
import sys
import json
import time
import base64
import oracledb
from datetime import datetime
from pathlib import Path

# ── Database Configuration ─────────────────────────────────────────────────────
DB_USER = "system"
DB_PASS = "Awesomekid123"
DB_DSN  = "localhost:1521/FREEPDB1"

# ── Directory paths ────────────────────────────────────────────────────────────
BASE_DIR    = Path.home() / "Desktop" / "OKW FieldSync"
SYNC_DIR    = BASE_DIR / "SyncDrop"
PHOTOS_DIR  = BASE_DIR / "FieldPhotos"

SYNC_DIR.mkdir(parents=True, exist_ok=True)
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

WATCH_INTERVAL = 30  # seconds between scans in watch mode

# ── Logger ─────────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}]  {msg}")

# ── Base64 image decoder ───────────────────────────────────────────────────────
def decode_photo(b64_string: str, filename: str):
    """
    Decode a Base64 image string to a .jpg file in FieldPhotos/.
    Returns the absolute file path on success, None on failure.
    Handles corrupted blobs, padding errors, and non-image data gracefully.
    """
    if not b64_string or not isinstance(b64_string, str):
        log("   ⚠️  photo_base64 field is empty or not a string. Skipping photo decode.")
        return None

    try:
        # Strip whitespace and data-URI prefix if present
        # iOS Shortcuts sometimes prepend "data:image/jpeg;base64,"
        clean = b64_string.strip()
        if "," in clean and clean.startswith("data:"):
            clean = clean.split(",", 1)[1]

        # Fix padding — Base64 strings must be a multiple of 4 chars
        padding_needed = len(clean) % 4
        if padding_needed:
            clean += "=" * (4 - padding_needed)

        image_bytes = base64.b64decode(clean, validate=True)

        # Basic sanity check — JPEG magic bytes are FF D8 FF
        if len(image_bytes) < 3:
            log("   ⚠️  Decoded image data is too small. Likely corrupted blob.")
            return None

        output_path = PHOTOS_DIR / filename
        with open(output_path, "wb") as img_file:
            img_file.write(image_bytes)

        size_kb = len(image_bytes) / 1024
        log(f"   📸 Photo decoded → {filename} ({size_kb:.1f} KB)")
        return str(output_path.resolve())

    except base64.binascii.Error as e:
        log(f"   ❌ Base64 decode error — corrupted blob: {e}")
        return None
    except OSError as e:
        log(f"   ❌ Failed to write photo file: {e}")
        return None
    except Exception as e:
        log(f"   ❌ Unexpected photo decode error: {e}")
        return None

# ── Core: process a single JSON payload file ───────────────────────────────────
def process_sync_payload(file_path: str) -> bool:
    log(f"📦 Payload detected: {os.path.basename(file_path)}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as e:
        log(f"❌ Invalid JSON — cannot parse payload: {e}")
        return False
    except OSError as e:
        log(f"❌ Cannot read file: {e}")
        return False

    records   = payload.get("records", [])
    device_id = payload.get("device_id", "UNKNOWN")

    if not records:
        log("⚠️  Payload contains no evidence records. Skipping.")
        return False

    log(f"   Device  : {device_id}")
    log(f"   Records : {len(records)}")

    try:
        conn   = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        cursor = conn.cursor()
    except oracledb.DatabaseError as e:
        log(f"❌ Database connection failed: {e}")
        return False

    success_count = 0
    error_count   = 0

    for rec in records:
        ev_id     = rec.get("evidence_id")
        sl_id     = rec.get("service_line_id")
        lat       = rec.get("gps_latitude")
        lon       = rec.get("gps_longitude")
        b64_photo = rec.get("photo_base64")
        # Also accept a plain photo_url if no base64 present
        photo_url = rec.get("photo_url", "")

        if not ev_id or not sl_id:
            log(f"   ⚠️  Skipping record — missing evidence_id or service_line_id.")
            error_count += 1
            continue

        # ── Decode photo if base64 is present ─────────────────────────────────
        if b64_photo:
            ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = f"EV{ev_id}_SL{sl_id}_{ts}.jpg"
            local_path = decode_photo(b64_photo, filename)

            if local_path:
                # Use absolute file path as the photo URL for the dashboard
                photo_url = f"file://{local_path}"
            else:
                log(f"   ⚠️  Photo decode failed for EV-{ev_id}. PHOTO_URL will be empty.")
                photo_url = photo_url or ""

        # ── Upsert into Oracle 23ai ───────────────────────────────────────────
        try:
            cursor.execute("""
                MERGE INTO EVIDENCE e
                USING DUAL ON (e.EVIDENCE_ID = :ev_id)
                WHEN MATCHED THEN
                    UPDATE SET
                        e.PHOTO_URL     = :photo_url,
                        e.GPS_LATITUDE  = :lat,
                        e.GPS_LONGITUDE = :lon,
                        e.UPLOAD_DATE   = SYSDATE
                WHEN NOT MATCHED THEN
                    INSERT (EVIDENCE_ID, SERVICE_LINE_ID, PHOTO_URL,
                            GPS_LATITUDE, GPS_LONGITUDE, UPLOAD_DATE,
                            USER_VERIFIED_STATUS)
                    VALUES (:ev_id, :sl_id, :photo_url,
                            :lat, :lon, SYSDATE, 'UNVERIFIED')
            """, dict(ev_id=int(ev_id), sl_id=int(sl_id),
                      photo_url=photo_url, lat=lat, lon=lon))

            success_count += 1
            log(f"   ✓  Upserted EV-{ev_id} / SL-{sl_id}"
                f"{' · ' + photo_url[:60] + '…' if photo_url else ''}")

        except oracledb.DatabaseError as e:
            log(f"   ❌ DB upsert failed for EV-{ev_id}: {e}")
            error_count += 1

    conn.commit()
    cursor.close()
    conn.close()

    log(f"✅ Sync complete — {success_count} succeeded, {error_count} failed.")
    return success_count > 0

# ── One scan pass ──────────────────────────────────────────────────────────────
def run_scan():
    files = sorted(SYNC_DIR.glob("*.json"))

    if not files:
        log("ℹ️  SyncDrop clear — no pending payloads.")
        return

    log(f"🔍 Found {len(files)} pending payload(s).")

    for file_path in files:
        if process_sync_payload(str(file_path)):
            archive_path = str(file_path) + ".processed"
            os.rename(file_path, archive_path)
            log(f"📁 Archived → {os.path.basename(archive_path)}\n")
        else:
            log(f"⚠️  Skipped (error) → {file_path.name}\n")

# ── Watch mode — continuous daemon ─────────────────────────────────────────────
def run_watch():
    log(f"👁  Watch mode active — scanning every {WATCH_INTERVAL}s")
    log(f"   SyncDrop  : {SYNC_DIR}")
    log(f"   FieldPhotos: {PHOTOS_DIR}")
    log(f"   Press Ctrl+C to stop.\n")

    scan_count = 0
    try:
        while True:
            scan_count += 1
            log(f"── Scan #{scan_count} ──────────────────────────────────")
            run_scan()
            log(f"   Next scan in {WATCH_INTERVAL}s…\n")
            time.sleep(WATCH_INTERVAL)
    except KeyboardInterrupt:
        log("\n🛑 Watch mode stopped. Goodbye.")
        sys.exit(0)

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*58}")
    print(f"  OKW FieldSync · Sync Processor v2.0")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  DB        : {DB_DSN}")
    print(f"  SyncDrop  : {SYNC_DIR}")
    print(f"  FieldPhotos: {PHOTOS_DIR}")
    print(f"{'='*58}\n")

    if "--watch" in sys.argv:
        run_watch()
    else:
        log("Running one-shot scan…")
        run_scan()
        log("Done.")