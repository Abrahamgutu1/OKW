// InspectionFormView.swift
// OKW FieldSync — Field inspection capture form
// ArcGIS Field Maps aesthetic: chunky inputs, high-contrast, field-optimized

import SwiftUI
import SwiftData

struct InspectionFormView: View {

    @Environment(\.modelContext) private var context
    @StateObject private var location       = LocationManager()
    @State private var selectedMaterial: String = ""

    // Form state
    @State private var serviceLineID  = ""
    @State private var evidenceID     = ""
    @State private var capturedImage: UIImage? = nil
    @State private var showCamera     = false
    @State private var showImagePicker = false
    @State private var showSuccess    = false
    @State private var errorMessage   = ""
    @State private var showError      = false

    enum Field { case serviceLineID, evidenceID }
    @FocusState private var focusedField: Field?

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

                            // ── Material picker card ─────────────────────────
                            materialPickerCard

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
            .scrollDismissesKeyboard(.interactively)
            .onTapGesture { focusedField = nil }
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    if focusedField == .serviceLineID {
                        Button("Next") { focusedField = .evidenceID }
                            .fontWeight(.semibold)
                            .foregroundColor(.accentTeal)
                    } else {
                        Button("Done") { focusedField = nil }
                            .fontWeight(.semibold)
                            .foregroundColor(.accentTeal)
                    }
                }
            }
            .sheet(isPresented: $showCamera) {
                CameraPicker(selectedImage: $capturedImage)
            }
            .sheet(isPresented: $showImagePicker) {
                ImageLibraryPicker(selectedImage: $capturedImage)
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
                VStack(alignment: .leading, spacing: 6) {
                    SectionLabel(text: "SERVICE LINE ID")
                    TextField("e.g.  21", text: $serviceLineID)
                        .keyboardType(.numberPad)
                        .focused($focusedField, equals: .serviceLineID)
                        .font(.bodyLarge)
                        .foregroundColor(.textPrimary)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 13)
                        .background(Color.inputBG)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 10, style: .continuous)
                                .stroke(serviceLineID.isEmpty ? Color.borderSubtle : Color.brand.opacity(0.6), lineWidth: 1)
                        )
                }
                Divider()
                VStack(alignment: .leading, spacing: 6) {
                    SectionLabel(text: "EVIDENCE ID")
                    TextField("e.g.  3", text: $evidenceID)
                        .keyboardType(.numberPad)
                        .focused($focusedField, equals: .evidenceID)
                        .font(.bodyLarge)
                        .foregroundColor(.textPrimary)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 13)
                        .background(Color.inputBG)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 10, style: .continuous)
                                .stroke(evidenceID.isEmpty ? Color.borderSubtle : Color.brand.opacity(0.6), lineWidth: 1)
                        )
                }
            }
            .padding(14)
        }
        .contentShape(Rectangle())
        .onTapGesture { focusedField = nil }
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

                HStack(spacing: 10) {
                    // Camera button
                    Button(action: { showCamera = true }) {
                        Label("Camera", systemImage: "camera")
                            .font(.system(size: 14, weight: .semibold))
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
                    // Photo library button
                    Button(action: { showImagePicker = true }) {
                        Label("Library", systemImage: "photo.on.rectangle")
                            .font(.system(size: 14, weight: .semibold))
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
    }

    // ── Manual material picker card ───────────────────────────────────────────
    private let materials: [(label: String, color: Color, risk: String)] = [
        ("Lead",        .dangerRed,    "HIGH"),
        ("Galvanized",  .pendingAmber, "MEDIUM"),
        ("Copper",      .safeGreen,    "LOW"),
        ("PVC",         .safeGreen,    "LOW"),
        ("Unknown",     .labelGray,    "HIGH")
    ]

    private var materialPickerCard: some View {
        FieldCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "wrench.and.screwdriver.fill")
                        .foregroundColor(.accentTeal)
                        .font(.system(size: 13))
                    SectionLabel(text: "PIPE MATERIAL")
                    Spacer()
                    if !selectedMaterial.isEmpty {
                        Text("✓ Selected")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.safeGreen)
                    }
                }

                // Material buttons grid
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 8) {
                    ForEach(materials, id: \.label) { material in
                        Button(action: { selectedMaterial = material.label }) {
                            VStack(spacing: 4) {
                                Text(material.label)
                                    .font(.system(size: 13, weight: .semibold))
                                Text(material.risk)
                                    .font(.system(size: 9, weight: .bold))
                                    .opacity(0.7)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(selectedMaterial == material.label
                                ? material.color.opacity(0.25)
                                : Color.inputBG)
                            .foregroundColor(selectedMaterial == material.label
                                ? material.color
                                : .labelGray)
                            .cornerRadius(6)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(selectedMaterial == material.label
                                        ? material.color
                                        : Color.borderSubtle, lineWidth: 1.5)
                            )
                        }
                    }
                }

                // Risk hint
                if !selectedMaterial.isEmpty,
                   let mat = materials.first(where: { $0.label == selectedMaterial }) {
                    HStack(spacing: 6) {
                        Circle()
                            .fill(mat.color)
                            .frame(width: 7, height: 7)
                        Text(riskLabel(selectedMaterial))
                            .font(.system(size: 11))
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding(14)
        }
    }

    // ── Risk helpers ───────────────────────────────────────────────────────────
    private func riskLabel(_ material: String) -> String {
        switch material {
        case "Lead":       return "HIGH risk — replace required per LCRI §141.84"
        case "Galvanized": return "MEDIUM risk — GRR classification, replacement required"
        case "Copper":     return "LOW risk — non-lead material, no replacement required"
        case "PVC":        return "LOW risk — non-lead material, no replacement required"
        case "Unknown":    return "HIGH risk — treat as lead per LCRI §141.84(b)"
        default:           return ""
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
        location.hasValidFix &&
        !selectedMaterial.isEmpty
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

        let riskForMaterial: String = {
            switch selectedMaterial {
            case "Lead", "Unknown": return "HIGH"
            case "Galvanized":      return "MEDIUM"
            default:                return "LOW"
            }
        }()

        let record = InspectionRecord(
            evidenceID:          evID,
            serviceLineID:       slID,
            gpsLatitude:         location.latitude,
            gpsLongitude:        location.longitude,
            gpsAccuracy:         location.accuracy,
            photoBase64:         base64,
            visionLabels:        selectedMaterial.lowercased(),
            visionColor:         "",
            visionPipeConfirmed: "1",
            visionConfidence:    riskForMaterial
        )

        context.insert(record)
        try? context.save()
        showSuccess = true
    }

    private func resetForm() {
        serviceLineID    = ""
        evidenceID       = ""
        capturedImage    = nil
        selectedMaterial = ""
    }
}
