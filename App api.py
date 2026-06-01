"""
OKW FieldSync — REST API Backend
Receives inspection records from iOS app and writes to Oracle 23ai
Run: python3 app_api.py
Port: 5001 (doesn't conflict with Streamlit on 8501 or Oracle on 1521)
"""

from flask import Flask, request, jsonify
import oracledb
import base64
import os
from datetime import datetime

app = Flask(__name__)

# ── Database config — matches okw_dashboard.py ─────────────────────────────────
DB_USER = "system"
DB_PASS = "Awesomekid123"
DB_DSN  = "localhost:1521/FREEPDB1"

# ── Photo storage directory ────────────────────────────────────────────────────
PHOTOS_DIR = os.path.expanduser("~/Desktop/OKW FieldSync/FieldPhotos")
os.makedirs(PHOTOS_DIR, exist_ok=True)


def decode_and_save_photo(base64_string, evidence_id, service_line_id):
    """Decode Base64 photo and save to FieldPhotos/. Returns file:// URL."""
    if not base64_string:
        return None
    try:
        # Strip data-URI prefix if iOS sent it
        clean = base64_string.strip()
        if "," in clean and clean.startswith("data:"):
            clean = clean.split(",", 1)[1]

        # Fix padding
        padding = len(clean) % 4
        if padding:
            clean += "=" * (4 - padding)

        image_bytes = base64.b64decode(clean, validate=True)

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"EV{evidence_id}_SL{service_line_id}_{ts}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return f"file://{os.path.abspath(filepath)}"

    except Exception as e:
        print(f"[WARN] Photo decode failed: {e}")
        return None


@app.route("/health", methods=["GET"])
def health():
    """Quick health check — use this to confirm API is reachable from iPhone."""
    return jsonify({
        "status": "ok",
        "service": "OKW FieldSync API",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/api/upload_inspection", methods=["POST"])
def upload_inspection():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error",
                            "message": "Missing JSON payload"}), 400

        # ── Extract fields from iOS payload ────────────────────────────────────
        service_line_id = data.get("service_line_id")
        evidence_id     = data.get("evidence_id")
        latitude        = data.get("latitude")
        longitude       = data.get("longitude")
        accuracy        = data.get("accuracy", 0.0)
        image_base64    = data.get("image_base64") or data.get("photo_base64")

        # ── Validate required fields ───────────────────────────────────────────
        if not service_line_id or not evidence_id:
            return jsonify({"status": "error",
                            "message": "Missing service_line_id or evidence_id"}), 400
        if latitude is None or longitude is None:
            return jsonify({"status": "error",
                            "message": "Missing GPS coordinates"}), 400

        # ── Decode photo → save to FieldPhotos/ ───────────────────────────────
        photo_url = decode_and_save_photo(image_base64,
                                          int(evidence_id),
                                          int(service_line_id))
        if not photo_url and image_base64:
            # If decode failed, store empty — don't block the record
            photo_url = ""

        # ── Write to Oracle 23ai via MERGE (upsert) ───────────────────────────
        conn   = oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)
        cursor = conn.cursor()

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
        """, dict(
            ev_id     = int(evidence_id),
            sl_id     = int(service_line_id),
            photo_url = photo_url or "",
            lat       = float(latitude),
            lon       = float(longitude)
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"[OK] EV-{evidence_id} / SL-{service_line_id} synced at {datetime.now():%H:%M:%S}")

        return jsonify({
            "status":   "success",
            "message":  f"EV-{evidence_id} synced to Oracle 23ai",
            "photo_url": photo_url or "no photo"
        }), 201

    except oracledb.DatabaseError as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("  OKW FieldSync API")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("  Listening on http://0.0.0.0:5001")
    print("  Health check: http://localhost:5001/health")
    print("  Upload endpoint: POST /api/upload_inspection")
    print("=" * 50)
    # 0.0.0.0 makes it reachable from iPhone on same WiFi
    app.run(host="0.0.0.0", port=5001, debug=True)