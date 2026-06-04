// ExportManager.swift
// OKW FieldSync — JSON payload builder and AirDrop share sheet trigger

import Foundation
import UIKit

enum ExportError: LocalizedError {
    case noRecords
    case encodingFailed
    case fileWriteFailed(Error)

    var errorDescription: String? {
        switch self {
        case .noRecords:              return "No records selected for export."
        case .encodingFailed:         return "Failed to encode payload as JSON."
        case .fileWriteFailed(let e): return "File write failed: \(e.localizedDescription)"
        }
    }
}

final class ExportManager {

    static let deviceID = "FIELD-MOBILE-NODE"

    // ── Build JSON payload from InspectionRecord array ────────────────────────
    static func buildPayload(from records: [InspectionRecord]) throws -> Data {
        guard !records.isEmpty else { throw ExportError.noRecords }

        let exportRecords = records.map {
            ExportRecord(
                evidence_id:            $0.evidenceID,
                service_line_id:        $0.serviceLineID,
                gps_latitude:           $0.gpsLatitude,
                gps_longitude:          $0.gpsLongitude,
                photo_base64:           $0.photoBase64,
                vision_labels:          $0.visionLabels,
                vision_color:           $0.visionColor,
                vision_pipe_confirmed:  $0.visionPipeConfirmed,
                vision_confidence:      $0.visionConfidence
            )
        }

        let payload = ExportPayload(device_id: deviceID, records: exportRecords)

        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        guard let data = try? encoder.encode(payload) else {
            throw ExportError.encodingFailed
        }
        return data
    }

    // ── Write payload to a temp .json file ────────────────────────────────────
    static func writeToTempFile(data: Data) throws -> URL {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        let timestamp = formatter.string(from: Date())
        let filename  = "field_drop_\(timestamp).json"

        let tempDir = FileManager.default.temporaryDirectory
        let fileURL = tempDir.appendingPathComponent(filename)

        do {
            try data.write(to: fileURL, options: .atomic)
        } catch {
            throw ExportError.fileWriteFailed(error)
        }
        return fileURL
    }

    // ── Present native iOS Share Sheet (AirDrop entry point) ─────────────────
    @MainActor
    static func presentShareSheet(
        for records: [InspectionRecord],
        from viewController: UIViewController
    ) {
        do {
            let data    = try buildPayload(from: records)
            let fileURL = try writeToTempFile(data: data)

            let activity = UIActivityViewController(
                activityItems: [fileURL],
                applicationActivities: nil
            )

            if let popover = activity.popoverPresentationController {
                popover.sourceView = viewController.view
                popover.sourceRect = CGRect(
                    x: viewController.view.bounds.midX,
                    y: viewController.view.bounds.midY,
                    width: 0, height: 0
                )
                popover.permittedArrowDirections = []
            }

            viewController.present(activity, animated: true)

        } catch {
            let alert = UIAlertController(
                title:   "Export Failed",
                message: error.localizedDescription,
                preferredStyle: .alert
            )
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            viewController.present(alert, animated: true)
        }
    }
}

// ── SwiftUI wrapper to get UIViewController for share sheet ───────────────────
import SwiftUI

struct ShareSheetButton: View {
    let records: [InspectionRecord]
    let label:   String

    @State private var showError = false
    @State private var errorMsg  = ""

    var body: some View {
        Button(action: triggerExport) {
            Label(label, systemImage: "square.and.arrow.up")
                .font(.system(size: 15, weight: .semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(records.isEmpty ? Color.gray.opacity(0.3) : Color("AccentTeal"))
                .foregroundColor(.white)
                .cornerRadius(6)
        }
        .disabled(records.isEmpty)
        .alert("Export Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(errorMsg)
        }
    }

    private func triggerExport() {
        guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let vc    = scene.windows.first?.rootViewController else { return }

        var topVC = vc
        while let presented = topVC.presentedViewController {
            topVC = presented
        }

        ExportManager.presentShareSheet(for: records, from: topVC)
    }
}
