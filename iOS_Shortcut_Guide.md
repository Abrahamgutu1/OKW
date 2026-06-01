# OKW FieldSync — iOS Apple Shortcut Build Guide
# Field Inspector Mobile Ingestion Layer v2.0
# Base64 inline photo strategy — fully offline capable
# ══════════════════════════════════════════════════════

## SHORTCUT NAME
OKW Field Capture

## DESCRIPTION
Captures pipe inspection data in the field. Takes a photo with
the device camera, encodes it inline as Base64, grabs GPS
coordinates, builds a self-contained JSON payload, and AirDrops
it to the Mac sync processor — no cloud storage required.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ACTION SEQUENCE

### Action 1 — Ask for Input
  Type     : Number
  Prompt   : "Enter Service Line ID"
  → Output : Variable [ServiceLineID]

### Action 2 — Ask for Input
  Type     : Number
  Prompt   : "Enter Evidence ID"
  → Output : Variable [EvidenceID]

### Action 3 — Take Photo
  Camera   : Back camera (default)
  Show preview before accepting: ON  ← lets inspector retake
  → Output : Variable [FieldPhoto]

### Action 4 — Encode Media
  Input    : [FieldPhoto]
  Encoding : Base64
  Line breaks: OFF  ← critical — must be a single continuous string
  → Output : Variable [Base64PhotoText]

### Action 5 — Get Current Location
  Accuracy : Best (highest precision)
  → Output : Variable [GPSLocation]

### Action 6 — Get Details of Locations
  Input    : [GPSLocation]
  Detail   : Latitude
  → Output : Variable [Latitude]

### Action 7 — Get Details of Locations
  Input    : [GPSLocation]
  Detail   : Longitude
  → Output : Variable [Longitude]

### Action 8 — Text
  (Builds the JSON payload. Insert variables exactly as shown.)

  Paste this entire block as the Text action content:
  ┌─────────────────────────────────────────────────────┐
  {
    "device_id": "FIELD-MOBILE-NODE",
    "records": [
      {
        "evidence_id": [EvidenceID],
        "service_line_id": [ServiceLineID],
        "gps_latitude": [Latitude],
        "gps_longitude": [Longitude],
        "photo_base64": "[Base64PhotoText]"
      }
    ]
  }
  └─────────────────────────────────────────────────────┘

  IMPORTANT: [EvidenceID], [ServiceLineID], [Latitude],
  [Longitude], [Base64PhotoText] are all Shortcut variable
  tokens — tap the variable name to insert them, don't type
  them as plain text.

  → Output : Variable [JSONPayload]

### Action 9 — Save File
  Input    : [JSONPayload]
  Filename : field_drop_[Current Date].json
             (tap "Date" token → format: YYYYMMDD_HHmmss)
  Save to  : iCloud Drive / On My iPhone — your choice
  Ask where to save: OFF
  → Output : Variable [SavedFile]

### Action 10 — Share
  Input    : [SavedFile]
  Action   : This opens the native iOS Share Sheet
             → Select your Mac via AirDrop
  
  NOTE: On the Mac, accept the AirDrop and save the file
  directly into:
  ~/Desktop/OKW FieldSync/SyncDrop/
  The watch processor will pick it up within 30 seconds.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT THE MAC SYNC PROCESSOR DOES WITH THE PAYLOAD

1. Detects the .json file in SyncDrop/
2. Parses photo_base64 string
3. Strips any data-URI prefix (data:image/jpeg;base64,...)
4. Fixes Base64 padding if needed
5. Validates JPEG magic bytes (FF D8 FF)
6. Decodes to binary and saves as:
   ~/Desktop/OKW FieldSync/FieldPhotos/EV{id}_SL{id}_{ts}.jpg
7. Writes file://... absolute path into EVIDENCE.PHOTO_URL
8. Upserts all fields into Oracle 23ai FREEPDB1 via MERGE
9. Archives the .json as .json.processed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXAMPLE OUTPUT PAYLOAD (what the Shortcut produces)

{
  "device_id": "FIELD-MOBILE-NODE",
  "records": [
    {
      "evidence_id": 5,
      "service_line_id": 23,
      "gps_latitude": 35.467821,
      "gps_longitude": -97.516934,
      "photo_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA..."
    }
  ]
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TESTING WITHOUT A REAL FIELD PHOTO

To test the pipeline with a synthetic Base64 image, drop this
file into SyncDrop/ and run the processor:

  file: test_base64_drop.json

{
  "device_id": "FIELD-IPAD-TEST",
  "records": [
    {
      "evidence_id": 10,
      "service_line_id": 99,
      "gps_latitude": 35.4678,
      "gps_longitude": -97.5169,
      "photo_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AJQAB/9k="
    }
  ]
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## NOTES

- Base64 strings from iOS cameras are typically 2-8 MB of text
  for a full resolution photo. The JSON file will be large.
  This is expected and handled correctly by the processor.

- The Streamlit dashboard reads PHOTO_URL as a file:// path.
  Local file:// URLs render correctly in st.image() when the
  dashboard is running on the same Mac as the FieldPhotos dir.

- For multi-inspector deployments, consider changing device_id
  in each inspector's shortcut (FIELD-IPAD-01, FIELD-IPAD-02)
  so the archive logs show which device submitted each payload.