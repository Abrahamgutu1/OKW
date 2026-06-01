// InspectionFormView.swift
// OKW FieldSync — Field inspection capture form
// ArcGIS Field Maps aesthetic: chunky inputs, high-contrast, field-optimized

import SwiftUI
import SwiftData

struct InspectionFormView: View {

    @Environment(\.modelContext) private var context
    @StateObject private var location = LocationManager()

    // Form state
    @State private var serviceLineID  = ""
    @State private var evidenceID     = ""
    @State private var capturedImage: UIImage? = nil
    @State private var showCamera     = false
    @State private var showSuccess    = false
    @State private var errorMessage   = ""
    @State private var showError      = false

    var body: some View {
        NavigationStack {
            ZStack {
                Color.fieldBackground.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 0) {

                        // ── Header bar ──────────────────────────────────────
                        headerBar

                        VStack(spacing: 16) {

                            // ── GPS status card ─────────────────────────────
                            gpsCard

                            // ── ID inputs card ──────────────────────────────
                            inputCard

                            // ── Photo capture card ──────────────────────────
                            photoCard

                            // ── Submit button ───────────────────────────────
                            submitButton

                        }
                        .padding(.horizontal, 16)
                        .padding(.top, 16)
                        .padding(.bottom, 32)
                    }
                }
            }
            .navigationBarHidden(true)
            .sheet(isPresented: $showCamera) {
                CameraPicker(selectedImage: $capturedImage)
            }
            .alert("Record Saved", isPresented: $showSuccess) {
                Button("OK") { resetForm() }
            } message: {
                Text("Inspection record queued for sync.")
            }
            .alert("Validation Error", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
        }
    }

    // ── Header ─────────────────────────────────────────────────────────────────
    private var headerBar: some View {
        HStack(spacing: 12) {
            Image(systemName: "drop.fill")
                .font(.title2)
                .foregroundColor(.white)
                .frame(width: 36, height: 36)
                .background(Color.accentTeal)
                .cornerRadius(6)

            VStack(alignment: .leading, spacing: 1) {
                Text("OKW FieldSync")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white)
                Text("Field Inspection Capture")
                    .font(.system(size: 11))
                    .foregroundColor(.white.opacity(0.7))
            }
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.navyHeader)
    }

    // ── GPS status card ────────────────────────────────────────────────────────
    private var gpsCard: some View {
        FieldCard {
            HStack(spacing: 10) {
                Image(systemName: location.hasValidFix ? "location.fill" : "location.slash")
                    .foregroundColor(location.hasValidFix ? .accentTeal : .pendingAmber)
                    .font(.title3)

                VStack(alignment: .leading, spacing: 2) {
                    SectionLabel(text: "GPS COORDINATES")
                    if location.hasValidFix {
                        Text(String(format: "%.6f,  %.6f",
                                    location.latitude, location.longitude))
                            .font(.system(size: 13, weight: .semibold, design: .monospaced))
                            .foregroundColor(.primary)
                    } else {
                        Text("Acquiring high-precision fix…")
                            .font(.system(size: 13))
                            .foregroundColor(.pendingAmber)
                    }
                }
                Spacer()

                // Accuracy badge
                Text(location.statusText)
                    .font(.system(size: 11, weight: .bold))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(location.hasValidFix
                                ? Color.safeGreen.opacity(0.15)
                                : Color.pendingAmber.opacity(0.15))
                    .foregroundColor(location.hasValidFix ? .safeGreen : .pendingAmber)
                    .cornerRadius(4)
            }
        }
    }

    // ── ID inputs card ─────────────────────────────────────────────────────────
    private var inputCard: some View {
        FieldCard {
            VStack(spacing: 14) {
                FieldInput(
                    label: "SERVICE LINE ID",
                    placeholder: "e.g.  21",
                    text: $serviceLineID,
                    keyboardType: .numberPad
                )
                Divider()
                FieldInput(
                    label: "EVIDENCE ID",
                    placeholder: "e.g.  3",
                    text: $evidenceID,
                    keyboardType: .numberPad
                )
            }
        }
    }

    // ── Photo capture card ─────────────────────────────────────────────────────
    private var photoCard: some View {
        FieldCard {
            VStack(spacing: 12) {
                HStack {
                    SectionLabel(text: "PIPE PHOTO")
                    Spacer()
                    if capturedImage != nil {
                        Text("✓ Captured")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.safeGreen)
                    }
                }

                if let img = capturedImage {
                    Image(uiImage: img)
                        .resizable()
                        .scaledToFill()
                        .frame(maxWidth: .infinity)
                        .frame(height: 200)
                        .clipped()
                        .cornerRadius(6)
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(Color.accentTeal, lineWidth: 1.5)
                        )
                }

                Button(action: { showCamera = true }) {
                    Label(
                        capturedImage == nil ? "Take Photo" : "Retake Photo",
                        systemImage: "camera"
                    )
                    .font(.system(size: 15, weight: .semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.accentTeal.opacity(0.12))
                    .foregroundColor(.accentTeal)
                    .cornerRadius(6)
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color.accentTeal, lineWidth: 1.5)
                    )
                }
            }
        }
    }

    // ── Submit button ──────────────────────────────────────────────────────────
    private var submitButton: some View {
        Button(action: saveRecord) {
            Text("Save to Sync Queue")
                .font(.system(size: 16, weight: .bold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(canSubmit ? Color.accentTeal : Color.gray.opacity(0.3))
                .foregroundColor(.white)
                .cornerRadius(6)
        }
        .disabled(!canSubmit)
    }

    // ── Validation ─────────────────────────────────────────────────────────────
    private var canSubmit: Bool {
        !serviceLineID.isEmpty &&
        !evidenceID.isEmpty &&
        capturedImage != nil &&
        location.hasValidFix
    }

    // ── Save record to SwiftData ───────────────────────────────────────────────
    private func saveRecord() {
        guard let slID = Int(serviceLineID),
              let evID = Int(evidenceID) else {
            errorMessage = "Service Line ID and Evidence ID must be valid numbers."
            showError    = true
            return
        }

        guard let image = capturedImage,
              let base64 = PhotoEncoder.encode(image) else {
            errorMessage = "Failed to encode photo. Please retake."
            showError    = true
            return
        }

        let record = InspectionRecord(
            evidenceID:    evID,
            serviceLineID: slID,
            gpsLatitude:   location.latitude,
            gpsLongitude:  location.longitude,
            gpsAccuracy:   location.accuracy,
            photoBase64:   base64
        )

        context.insert(record)
        try? context.save()
        showSuccess = true
    }

    private func resetForm() {
        serviceLineID = ""
        evidenceID    = ""
        capturedImage = nil
    }
}

// FieldCard, FieldInput, StatusBadge — defined in DesignSystem.swift
