# OKW FieldSync iOS — Xcode Setup Guide

## Files to add to your Xcode project

Add all 5 Swift files to your Xcode project target:

1. ContentView.swift        — App entry point + tab layout + color tokens
2. InspectionRecord.swift   — SwiftData model + Codable export structs
3. FieldCaptureManager.swift — LocationManager + PhotoEncoder + CameraPicker
4. InspectionFormView.swift — Field capture form UI
5. SyncQueueView.swift      — Pending records list + export bar
6. ExportManager.swift      — JSON builder + AirDrop share sheet

---

## Xcode project settings

1. iOS Deployment Target: iOS 17.0+
   (Required for SwiftData. If you need iOS 16, swap @Model for CoreData)

2. Info.plist — add these privacy keys:
   NSCameraUsageDescription
   → "OKW FieldSync needs camera access to photograph service line pipes."

   NSLocationWhenInUseUsageDescription
   → "OKW FieldSync needs your location to tag inspection coordinates."

3. Capabilities (Signing & Capabilities tab):
   No special entitlements needed for AirDrop or SwiftData.

---

## AccentTeal color asset

In Assets.xcassets, create a Color Set named "AccentTeal":
- Any Appearance: R=0  G=178  B=214  (hex #00B2D6)
- Dark Appearance: same value

---

## How AirDrop to Mac works

1. Inspector taps "Export All Pending" or selects specific records
2. App builds field_drop_YYYYMMDD_HHmmss.json in temp directory
3. iOS Share Sheet opens
4. Inspector taps AirDrop → selects Mac
5. On Mac: click Accept dropdown → Save to → SyncDrop folder
6. sync_processor.py (--watch mode) picks it up within 30 seconds

---

## JSON output example

{
  "device_id": "FIELD-MOBILE-NODE",
  "records": [
    {
      "evidence_id": 3,
      "service_line_id": 22,
      "gps_latitude": 35.2215,
      "gps_longitude": -97.4442,
      "photo_base64": "/9j/4AAQSkZJRg..."
    }
  ]
}

photo_base64 is raw Base64 with NO data:image/jpeg;base64, prefix.
This matches exactly what sync_processor.py expects.
