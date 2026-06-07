// NetworkManager.swift
// OKW FieldSync — Live API sync to Oracle 23ai via Flask backend
// Replaces the AirDrop/JSON file export with direct HTTP POST

import Foundation
import UIKit
import Combine

// ── API response model ─────────────────────────────────────────────────────────
struct APIResponse: Decodable {
    let status:  String
    let message: String
}

// ── Upload result ──────────────────────────────────────────────────────────────
enum UploadResult {
    case success(String)
    case failure(String)
}

// ── Network Manager ────────────────────────────────────────────────────────────
final class NetworkManager: ObservableObject {

    // MARK: - Configuration
    //
    // When running on iPhone Simulator: use "localhost"
    // When running on a real iPhone:    use your Mac's local IP address
    //   → Find it: System Settings → Wi-Fi → Details → IP Address
    //   → Example: "192.168.1.42"
    //
    static let macIPAddress = "localhost"  // ← change to Mac IP for real device
    static let apiPort      = 8000
    static let baseURL      = "http://\(macIPAddress):\(apiPort)"

    // MARK: - Published state (for SwiftUI binding)
    @Published var isUploading  = false
    @Published var lastMessage  = ""
    @Published var uploadSuccess = false

    // MARK: - Health Check
    /// Call this on app launch to confirm the API is reachable
    func checkHealth(completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(Self.baseURL)/health") else {
            completion(false)
            return
        }
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard error == nil,
                  let http = response as? HTTPURLResponse,
                  http.statusCode == 200 else {
                completion(false)
                return
            }
            completion(true)
        }.resume()
    }

    // MARK: - Upload Inspection Record
    func uploadInspection(
        serviceLineID: Int,
        evidenceID:    Int,
        latitude:      Double,
        longitude:     Double,
        accuracy:      Double,
        image:         UIImage,
        completion:    @escaping (UploadResult) -> Void
    ) {
        guard let url = URL(string: "\(Self.baseURL)/api/upload_inspection") else {
            completion(.failure("Invalid API URL"))
            return
        }

        // Compress image to JPEG at 0.75 quality — matches sync_processor.py
        guard let jpegData = image.jpegData(compressionQuality: 0.4) else {
            completion(.failure("Failed to encode image as JPEG"))
            return
        }

        // Clean raw Base64 — no data-URI prefix, no line breaks
        let base64String = jpegData.base64EncodedString(options: [])

        // Build JSON payload — matches Flask API + sync_processor.py schema
        let payload: [String: Any] = [
            "evidence_id":     evidenceID,
            "service_line_id": serviceLineID,
            "latitude":        latitude,
            "longitude":       longitude,
            "accuracy":        accuracy,
            "image_base64":    base64String
        ]

        guard let body = try? JSONSerialization.data(withJSONObject: payload) else {
            completion(.failure("Failed to serialize JSON payload"))
            return
        }

        var request        = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody   = body
        request.timeoutInterval = 60

        DispatchQueue.main.async { self.isUploading = true }

        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isUploading = false
            }

            // Network error
            if let error = error {
                completion(.failure("Network error: \(error.localizedDescription)"))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                completion(.failure("No response from server"))
                return
            }

            guard let data = data,
                  let decoded = try? JSONDecoder().decode(APIResponse.self, from: data) else {
                completion(.failure("Could not parse server response (HTTP \(http.statusCode))"))
                return
            }

            if http.statusCode == 201 {
                DispatchQueue.main.async {
                    self?.lastMessage   = decoded.message
                    self?.uploadSuccess = true
                }
                completion(.success(decoded.message))
            } else {
                completion(.failure("Server error: \(decoded.message)"))
            }
        }.resume()
    }
}
