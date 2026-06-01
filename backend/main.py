"""
OKW FieldSync — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import oracledb, os, subprocess
from datetime import datetime

app = FastAPI(title="OKW FieldSync API", version="2.0")
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000"],
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

class AuditUpdate(BaseModel):
    evidence_id: int
    status: str
    inspector_pin: str

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/evidence")
def get_evidence():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT EVIDENCE_ID, SERVICE_LINE_ID, PHOTO_URL,
                       GPS_LATITUDE, GPS_LONGITUDE, UPLOAD_DATE,
                       NVL(USER_VERIFIED_STATUS,'UNVERIFIED') AS USER_VERIFIED_STATUS,
                       AUDITED_BY,
                       VECTOR_DISTANCE(IMAGE_VECTOR,VECTOR('[1.00,0.00,1.00]',3,FLOAT32),COSINE) AS AI_DISTANCE
                FROM EVIDENCE ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
            """)
            vec_ok = True
        except Exception:
            cursor.execute("""
                SELECT EVIDENCE_ID, SERVICE_LINE_ID, PHOTO_URL,
                       GPS_LATITUDE, GPS_LONGITUDE, UPLOAD_DATE,
                       NVL(USER_VERIFIED_STATUS,'UNVERIFIED') AS USER_VERIFIED_STATUS,
                       AUDITED_BY, NULL AS AI_DISTANCE
                FROM EVIDENCE ORDER BY SERVICE_LINE_ID, EVIDENCE_ID
            """)
            vec_ok = False
        cols = [d[0].lower() for d in cursor.description]
        rows = []
        for row in cursor.fetchall():
            r = dict(zip(cols, row))
            if r.get("upload_date"):
                r["upload_date"] = r["upload_date"].isoformat() if hasattr(r["upload_date"],"isoformat") else str(r["upload_date"])
            if r.get("ai_distance") is not None:
                try: r["ai_distance"] = float(r["ai_distance"])
                except: r["ai_distance"] = None
            rows.append(r)
        total = len(rows)
        suspect  = sum(1 for r in rows if r.get("ai_distance") is not None and r["ai_distance"] < 0.35)
        verified = sum(1 for r in rows if r.get("user_verified_status","") in ["MANUALLY_CONFIRMED_LEAD","MANUALLY_CONFIRMED_SAFE"])
        has_photo = sum(1 for r in rows if str(r.get("photo_url","")).startswith("http"))
        cursor.close(); conn.close()
        return {"records": rows, "kpis": {"total": total, "suspect": suspect, "verified": verified,
                "has_photo": has_photo, "pending": total - verified,
                "lines": len(set(r["service_line_id"] for r in rows))}, "vec_ok": vec_ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audit")
def submit_audit(body: AuditUpdate):
    if body.inspector_pin not in INSPECTOR_REGISTRY:
        raise HTTPException(status_code=401, detail="Invalid inspector PIN")
    if body.status not in ["MANUALLY_CONFIRMED_LEAD","MANUALLY_CONFIRMED_SAFE"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    try:
        inspector = INSPECTOR_REGISTRY[body.inspector_pin]
        conn = get_conn(); cursor = conn.cursor()
        cursor.execute("UPDATE EVIDENCE SET USER_VERIFIED_STATUS=:1, AUDITED_BY=:2 WHERE EVIDENCE_ID=:3",
                       (body.status, inspector, body.evidence_id))
        conn.commit(); cursor.close(); conn.close()
        return {"status": "ok", "message": f"EV-{body.evidence_id} signed off by {inspector}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def tex_escape(val):
    if val is None: return "---"
    s = str(val)
    for char, repl in [("\\","\\textbackslash{}"),("&","\\&"),("%","\\%"),
                       ("$","\\$"),("#","\\#"),("_","\\_"),("{","\\{"),("}","\\}")]:
        s = s.replace(char, repl)
    return s

@app.post("/api/report")
def generate_report():
    try:
        conn = get_conn(); cursor = conn.cursor()
        try:
            cursor.execute("""SELECT EVIDENCE_ID,SERVICE_LINE_ID,GPS_LATITUDE,GPS_LONGITUDE,
                NVL(USER_VERIFIED_STATUS,'UNVERIFIED'),AUDITED_BY,
                VECTOR_DISTANCE(IMAGE_VECTOR,VECTOR('[1.00,0.00,1.00]',3,FLOAT32),COSINE)
                FROM EVIDENCE ORDER BY SERVICE_LINE_ID,EVIDENCE_ID""")
        except Exception:
            cursor.execute("""SELECT EVIDENCE_ID,SERVICE_LINE_ID,GPS_LATITUDE,GPS_LONGITUDE,
                NVL(USER_VERIFIED_STATUS,'UNVERIFIED'),AUDITED_BY,NULL
                FROM EVIDENCE ORDER BY SERVICE_LINE_ID,EVIDENCE_ID""")
        rows = cursor.fetchall(); cursor.close(); conn.close()
        total = len(rows)
        verified = sum(1 for r in rows if 'CONFIRMED' in str(r[4]))
        suspect  = sum(1 for r in rows if r[6] is not None and float(r[6]) < 0.35)
        lines    = len(set(r[1] for r in rows))
        table_rows = ""
        for r in rows:
            ev=tex_escape(r[0]); sl=tex_escape(r[1])
            lat=f"{float(r[2]):.4f}" if r[2] else "---"
            lon=f"{float(r[3]):.4f}" if r[3] else "---"
            st=str(r[4]).replace("MANUALLY_CONFIRMED_","")
            ins=tex_escape(str(r[5])[:24]) if r[5] else "---"
            dist=f"{float(r[6]):.4f}" if r[6] is not None else "N/A"
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
        proc = subprocess.run(["pdflatex","-interaction=nonstopmode",
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
