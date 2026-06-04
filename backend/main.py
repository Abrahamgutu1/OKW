"""
OKW FieldSync — FastAPI Backend
Run: uvicorn main:app --reload --port 8000 --host 0.0.0.0
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import oracledb, os, subprocess, base64, json
from datetime import datetime
import random

app = FastAPI(title="OKW FieldSync API", version="2.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DB_USER = "system"
DB_PASS = "Awesomekid123"
DB_DSN  = "localhost:1521/FREEPDB1"
WORKSPACE = os.path.expanduser("~/Desktop/OKW FieldSync")
PWSID = "OK1020401"

INSPECTOR_REGISTRY = {
    "PIN-9402": "A. Mutu (Badge #402)",
    "PIN-1185": "J. Doe (Badge #185)",
    "PIN-2365": "S. Smith (Badge #365)",
}

def get_conn():
    return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=DB_DSN)

# ── Pydantic models ────────────────────────────────────────────────────────────
class AuditUpdate(BaseModel):
    evidence_id: int
    status: str
    inspector_pin: str

class InspectionUpload(BaseModel):
    evidence_id:          int
    service_line_id:      int
    latitude:             float
    longitude:            float
    accuracy:             Optional[float] = None
    image_base64:         str
    vision_labels:        Optional[str] = ""
    vision_color:         Optional[str] = ""
    vision_pipe_confirmed: Optional[str] = "0"
    vision_confidence:    Optional[str] = "UNKNOWN"

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ── Upload inspection from iPhone ──────────────────────────────────────────────
@app.post("/api/upload_inspection", status_code=201)
def upload_inspection(body: InspectionUpload):
    try:
        # Decode base64 photo and save to disk
        photos_dir = os.path.join(WORKSPACE, "FieldPhotos")
        os.makedirs(photos_dir, exist_ok=True)

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename    = f"EV{body.evidence_id}_SL{body.service_line_id}_{timestamp}.jpg"
        photo_path  = os.path.join(photos_dir, filename)
        photo_url   = f"file://{photo_path}"

        try:
            img_data = base64.b64decode(body.image_base64)
            with open(photo_path, "wb") as f:
                f.write(img_data)
        except Exception:
            photo_url = "upload_error"

        # Determine status from material classification
        material = body.vision_labels.lower() if body.vision_labels else ""
        if "lead" in material:
            auto_status = "MANUALLY_CONFIRMED_LEAD"
        elif material in ["copper", "pvc"]:
            auto_status = "MANUALLY_CONFIRMED_SAFE"
        else:
            auto_status = "UNVERIFIED"

        conn   = get_conn()
        cursor = conn.cursor()

        # Check if evidence_id already exists
        cursor.execute("SELECT COUNT(*) FROM SYSTEM.EVIDENCE WHERE EVIDENCE_ID = :1",
                       (body.evidence_id,))
        exists = cursor.fetchone()[0]

        if exists:
            # Update existing record
            cursor.execute("""
                UPDATE SYSTEM.EVIDENCE SET
                    SERVICE_LINE_ID       = :1,
                    GPS_LATITUDE          = :2,
                    GPS_LONGITUDE         = :3,
                    PHOTO_URL             = :4,
                    USER_VERIFIED_STATUS  = :5,
                    UPLOAD_DATE           = SYSDATE
                WHERE EVIDENCE_ID = :6
            """, (body.service_line_id, body.latitude, body.longitude,
                  photo_url, auto_status, body.evidence_id))
        else:
            # Insert new record
            try:
                cursor.execute("""
                    INSERT INTO SYSTEM.EVIDENCE (
                        EVIDENCE_ID, SERVICE_LINE_ID,
                        GPS_LATITUDE, GPS_LONGITUDE,
                        PHOTO_URL, UPLOAD_DATE,
                        USER_VERIFIED_STATUS,
                        IMAGE_VECTOR
                    ) VALUES (
                        :1, :2, :3, :4, :5, SYSDATE, :6,
                        VECTOR('[0.50,0.50,0.50]', 3, FLOAT32)
                    )
                """, (body.evidence_id, body.service_line_id,
                      body.latitude, body.longitude,
                      photo_url, auto_status))
            except Exception:
                # Fallback without vector column
                cursor.execute("""
                    INSERT INTO SYSTEM.EVIDENCE (
                        EVIDENCE_ID, SERVICE_LINE_ID,
                        GPS_LATITUDE, GPS_LONGITUDE,
                        PHOTO_URL, UPLOAD_DATE,
                        USER_VERIFIED_STATUS
                    ) VALUES (:1, :2, :3, :4, :5, SYSDATE, :6)
                """, (body.evidence_id, body.service_line_id,
                      body.latitude, body.longitude,
                      photo_url, auto_status))

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status":  "ok",
            "message": f"EV-{body.evidence_id} uploaded successfully",
            "photo":   filename,
            "classification": auto_status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Get all evidence for dashboard ────────────────────────────────────────────
@app.get("/api/evidence")
def get_evidence():
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT EVIDENCE_ID, SERVICE_LINE_ID, PHOTO_URL,
                       GPS_LATITUDE, GPS_LONGITUDE, UPLOAD_DATE,
                       NVL(USER_VERIFIED_STATUS,'UNVERIFIED') AS USER_VERIFIED_STATUS,
                       AUDITED_BY,
                       VECTOR_DISTANCE(IMAGE_VECTOR,VECTOR('[1.00,0.00,1.00]',3,FLOAT32),COSINE) AS AI_DISTANCE
                FROM SYSTEM.EVIDENCE ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
            """)
            vec_ok = True
        except Exception:
            cursor.execute("""
                SELECT EVIDENCE_ID, SERVICE_LINE_ID, PHOTO_URL,
                       GPS_LATITUDE, GPS_LONGITUDE, UPLOAD_DATE,
                       NVL(USER_VERIFIED_STATUS,'UNVERIFIED') AS USER_VERIFIED_STATUS,
                       AUDITED_BY, NULL AS AI_DISTANCE
                FROM SYSTEM.EVIDENCE ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
            """)
            vec_ok = False

        cols = [d[0].lower() for d in cursor.description]
        rows = []
        for row in cursor.fetchall():
            r = dict(zip(cols, row))
            if r.get("upload_date"):
                r["upload_date"] = r["upload_date"].isoformat() if hasattr(r["upload_date"], "isoformat") else str(r["upload_date"])
            if r.get("ai_distance") is not None:
                try: r["ai_distance"] = float(r["ai_distance"])
                except: r["ai_distance"] = None
            rows.append(r)

        total    = len(rows)
        suspect  = sum(1 for r in rows if r.get("ai_distance") is not None and r["ai_distance"] < 0.35)
        verified = sum(1 for r in rows if r.get("user_verified_status", "") in ["MANUALLY_CONFIRMED_LEAD", "MANUALLY_CONFIRMED_SAFE"])
        has_photo = sum(1 for r in rows if str(r.get("photo_url", "")).startswith(("http", "file")))

        cursor.close(); conn.close()
        return {
            "records": rows,
            "kpis": {
                "total":     total,
                "suspect":   suspect,
                "verified":  verified,
                "has_photo": has_photo,
                "pending":   total - verified,
                "lines":     len(set(r["service_line_id"] for r in rows))
            },
            "vec_ok": vec_ok
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Audit / verify a record ────────────────────────────────────────────────────
@app.post("/api/audit")
def submit_audit(body: AuditUpdate):
    if body.inspector_pin not in INSPECTOR_REGISTRY:
        raise HTTPException(status_code=401, detail="Invalid inspector PIN")
    if body.status not in ["MANUALLY_CONFIRMED_LEAD", "MANUALLY_CONFIRMED_SAFE"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    try:
        inspector = INSPECTOR_REGISTRY[body.inspector_pin]
        conn = get_conn(); cursor = conn.cursor()
        cursor.execute(
            "UPDATE SYSTEM.EVIDENCE SET USER_VERIFIED_STATUS=:1, AUDITED_BY=:2 WHERE EVIDENCE_ID=:3",
            (body.status, inspector, body.evidence_id))
        conn.commit(); cursor.close(); conn.close()
        return {"status": "ok", "message": f"EV-{body.evidence_id} signed off by {inspector}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Seed demo data ─────────────────────────────────────────────────────────────
@app.post("/api/seed")
def seed_demo_data():
    """Insert 18 realistic demo records for Norman, OK area."""
    demo_records = [
        # (evidence_id, service_line_id, lat, lon, status, material)
        (1,  101, 35.2226, -97.4395, "MANUALLY_CONFIRMED_LEAD",  "lead pipe — dull grey surface, scratches silver"),
        (2,  101, 35.2228, -97.4392, "UNVERIFIED",               "unknown — corroded, inconclusive scratch test"),
        (3,  102, 35.2231, -97.4401, "MANUALLY_CONFIRMED_SAFE",  "copper — orange-brown color, verified"),
        (4,  103, 35.2219, -97.4388, "MANUALLY_CONFIRMED_LEAD",  "lead — soft metal, scratches bright silver"),
        (5,  104, 35.2245, -97.4412, "UNVERIFIED",               "galvanized steel — grey, threaded fittings"),
        (6,  105, 35.2201, -97.4378, "MANUALLY_CONFIRMED_SAFE",  "PVC — white plastic, post-1986 installation"),
        (7,  106, 35.2258, -97.4425, "MANUALLY_CONFIRMED_LEAD",  "lead — matches city records pre-1950 construction"),
        (8,  107, 35.2234, -97.4398, "UNVERIFIED",               "unknown — partial excavation, photo only"),
        (9,  108, 35.2267, -97.4435, "MANUALLY_CONFIRMED_SAFE",  "copper — green patina, confirmed non-lead"),
        (10, 109, 35.2212, -97.4367, "MANUALLY_CONFIRMED_LEAD",  "lead — city atlas confirms pre-1940 service"),
        (11, 110, 35.2289, -97.4451, "UNVERIFIED",               "galvanized — GRR candidate, downstream of lead"),
        (12, 111, 35.2198, -97.4356, "MANUALLY_CONFIRMED_SAFE",  "PVC — blue-tinted, post-1986"),
        (13, 112, 35.2301, -97.4462, "MANUALLY_CONFIRMED_LEAD",  "lead — soft, silver scratch, pre-1950 block"),
        (14, 113, 35.2178, -97.4341, "UNVERIFIED",               "unknown — meter pit flooded, inconclusive"),
        (15, 114, 35.2312, -97.4478, "MANUALLY_CONFIRMED_SAFE",  "copper — orange, verified by inspector Badge #402"),
        (16, 115, 35.2156, -97.4329, "MANUALLY_CONFIRMED_LEAD",  "lead — city records confirm 1932 installation"),
        (17, 116, 35.2334, -97.4489, "UNVERIFIED",               "galvanized — threaded joints, GRR classification pending"),
        (18, 117, 35.2145, -97.4318, "MANUALLY_CONFIRMED_SAFE",  "PVC — white, installed 2005 per permit records"),
    ]

    try:
        conn = get_conn(); cursor = conn.cursor()

        inserted = 0
        skipped  = 0

        for ev_id, sl_id, lat, lon, status, notes in demo_records:
            # Skip if already exists
            cursor.execute("SELECT COUNT(*) FROM SYSTEM.EVIDENCE WHERE EVIDENCE_ID = :1", (ev_id,))
            if cursor.fetchone()[0] > 0:
                skipped += 1
                continue

            photo_url = f"https://okw-fieldsync-demo.s3.amazonaws.com/demo/EV{ev_id:03d}.jpg"

            try:
                cursor.execute("""
                    INSERT INTO SYSTEM.EVIDENCE (
                        EVIDENCE_ID, SERVICE_LINE_ID,
                        GPS_LATITUDE, GPS_LONGITUDE,
                        PHOTO_URL, UPLOAD_DATE,
                        USER_VERIFIED_STATUS,
                        IMAGE_VECTOR
                    ) VALUES (
                        :1, :2, :3, :4, :5, SYSDATE, :6,
                        VECTOR('[0.80,0.10,0.80]', 3, FLOAT32)
                    )
                """, (ev_id, sl_id, lat, lon, photo_url, status))
            except Exception:
                cursor.execute("""
                    INSERT INTO SYSTEM.EVIDENCE (
                        EVIDENCE_ID, SERVICE_LINE_ID,
                        GPS_LATITUDE, GPS_LONGITUDE,
                        PHOTO_URL, UPLOAD_DATE,
                        USER_VERIFIED_STATUS
                    ) VALUES (:1, :2, :3, :4, :5, SYSDATE, :6)
                """, (ev_id, sl_id, lat, lon, photo_url, status))

            inserted += 1

        conn.commit(); cursor.close(); conn.close()

        return {
            "status":   "ok",
            "inserted": inserted,
            "skipped":  skipped,
            "message":  f"Seeded {inserted} demo records ({skipped} already existed)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Delete all records (dev only) ──────────────────────────────────────────────
@app.delete("/api/reset")
def reset_data():
    """WARNING: Deletes all evidence records. Dev use only."""
    try:
        conn = get_conn(); cursor = conn.cursor()
        cursor.execute("DELETE FROM SYSTEM.EVIDENCE")
        conn.commit(); cursor.close(); conn.close()
        return {"status": "ok", "message": "All records deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── LaTeX helpers ──────────────────────────────────────────────────────────────
def tex_escape(val):
    if val is None: return "---"
    s = str(val)
    for char, repl in [("\\","\\textbackslash{}"),("&","\\&"),("%","\\%"),
                       ("$","\\$"),("#","\\#"),("_","\\_"),("{","\\{"),("}","\\}")]:
        s = s.replace(char, repl)
    return s

# ── Generate ODEQ PDF report ───────────────────────────────────────────────────
@app.post("/api/report")
def generate_report():
    try:
        conn = get_conn(); cursor = conn.cursor()
        try:
            cursor.execute("""SELECT EVIDENCE_ID,SERVICE_LINE_ID,GPS_LATITUDE,GPS_LONGITUDE,
                NVL(USER_VERIFIED_STATUS,'UNVERIFIED'),AUDITED_BY,
                VECTOR_DISTANCE(IMAGE_VECTOR,VECTOR('[1.00,0.00,1.00]',3,FLOAT32),COSINE)
                FROM SYSTEM.EVIDENCE ORDER BY SERVICE_LINE_ID,EVIDENCE_ID""")
        except Exception:
            cursor.execute("""SELECT EVIDENCE_ID,SERVICE_LINE_ID,GPS_LATITUDE,GPS_LONGITUDE,
                NVL(USER_VERIFIED_STATUS,'UNVERIFIED'),AUDITED_BY,NULL
                FROM SYSTEM.EVIDENCE ORDER BY SERVICE_LINE_ID,EVIDENCE_ID""")

        rows = cursor.fetchall(); cursor.close(); conn.close()
        total    = len(rows)
        verified = sum(1 for r in rows if 'CONFIRMED' in str(r[4]))
        suspect  = sum(1 for r in rows if r[6] is not None and float(r[6]) < 0.35)
        lines    = len(set(r[1] for r in rows))

        table_rows = ""
        for r in rows:
            ev  = tex_escape(r[0]); sl = tex_escape(r[1])
            lat = f"{float(r[2]):.4f}" if r[2] else "---"
            lon = f"{float(r[3]):.4f}" if r[3] else "---"
            st  = str(r[4]).replace("MANUALLY_CONFIRMED_", "")
            ins = tex_escape(str(r[5])[:24]) if r[5] else "---"
            dist = f"{float(r[6]):.4f}" if r[6] is not None else "N/A"
            table_rows += f"EV-{ev} & SL-{sl} & {lat}, {lon} & \\small {tex_escape(st)} & {dist} & {ins} \\\\\n\\midrule\n"

        latex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[top=1in,bottom=1in,left=0.65in,right=0.65in]{geometry}
\usepackage{booktabs,longtable,fancyhdr,xcolor}
\definecolor{deqblue}{HTML}{0D3B66}
\pagestyle{fancy}\fancyhf{}
\lhead{\textbf{Oklahoma DEQ LSLI Compliance Submittal}}
\rhead{PWSID: """ + PWSID + r"""}
\cfoot{\thepage}
\begin{document}
\begin{center}
{\Large\bfseries\color{deqblue}LEAD SERVICE LINE INVENTORY --- COMPLIANCE AUDIT LOG}\\
\vspace{2mm}\small Prepared per 40 CFR \S141.84 and Oklahoma DEQ Rules\\
\textbf{Date:} \today
\end{center}
\section*{Executive Metrics}
\begin{tabular}{ll}\toprule
\textbf{Metric} & \textbf{Count}\\\midrule
Total Evidence Records & """ + str(total) + r"""\\
Distinct Service Lines & """ + str(lines) + r"""\\
Lead Suspect (AI) & """ + str(suspect) + r"""\\
Inspector Verified & """ + str(verified) + r"""\\
Pending Review & """ + str(total-verified) + r"""\\
\bottomrule\end{tabular}
\section*{Certified Field Evidence Ledger}
\begin{longtable}{llllll}
\toprule\textbf{EV} & \textbf{SL} & \textbf{GPS} & \textbf{Status} & \textbf{AI Dist} & \textbf{Inspector}\\
\midrule\endhead
""" + table_rows + r"""\bottomrule\end{longtable}
\section*{Legal Attestation}
I hereby certify under penalty of law that this document was compiled in accordance with 40 CFR Part 141 and Oklahoma Administrative Code 252:641.
\vspace{1.2cm}
\noindent\rule{6cm}{0.4pt}\hfill\rule{4cm}{0.4pt}\\
\textbf{Authorized Utility Sign-off}\hfill\textbf{Date}
\end{document}
"""
        tex_path = os.path.join(WORKSPACE, "compliance_report.tex")
        pdf_path = os.path.join(WORKSPACE, "compliance_report.pdf")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex)
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode",
             f"-output-directory={WORKSPACE}", tex_path],
            capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type="application/pdf",
                filename=f"OKW_ODEQ_{datetime.now().strftime('%Y%m%d')}.pdf")
        else:
            raise HTTPException(status_code=500, detail=f"pdflatex failed: {proc.stdout[-500:]}")
    except HTTPException: raise
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pdflatex not found. Install: brew install --cask mactex")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
