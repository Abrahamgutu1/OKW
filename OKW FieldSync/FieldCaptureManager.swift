// FieldCaptureManager.swift
// OKW FieldSync — Camera, GPS, Gemini Vision + PIPE_VISION_AI v2 CoreML

import Foundation
import UIKit
import CoreLocation
import CoreML
import Vision
import Combine
import SwiftUI

// ── Vision Result ──────────────────────────────────────────────────────────────
struct VisionAnalysis {
    var materialGuess:   String
    var description:     String
    var isPipeConfirmed: Bool
    var riskLevel:       String
    var dominantColor:   String
    var labels:          [String]
    var rawResponse:     String
    // PIPE_VISION_AI v2 fields
    var pipeCondition:   String   // "corrosion" | "crack" | "good" | "unknown"
    var pipeSeverity:    String   // "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    var yoloConfidence:  Float    // 0.0 – 1.0
    var yoloDetections:  [String] // e.g. ["corrosion (0.82)", "crack (0.61)"]
}

// ── Location Manager ───────────────────────────────────────────────────────────
final class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {

    private let manager = CLLocationManager()

    @Published var latitude:   Double = 0.0
    @Published var longitude:  Double = 0.0
    @Published var accuracy:   Double = -1
    @Published var statusText: String = "Acquiring GPS…"

    override init() {
        super.init()
        manager.delegate        = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        manager.distanceFilter  = kCLDistanceFilterNone
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
        DispatchQueue.main.async { self.statusText = "GPS unavailable" }
    }

    var hasValidFix: Bool { accuracy > 0 && accuracy < 50 }
}

// ── Image → Base64 ─────────────────────────────────────────────────────────────
enum PhotoEncoder {
    static func encode(_ image: UIImage, compressionQuality: CGFloat = 0.75) -> String? {
        guard let jpegData = image.jpegData(compressionQuality: compressionQuality) else {
            return nil
        }
        return jpegData.base64EncodedString(options: [])
    }
}

// ── PIPE_VISION_AI v2 — On-device CoreML ──────────────────────────────────────
final class PipeVisionAI {

    static let shared = PipeVisionAI()

    private var visionModel: VNCoreMLModel?
    private let classNames = ["corrosion", "crack"]   // must match training classes

    private init() {
        loadModel()
    }

    private func loadModel() {
        guard let modelURL = Bundle.main.url(forResource: "best_v2",
                                             withExtension: "mlpackage") else {
            print("⚠️ PIPE_VISION_AI: best_v2.mlpackage not found in bundle")
            return
        }
        do {
            let config = MLModelConfiguration()
            config.computeUnits = .cpuAndNeuralEngine
            let mlModel = try MLModel(contentsOf: modelURL, configuration: config)
            visionModel = try VNCoreMLModel(for: mlModel)
            print("✅ PIPE_VISION_AI v2 loaded")
        } catch {
            print("⚠️ PIPE_VISION_AI load error: \(error)")
        }
    }

    struct YOLOResult {
        var condition:   String  // top detected class
        var severity:    String  // HIGH/MEDIUM/LOW/UNKNOWN
        var confidence:  Float
        var detections:  [String]
    }

    func analyze(image: UIImage, completion: @escaping (YOLOResult) -> Void) {
        guard let visionModel = visionModel,
              let cgImage = image.cgImage else {
            completion(YOLOResult(condition: "unknown", severity: "UNKNOWN",
                                  confidence: 0, detections: []))
            return
        }

        let request = VNCoreMLRequest(model: visionModel) { request, error in
            guard error == nil,
                  let results = request.results as? [VNRecognizedObjectObservation],
                  !results.isEmpty else {
                completion(YOLOResult(condition: "good", severity: "LOW",
                                      confidence: 0, detections: []))
                return
            }

            // Sort by confidence
            let sorted = results.sorted { $0.confidence > $1.confidence }
            var detections: [String] = []
            var topCondition = "good"
            var topConfidence: Float = 0

            for obs in sorted.prefix(5) {
                if let label = obs.labels.first {
                    let det = "\(label.identifier) (\(String(format: "%.2f", obs.confidence)))"
                    detections.append(det)
                    if obs.confidence > topConfidence {
                        topCondition  = label.identifier
                        topConfidence = obs.confidence
                    }
                }
            }

            let severity: String
            switch topCondition.lowercased() {
            case "corrosion":
                severity = topConfidence > 0.75 ? "HIGH" : topConfidence > 0.5 ? "MEDIUM" : "LOW"
            case "crack":
                severity = topConfidence > 0.70 ? "HIGH" : "MEDIUM"
            default:
                severity = "LOW"
            }

            completion(YOLOResult(
                condition:  topCondition,
                severity:   severity,
                confidence: topConfidence,
                detections: detections
            ))
        }

        request.imageCropAndScaleOption = .scaleFill

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        DispatchQueue.global(qos: .userInitiated).async {
            try? handler.perform([request])
        }
    }
}

// ── Gemini Vision Client ───────────────────────────────────────────────────────
final class ClaudeVisionClient {

    private let apiKey   = "GEMINI_API_KEY_HERE"
    private let endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    private let model    = "gemini-2.5-flash"

    private let prompt = """
    You are an EPA Lead and Copper Rule compliance assistant analyzing a field photo \
    of a water service line pipe taken by an Oklahoma water utility inspector.

    Analyze this image and respond in this exact JSON format (no markdown, no backticks):
    {
      "pipe_detected": true or false,
      "material_guess": "lead" | "galvanized steel" | "copper" | "PVC" | "unknown",
      "risk_level": "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN",
      "color_description": "brief color description",
      "surface_description": "brief surface/texture description",
      "confidence": "HIGH" | "MEDIUM" | "LOW",
      "epa_classification_hint": "one sentence relevant to LCRI §141.84 classification",
      "inspector_note": "one actionable sentence for the field inspector"
    }

    Risk level guide:
    - HIGH = lead or unknown material (treat as lead per LCRI §141.84(b))
    - MEDIUM = galvanized requiring replacement (GRR)
    - LOW = copper or PVC (non-lead)
    - UNKNOWN = cannot determine from image

    If no pipe is visible, set pipe_detected to false and all other fields to "unknown".
    """

    func analyze(image: UIImage, completion: @escaping (VisionAnalysis?) -> Void) {
        guard let base64 = PhotoEncoder.encode(image, compressionQuality: 0.75),
              let url = URL(string: endpoint) else {
            completion(nil); return
        }

        let body: [String: Any] = [
            "contents": [[
                "parts": [
                    ["text": prompt],
                    ["inline_data": [
                        "mime_type": "image/jpeg",
                        "data": base64
                    ]]
                ]
            ]],
            "generationConfig": [
                "temperature": 0.1,
                "maxOutputTokens": 512
            ]
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "content-type")
        request.setValue(apiKey,             forHTTPHeaderField: "x-goog-api-key")
        request.timeoutInterval = 20

        guard let httpBody = try? JSONSerialization.data(withJSONObject: body) else {
            completion(nil); return
        }
        request.httpBody = httpBody

        URLSession.shared.dataTask(with: request) { data, _, error in
            guard let data = data, error == nil else {
                DispatchQueue.main.async { completion(nil) }
                return
            }
            let result = self.parseResponse(data: data)
            DispatchQueue.main.async { completion(result) }
        }.resume()
    }

    private func parseResponse(data: Data) -> VisionAnalysis? {
        guard
            let json       = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let candidates = json["candidates"] as? [[String: Any]],
            let first      = candidates.first,
            let content    = first["content"] as? [String: Any],
            let parts      = content["parts"] as? [[String: Any]],
            let text       = parts.first?["text"] as? String
        else { return nil }

        let cleaned = text
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "```json", with: "")
            .replacingOccurrences(of: "```", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)

        guard
            let jsonData = cleaned.data(using: .utf8),
            let parsed   = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
        else {
            return VisionAnalysis(
                materialGuess: "unknown", description: text,
                isPipeConfirmed: text.lowercased().contains("pipe"),
                riskLevel: "UNKNOWN", dominantColor: "unknown",
                labels: [], rawResponse: text,
                pipeCondition: "unknown", pipeSeverity: "UNKNOWN",
                yoloConfidence: 0, yoloDetections: []
            )
        }

        let material  = parsed["material_guess"]          as? String ?? "unknown"
        let risk      = parsed["risk_level"]              as? String ?? "UNKNOWN"
        let color     = parsed["color_description"]       as? String ?? "unknown"
        let surface   = parsed["surface_description"]     as? String ?? ""
        let epaHint   = parsed["epa_classification_hint"] as? String ?? ""
        let note      = parsed["inspector_note"]          as? String ?? ""
        let pipeFound = parsed["pipe_detected"]           as? Bool   ?? false
        let confidence = parsed["confidence"]             as? String ?? "LOW"

        let description = [epaHint, note].filter { !$0.isEmpty }.joined(separator: " ")
        let labels      = [material, color, surface, confidence.lowercased()]
                            .filter { !$0.isEmpty && $0 != "unknown" }

        return VisionAnalysis(
            materialGuess:   material,
            description:     description.isEmpty ? text : description,
            isPipeConfirmed: pipeFound,
            riskLevel:       risk,
            dominantColor:   color,
            labels:          labels,
            rawResponse:     text,
            pipeCondition:   "unknown",
            pipeSeverity:    "UNKNOWN",
            yoloConfidence:  0,
            yoloDetections:  []
        )
    }
}

// ── Field Capture Manager ──────────────────────────────────────────────────────
@MainActor
final class FieldCaptureManager: ObservableObject {

    @Published var capturedImage:    UIImage?
    @Published var visionResult:     VisionAnalysis?
    @Published var isAnalyzing:      Bool   = false
    @Published var visionStatusText: String = ""

    private let geminiClient = ClaudeVisionClient()

    func photoSelected(_ image: UIImage) {
        capturedImage    = image
        visionResult     = nil
        isAnalyzing      = true
        visionStatusText = "Analyzing pipe with Gemini + PIPE_VISION_AI…"

        // Run Gemini and YOLO in parallel using DispatchGroup
        let group = DispatchGroup()

        var geminiResult: VisionAnalysis?
        var yoloResult: PipeVisionAI.YOLOResult?

        // Gemini analysis
        group.enter()
        geminiClient.analyze(image: image) { result in
            geminiResult = result
            group.leave()
        }

        // PIPE_VISION_AI v2 analysis
        group.enter()
        PipeVisionAI.shared.analyze(image: image) { result in
            yoloResult = result
            group.leave()
        }

        // Merge results when both complete
        group.notify(queue: .main) { [weak self] in
            guard let self else { return }
            self.isAnalyzing = false

            if var analysis = geminiResult {
                // Merge YOLO results into Gemini analysis
                if let yolo = yoloResult {
                    analysis.pipeCondition  = yolo.condition
                    analysis.pipeSeverity   = yolo.severity
                    analysis.yoloConfidence = yolo.confidence
                    analysis.yoloDetections = yolo.detections

                    // Escalate risk if YOLO finds severe corrosion
                    if yolo.condition == "corrosion" && yolo.severity == "HIGH" && analysis.riskLevel != "HIGH" {
                        analysis.riskLevel = "HIGH"
                        analysis.description += " PIPE_VISION_AI detected severe corrosion."
                    }
                }
                self.visionResult     = analysis
                self.visionStatusText = analysis.description
            } else if let yolo = yoloResult {
                // Gemini failed, use YOLO only
                self.visionResult = VisionAnalysis(
                    materialGuess:   "unknown",
                    description:     "PIPE_VISION_AI: \(yolo.condition) detected (\(String(format: "%.0f", yolo.confidence * 100))% confidence)",
                    isPipeConfirmed: yolo.condition != "unknown",
                    riskLevel:       yolo.severity,
                    dominantColor:   "unknown",
                    labels:          [yolo.condition],
                    rawResponse:     "",
                    pipeCondition:   yolo.condition,
                    pipeSeverity:    yolo.severity,
                    yoloConfidence:  yolo.confidence,
                    yoloDetections:  yolo.detections
                )
                self.visionStatusText = self.visionResult?.description ?? ""
            } else {
                self.visionStatusText = "Vision analysis unavailable — manual classification required"
            }
        }
    }

    func visionMetadata() -> [String: String] {
        guard let v = visionResult else { return [:] }
        return [
            "vision_labels":         v.labels.joined(separator: ","),
            "vision_color":          v.dominantColor,
            "vision_pipe_confirmed": v.isPipeConfirmed ? "1" : "0",
            "vision_confidence":     v.riskLevel,
            "vision_raw_json":       v.rawResponse,
            "pipe_condition":        v.pipeCondition,
            "pipe_severity":         v.pipeSeverity,
            "yolo_confidence":       String(format: "%.3f", v.yoloConfidence),
            "yolo_detections":       v.yoloDetections.joined(separator: "|")
        ]
    }
}

// ── Camera coordinator ─────────────────────────────────────────────────────────
struct CameraPicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    var onImageSelected: ((UIImage) -> Void)? = nil
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType        = .camera
        picker.cameraCaptureMode = .photo
        picker.cameraDevice      = .rear
        picker.allowsEditing     = false
        picker.delegate          = context.coordinator
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
                parent.onImageSelected?(img)
            }
            parent.dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}

// ── Photo Library Picker ───────────────────────────────────────────────────────
struct ImageLibraryPicker: UIViewControllerRepresentable {
    @Binding var selectedImage: UIImage?
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType    = .photoLibrary
        picker.allowsEditing = false
        picker.delegate      = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController,
                                context: Context) {}

    final class Coordinator: NSObject,
                             UIImagePickerControllerDelegate,
                             UINavigationControllerDelegate {
        let parent: ImageLibraryPicker
        init(_ parent: ImageLibraryPicker) { self.parent = parent }

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
