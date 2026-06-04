// InspectionRecord.swift
// OKW FieldSync — Local persistence model
// SwiftData (iOS 17+)

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
    var id:                   UUID
    var evidenceID:           Int
    var serviceLineID:        Int
    var gpsLatitude:          Double
    var gpsLongitude:         Double
    var gpsAccuracy:          Double
    var photoBase64:          String
    var capturedAt:           Date
    var syncStatus:           String

    // Cloud Vision fields
    var visionLabels:         String   // comma-separated, e.g. "pipe,metal,corroded"
    var visionColor:          String   // "grey" | "orange" | "dark" | "unknown"
    var visionPipeConfirmed:  String   // "1" or "0"
    var visionConfidence:     String   // "0.00" – "1.00"

    init(
        evidenceID:           Int,
        serviceLineID:        Int,
        gpsLatitude:          Double,
        gpsLongitude:         Double,
        gpsAccuracy:          Double,
        photoBase64:          String,
        visionLabels:         String = "",
        visionColor:          String = "",
        visionPipeConfirmed:  String = "0",
        visionConfidence:     String = "0.00"
    ) {
        self.id                   = UUID()
        self.evidenceID           = evidenceID
        self.serviceLineID        = serviceLineID
        self.gpsLatitude          = gpsLatitude
        self.gpsLongitude         = gpsLongitude
        self.gpsAccuracy          = gpsAccuracy
        self.photoBase64          = photoBase64
        self.capturedAt           = Date()
        self.syncStatus           = SyncStatus.pending.rawValue
        self.visionLabels         = visionLabels
        self.visionColor          = visionColor
        self.visionPipeConfirmed  = visionPipeConfirmed
        self.visionConfidence     = visionConfidence
    }

    var status: SyncStatus {
        SyncStatus(rawValue: syncStatus) ?? .pending
    }
}

// ── Codable export model — maps to sync_processor.py JSON contract ─────────────
struct ExportRecord: Codable {
    let evidence_id:            Int
    let service_line_id:        Int
    let gps_latitude:           Double
    let gps_longitude:          Double
    let photo_base64:           String
    let vision_labels:          String
    let vision_color:           String
    let vision_pipe_confirmed:  String
    let vision_confidence:      String
}

struct ExportPayload: Codable {
    let device_id: String
    let records:   [ExportRecord]
}
