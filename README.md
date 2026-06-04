# OKW FieldSync v2.0

**EPA Lead & Copper Rule Improvements (LCRI) compliance platform for Oklahoma water utilities.**

Full-stack: React dashboard · FastAPI backend · Oracle 23ai · SwiftUI iOS app · ResNet-50 AI pipeline

---

## What This Is

OKW FieldSync lets field inspectors capture lead service line evidence on an iPhone and syncs it to a compliance dashboard in real time. Built specifically for Oklahoma water systems facing the EPA LCRI inventory deadline (November 1, 2027).

```
iPhone (field capture)
    ↓  WiFi sync
FastAPI backend (port 8000)
    ↓
Oracle 23ai Docker (port 1521)
    ↑
React dashboard (port 5173)
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | brew install python |
| Node.js | 18+ | brew install node |
| Docker Desktop | latest | docker.com/products/docker-desktop |
| Xcode | 15+ | Mac App Store (iOS dev only) |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/Abrahamgutu1/OKW.git
cd OKW
```

### 2. Start Oracle 23ai (Docker)

```bash
docker run -d \
  --name oracle-free \
  -p 1521:1521 \
  -e ORACLE_PASSWORD=Awesomekid123 \
  container-registry.oracle.com/database/free:latest

# Wait ~2 minutes for Oracle to initialize, then unlock system user:
docker exec -i oracle-free bash -c "printf 'ALTER USER system ACCOUNT UNLOCK;\nALTER USER system IDENTIFIED BY Awesomekid123 CONTAINER=ALL;\nEXIT;\n' > /tmp/fix.sql && sqlplus / as sysdba @/tmp/fix.sql"
```

If Oracle container already exists (returning user):
```bash
docker start oracle-free && sleep 35 && docker exec -i oracle-free bash -c "printf 'ALTER USER system ACCOUNT UNLOCK;\nALTER USER system IDENTIFIED BY Awesomekid123 CONTAINER=ALL;\nEXIT;\n' > /tmp/fix.sql && sqlplus / as sysdba @/tmp/fix.sql"
```

### 3. Set up the database schema

```bash
docker exec -i oracle-free sqlplus system/Awesomekid123@localhost:1521/FREEPDB1 < okw_fieldsync_oracle23ai.sql
```

### 4. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 --host 0.0.0.0
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 5. Start the frontend dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at: `http://localhost:5173`

---

## iOS App (Xcode)

1. Open `OKW FieldSync.xcodeproj` in Xcode
2. Select your iPhone as the target device
3. In `OKW FieldSync/NetworkManager.swift` update the Mac IP:
```swift
static let macIPAddress = "YOUR_MAC_IP"  // run: ipconfig getifaddr en0
```
4. Add your API key in `OKW FieldSync/FieldCaptureManager.swift`:
```swift
private let apiKey = "YOUR_ANTHROPIC_KEY_HERE"
```
5. Hit **Cmd+R** to build and run on device

> Your iPhone and Mac must be on the same WiFi network.

---

## Project Structure

```
OKW FieldSync/
├── backend/
│   ├── main.py              # FastAPI app — all API endpoints
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React + Vite dashboard
│   └── package.json
├── OKW FieldSync/           # SwiftUI iOS app (9 files)
│   ├── ContentView.swift
│   ├── InspectionFormView.swift
│   ├── InspectionRecord.swift
│   ├── FieldCaptureManager.swift
│   ├── NetworkManager.swift
│   ├── SyncQueueView.swift
│   ├── ExportManager.swift
│   ├── DesignSystem.swift
│   └── LaunchScreenView.swift
├── OKW FieldSync.xcodeproj/
├── okw_fieldsync_oracle23ai.sql   # Oracle schema
├── sync_processor.py              # JSON → Oracle sync processor
├── Train model.py                 # PIPE_VISION_AI ResNet-50 training
├── Deploy model.py                # Model inference pipeline
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check backend status |
| GET | `/api/evidence` | Fetch all records + KPIs for dashboard |
| POST | `/api/upload_inspection` | Receive iPhone photo + GPS → Oracle |
| POST | `/api/audit` | Inspector verifies a record |
| POST | `/api/report` | Generate ODEQ PDF compliance report |
| POST | `/api/seed` | Seed 15 demo records for testing |

---

## Database

- **Host:** localhost:1521
- **Service:** FREEPDB1
- **User:** system
- **Password:** Awesomekid123
- **Main table:** SYSTEM.EVIDENCE

Connect via SQL*Plus:
```bash
docker exec -it oracle-free sqlplus system/Awesomekid123@localhost:1521/FREEPDB1
```

---

## Environment / Secrets

Never commit API keys. After cloning, set your keys locally:

- **Anthropic API key** → `OKW FieldSync/FieldCaptureManager.swift` line with `YOUR_ANTHROPIC_KEY_HERE`
- **Mac IP for iOS** → `OKW FieldSync/NetworkManager.swift` — `macIPAddress`

---

## Regulatory Context

- **EPA Rule:** Lead and Copper Rule Improvements (LCRI) — 40 CFR §141.84
- **Oklahoma Authority:** ODEQ / OWRB
- **PWSID:** OK1020401 (demo)
- **Inventory Deadline:** November 1, 2027
- **Key Classification:** Lead/Unknown = HIGH risk (replace), Galvanized = MEDIUM (GRR), Copper/PVC = LOW

---

## Team

- **Abraham Gutu** — Co-founder, iOS + Full-stack
- University of Oklahoma, CS + ML, May 2027

---

## License

Private — not for redistribution.
