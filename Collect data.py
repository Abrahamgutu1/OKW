"""
PIPE_VISION_AI — Step 1: Data Collection Pipeline
Exports labeled inspection photos from Oracle 23ai into a structured
dataset directory ready for model training.

Run: python3 collect_data.py
"""

import os
import base64
import json
import shutil
from datetime import datetime
from pathlib import Path

import oracledb

# ── Config ─────────────────────────────────────────────────────────────────────
DB_USER   = "system"
DB_PASS   = "Awesomekid123"
DB_DSN    = "localhost:1521/FREEPDB1"

DATASET_DIR = os.path.expanduser("~/Desktop/OKW FieldSync/PipeVisionDataset")

# ODEQ four-tier label mapping
LABEL_MAP = {
    "MANUALLY_CONFIRMED_LEAD":  "LEAD",
    "MANUALLY_CONFIRMED_SAFE":  "NON_LEAD",
    "UNVERIFIED":               None,   # skip unverified
}

# ── Directory structure ────────────────────────────────────────────────────────
# PipeVisionDataset/
#   images/
#     LEAD/        ← confirmed lead pipe photos
#     NON_LEAD/    ← confirmed safe/non-lead photos
#     GRR/         ← galvanized requiring replacement
#     UNKNOWN/     ← cannot determine
#   manifest.json  ← full metadata for every image
#   stats.json     ← dataset statistics

def setup_dirs():
    classes = ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]
    for cls in classes:
        Path(os.path.join(DATASET_DIR, "images", cls)).mkdir(parents=True, exist_ok=True)
    print(f"Dataset directory: {DATASET_DIR}")

def load_manifest():
    path = os.path.join(DATASET_DIR, "manifest.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"version": "1.0", "created": datetime.now().isoformat(),
            "images": [], "class_counts": {}}

def save_manifest(manifest):
    path = os.path.join(DATASET_DIR, "manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

def export_from_oracle(manifest):
    """Pull all verified records with photos from Oracle."""
    print("\nConnecting to Oracle 23ai…")
    conn   = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            EVIDENCE_ID,
            SERVICE_LINE_ID,
            PHOTO_URL,
            GPS_LATITUDE,
            GPS_LONGITUDE,
            USER_VERIFIED_STATUS,
            AUDITED_BY,
            UPLOAD_DATE
        FROM EVIDENCE
        WHERE USER_VERIFIED_STATUS IN (
            'MANUALLY_CONFIRMED_LEAD',
            'MANUALLY_CONFIRMED_SAFE'
        )
        AND PHOTO_URL IS NOT NULL
        ORDER BY EVIDENCE_ID
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Found {len(rows)} labeled records in Oracle.")
    return rows

def decode_photo_from_url(photo_url, evidence_id):
    """Load photo from file:// URL or http URL."""
    try:
        if photo_url.startswith("file://"):
            path = photo_url.replace("file://", "")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return f.read()
        elif photo_url.startswith("http"):
            import urllib.request
            with urllib.request.urlopen(photo_url, timeout=10) as r:
                return r.read()
    except Exception as e:
        print(f"  [WARN] Could not load photo for EV-{evidence_id}: {e}")
    return None

def process_rows(rows, manifest):
    """Save each labeled photo to the correct class directory."""
    existing_ids = {img["evidence_id"] for img in manifest["images"]}
    new_count = 0

    for row in rows:
        ev_id, sl_id, photo_url, lat, lon, status, auditor, upload_date = row

        if ev_id in existing_ids:
            continue  # already in dataset

        label = LABEL_MAP.get(status)
        if not label:
            continue

        photo_data = decode_photo_from_url(photo_url, ev_id)
        if not photo_data:
            continue

        # Save image
        filename  = f"EV{ev_id}_SL{sl_id}_{label}.jpg"
        dest_path = os.path.join(DATASET_DIR, "images", label, filename)
        with open(dest_path, "wb") as f:
            f.write(photo_data)

        # Add to manifest
        manifest["images"].append({
            "evidence_id":    ev_id,
            "service_line_id": sl_id,
            "filename":       filename,
            "label":          label,
            "class_path":     f"images/{label}/{filename}",
            "gps_latitude":   float(lat) if lat else None,
            "gps_longitude":  float(lon) if lon else None,
            "audited_by":     auditor,
            "source":         "oracle_verified",
            "added_at":       datetime.now().isoformat(),
        })

        new_count += 1
        print(f"  + EV-{ev_id} → {label}")

    return new_count

def add_manual_image(image_path, label, manifest, notes=""):
    """Add a manually labeled photo to the dataset."""
    valid_labels = ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]
    if label not in valid_labels:
        print(f"Invalid label. Must be one of: {valid_labels}")
        return False

    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return False

    import hashlib
    with open(image_path, "rb") as f:
        data = f.read()
    file_hash = hashlib.md5(data).hexdigest()[:10]

    ext      = Path(image_path).suffix.lower() or ".jpg"
    filename = f"manual_{file_hash}_{label}{ext}"
    dest     = os.path.join(DATASET_DIR, "images", label, filename)
    shutil.copy2(image_path, dest)

    manifest["images"].append({
        "evidence_id":    None,
        "filename":       filename,
        "label":          label,
        "class_path":     f"images/{label}/{filename}",
        "source":         "manual",
        "notes":          notes,
        "added_at":       datetime.now().isoformat(),
    })
    print(f"  + Added {filename} → {label}")
    return True

def print_stats(manifest):
    counts = {}
    for img in manifest["images"]:
        cls = img["label"]
        counts[cls] = counts.get(cls, 0) + 1

    total = sum(counts.values())
    print("\n" + "="*50)
    print("  PIPE_VISION_AI Dataset Statistics")
    print("="*50)
    print(f"  Total labeled images: {total}")
    print(f"  Target for training:  500+ per class")
    print()
    for cls in ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]:
        count = counts.get(cls, 0)
        pct   = min(100, int((count / 500) * 100))
        bar   = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"  {cls:<10} {count:>4}/500  [{bar}] {pct}%")
    print()

    if total < 100:
        print("  ⚠  Need more data before training.")
        print("  → Partner with a utility to collect labeled field photos.")
    elif total < 500:
        print("  ⚡ Enough for a pilot model — accuracy will be limited.")
        print("  → Run: python3 train_model.py --mode pilot")
    else:
        print("  ✅ Ready for full model training.")
        print("  → Run: python3 train_model.py --mode full")

def main():
    print("PIPE_VISION_AI Data Collection Pipeline")
    print("OKW FieldSync — Oracle 23ai → Training Dataset")
    print("=" * 50)

    setup_dirs()
    manifest = load_manifest()

    # Export from Oracle
    try:
        rows     = export_from_oracle(manifest)
        new_imgs = process_rows(rows, manifest)
        print(f"\nExported {new_imgs} new images from Oracle.")
    except Exception as e:
        print(f"\n[WARN] Oracle export failed: {e}")
        print("Run with Oracle running. Manual images can still be added.")

    save_manifest(manifest)
    print_stats(manifest)

if __name__ == "__main__":
    main()