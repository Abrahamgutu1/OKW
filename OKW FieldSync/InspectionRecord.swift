// InspectionRecord.swift
// OKW FieldSync — Local persistence model
// SwiftData (iOS 17+) — falls back to instructions for CoreData below

import Foundation
import SwiftData

// ── Sync status ────────────────────────────────────────────────────────────────
enum SyncStatus: String, Codable {
    case pending  = "PENDING"
    case synced   = "SYNCED"
    case failed   = "FAILED"
}

// ── Local device record (SwiftData model) ─────────────────────────────────────
@Model
final class InspectionRecord {
    var id:              UUID
    var evidenceID:      Int
    var serviceLineID:   Int
    var gpsLatitude:     Double
    var gpsLongitude:    Double
    var gpsAccuracy:     Double        // metres
    var photoBase64:     String        // raw Base64, no data-URI prefix
    var capturedAt:      Date
    var syncStatus:      String        // store as String for SwiftData compat

    init(
        evidenceID:    Int,
        serviceLineID: Int,
        gpsLatitude:   Double,
        gpsLongitude:  Double,
        gpsAccuracy:   Double,
        photoBase64:   String
    ) {
        self.id            = UUID()
        self.evidenceID    = evidenceID
        self.serviceLineID = serviceLineID
        self.gpsLatitude   = gpsLatitude
        self.gpsLongitude  = gpsLongitude
        self.gpsAccuracy   = gpsAccuracy
        self.photoBase64   = photoBase64
        self.capturedAt    = Date()
        self.syncStatus    = SyncStatus.pending.rawValue
    }

    var status: SyncStatus {
        SyncStatus(rawValue: syncStatus) ?? .pending
    }
}

// ── Codable export model — maps to sync_processor.py JSON contract ─────────────
struct ExportRecord: Codable {
    let evidence_id:    Int
    let service_line_id: Int
    let gps_latitude:   Double
    let gps_longitude:  Double
    let photo_base64:   String   // clean raw Base64, no prefix
}

struct ExportPayload: Codable {
    let device_id: String
    let records:   [ExportRecord]
}
