// FieldCaptureManager.swift
// OKW FieldSync — Camera invocation, GPS capture, Base64 encoding

import Foundation
import UIKit
import CoreLocation
import Combine

// ── Location Manager ───────────────────────────────────────────────────────────
final class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {

    private let manager = CLLocationManager()

    @Published var latitude:  Double = 0.0
    @Published var longitude: Double = 0.0
    @Published var accuracy:  Double = -1     // negative = no fix yet
    @Published var statusText: String = "Acquiring GPS…"

    override init() {
        super.init()
        manager.delegate           = self
        manager.desiredAccuracy    = kCLLocationAccuracyBest
        manager.distanceFilter     = kCLDistanceFilterNone
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager,
                         didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        DispatchQueue.main.async {
            self.latitude   = loc.coordinate.latitude
            self.longitude  = loc.coordinate.longitude
            self.accuracy   = loc.horizontalAccuracy
            self.statusText = String(format: "±%.1f m", loc.horizontalAccuracy)
        }
    }

    func locationManager(_ manager: CLLocationManager,
                         didFailWithError error: Error) {
        DispatchQueue.main.async {
            self.statusText = "GPS unavailable"
        }
    }

    var hasValidFix: Bool { accuracy > 0 && accuracy < 50 }
}

// ── Image → clean raw Base64 ───────────────────────────────────────────────────
enum PhotoEncoder {
    /// Converts a UIImage to a raw Base64 string (no data-URI prefix).
    /// Matches what sync_processor.py expects.
    static func encode(_ image: UIImage, compressionQuality: CGFloat = 0.75) -> String? {
        guard let jpegData = image.jpegData(compressionQuality: compressionQuality) else {
            return nil
        }
        // Encode to Base64 WITHOUT line breaks — critical for valid JSON
        return jpegData.base64EncodedString(options: [])
    }
}

// ── Camera coordinator (UIImagePickerController wrapper) ──────────────────────
import SwiftUI

struct CameraPicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType            = .camera
        picker.cameraCaptureMode     = .photo
        picker.cameraDevice          = .rear
        picker.allowsEditing         = false
        picker.delegate              = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController,
                                context: Context) {}

    final class Coordinator: NSObject,
                             UIImagePickerControllerDelegate,
                             UINavigationControllerDelegate {
        let parent: CameraPicker
        init(_ parent: CameraPicker) { self.parent = parent }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let img = info[.originalImage] as? UIImage {
                parent.selectedImage = img
            }
            parent.dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}
