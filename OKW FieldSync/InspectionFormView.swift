// InspectionFormView.swift
// OKW FieldSync — ArcGIS Field Maps + Fulcrum + FedEx design pattern

import SwiftUI
import SwiftData
import MapKit

struct InspectionFormView: View {

    @Environment(\.modelContext) private var context
    @StateObject private var location = LocationManager()
    @State private var selectedMaterial: String = ""
    @State private var serviceLineID  = ""
    @State private var evidenceID     = ""
    @State private var capturedImage: UIImage? = nil
    @State private var showCamera     = false
    @State private var showImagePicker = false
    @State private var showSuccess    = false
    @State private var errorMessage   = ""
    @State private var showError      = false
    @State private var drawerExpanded = true

    enum Field { case serviceLineID, evidenceID }
    @FocusState private var focusedField: Field?

    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 35.2226, longitude: -97.4395),
        span: MKCoordinateSpan(latitudeDelta: 0.003, longitudeDelta: 0.003)
    )

    var body: some View {
        ZStack(alignment: .bottom) {
            mapView.ignoresSafeArea()
            VStack {
                statusBanner
                Spacer()
            }
            bottomDrawer
        }
        .ignoresSafeArea(edges: .bottom)
        .onReceive(location.$latitude) { lat in
            if lat != 0 {
                withAnimation(.easeInOut(duration: 0.5)) {
                    region.center = CLLocationCoordinate2D(
                        latitude: location.latitude,
                        longitude: location.longitude
                    )
                }
            }
        }
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                if focusedField == .serviceLineID {
                    Button("Next") { focusedField = .evidenceID }
                        .fontWeight(.semibold).foregroundColor(.accentTeal)
                } else {
                    Button("Done") { focusedField = nil }
                        .fontWeight(.semibold).foregroundColor(.accentTeal)
                }
            }
        }
        .sheet(isPresented: $showCamera) { CameraPicker(selectedImage: $capturedImage) }
        .sheet(isPresented: $showImagePicker) { ImageLibraryPicker(selectedImage: $capturedImage) }
        .alert("Record Saved", isPresented: $showSuccess) {
            Button("OK") { resetForm() }
        } message: { Text("Inspection record queued for sync.") }
        .alert("Validation Error", isPresented: $showError) {
            Button("OK", role: .cancel) {}
        } message: { Text(errorMessage) }
    }

    private var mapView: some View {
        Map(coordinateRegion: $region, showsUserLocation: true)
    }

    private var statusBanner: some View {
        HStack(spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "drop.fill")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.accentTeal)
                Text("OKW FieldSync")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
            }.padding(.horizontal, 12)
            Divider().frame(height: 20)
            HStack(spacing: 4) {
                Image(systemName: location.hasValidFix ? "location.fill" : "location.slash")
                    .font(.system(size: 10))
                    .foregroundColor(location.hasValidFix ? .safeGreen : .pendingAmber)
                Text(location.hasValidFix
                     ? String(format: "GPS ±%.0fm", location.accuracy)
                     : "Acquiring GPS…")
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .foregroundColor(location.hasValidFix ? .safeGreen : .pendingAmber)
            }.padding(.horizontal, 10)
            Divider().frame(height: 20)
            HStack(spacing: 4) {
                Circle().fill(Color.safeGreen).frame(width: 5, height: 5)
                Text("LOCAL DB OK")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundColor(.safeGreen)
            }.padding(.horizontal, 10)
            Spacer()
        }
        .frame(height: 36)
        .background(Color.navyHeader.opacity(0.95))
        .padding(.top, 50)
    }

    private var bottomDrawer: some View {
        VStack(spacing: 0) {
            Button(action: {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) {
                    drawerExpanded.toggle()
                }
            }) {
                VStack(spacing: 6) {
                    Capsule()
                        .fill(Color.labelGray.opacity(0.5))
                        .frame(width: 36, height: 4)
                    HStack {
                        Text("FIELD CAPTURE")
                            .font(.system(size: 10, weight: .black))
                            .foregroundColor(.labelGray)
                            .tracking(1.5)
                        Spacer()
                        completionBadge
                        Image(systemName: drawerExpanded ? "chevron.down" : "chevron.up")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.labelGray)
                    }.padding(.horizontal, 20)
                }
                .padding(.top, 10).padding(.bottom, 8)
                .background(Color.cardBackground)
            }.buttonStyle(.plain)

            if drawerExpanded {
                ScrollView {
                    VStack(spacing: 14) {
                        idInputSection
                        photoSection
                        materialSection
                        submitSection
                    }
                    .padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 40)
                }
                .frame(maxHeight: 460)
                .background(Color.fieldBackground)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            } else {
                collapsedSummary
            }
        }
        .background(Color.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: .black.opacity(0.4), radius: 20, x: 0, y: -4)
    }

    private var completionBadge: some View {
        let steps = [!serviceLineID.isEmpty, !evidenceID.isEmpty,
                     capturedImage != nil, !selectedMaterial.isEmpty]
        let done = steps.filter { $0 }.count
        return HStack(spacing: 3) {
            ForEach(0..<4, id: \.self) { i in
                RoundedRectangle(cornerRadius: 2)
                    .fill(i < done ? Color.accentTeal : Color.borderSubtle)
                    .frame(width: 18, height: 4)
            }
        }
    }

    private var collapsedSummary: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text("COORDINATES")
                    .font(.system(size: 8, weight: .bold))
                    .foregroundColor(.labelGray).tracking(0.8)
                Text(location.hasValidFix
                     ? String(format: "%.5f, %.5f", location.latitude, location.longitude)
                     : "Acquiring…")
                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                    .foregroundColor(location.hasValidFix ? .primary : .pendingAmber)
            }
            Spacer()
            if !selectedMaterial.isEmpty,
               let mat = materials.first(where: { $0.label == selectedMaterial }) {
                Text(selectedMaterial.uppercased())
                    .font(.system(size: 10, weight: .black))
                    .padding(.horizontal, 10).padding(.vertical, 4)
                    .background(mat.color).foregroundColor(.white).cornerRadius(4)
            }
        }
        .padding(.horizontal, 20).padding(.vertical, 12)
        .background(Color.fieldBackground)
    }

    private var idInputSection: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 5) {
                Text("SERVICE LINE ID")
                    .font(.system(size: 9, weight: .black))
                    .foregroundColor(.labelGray).tracking(1)
                TextField("e.g. 21", text: $serviceLineID)
                    .keyboardType(.numberPad)
                    .focused($focusedField, equals: .serviceLineID)
                    .font(.system(size: 22, weight: .bold, design: .monospaced))
                    .foregroundColor(.textPrimary)
                    .padding(14).background(Color.inputBG).cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8)
                        .stroke(!serviceLineID.isEmpty ? Color.accentTeal : Color.borderSubtle, lineWidth: 1.5))
            }
            VStack(alignment: .leading, spacing: 5) {
                Text("EVIDENCE ID")
                    .font(.system(size: 9, weight: .black))
                    .foregroundColor(.labelGray).tracking(1)
                TextField("e.g. 3", text: $evidenceID)
                    .keyboardType(.numberPad)
                    .focused($focusedField, equals: .evidenceID)
                    .font(.system(size: 22, weight: .bold, design: .monospaced))
                    .foregroundColor(.textPrimary)
                    .padding(14).background(Color.inputBG).cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8)
                        .stroke(!evidenceID.isEmpty ? Color.accentTeal : Color.borderSubtle, lineWidth: 1.5))
            }
        }
        .contentShape(Rectangle()).onTapGesture { focusedField = nil }
    }

    private var photoSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("PIPE PHOTO")
                    .font(.system(size: 9, weight: .black))
                    .foregroundColor(.labelGray).tracking(1)
                Spacer()
                if capturedImage != nil {
                    Label("Captured", systemImage: "checkmark.circle.fill")
                        .font(.system(size: 10, weight: .bold)).foregroundColor(.safeGreen)
                }
            }
            if let img = capturedImage {
                Image(uiImage: img).resizable().scaledToFill()
                    .frame(maxWidth: .infinity).frame(height: 130).clipped().cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.accentTeal, lineWidth: 1.5))
            }
            HStack(spacing: 10) {
                Button(action: { showCamera = true }) {
                    HStack(spacing: 6) {
                        Image(systemName: "camera.fill").font(.system(size: 16))
                        Text(capturedImage == nil ? "Camera" : "Retake")
                            .font(.system(size: 14, weight: .bold))
                    }
                    .frame(maxWidth: .infinity).padding(.vertical, 14)
                    .background(capturedImage == nil ? Color.accentTeal : Color.accentTeal.opacity(0.15))
                    .foregroundColor(capturedImage == nil ? .white : .accentTeal)
                    .cornerRadius(8)
                }
                Button(action: { showImagePicker = true }) {
                    HStack(spacing: 6) {
                        Image(systemName: "photo.on.rectangle").font(.system(size: 16))
                        Text("Library").font(.system(size: 14, weight: .bold))
                    }
                    .frame(maxWidth: .infinity).padding(.vertical, 14)
                    .background(Color.inputBG).foregroundColor(.labelGray).cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderSubtle, lineWidth: 1.5))
                }
            }
        }
    }

    private let materials: [(label: String, color: Color, risk: String, icon: String)] = [
        ("Lead",       .dangerRed,    "HIGH",   "exclamationmark.triangle.fill"),
        ("Galvanized", .pendingAmber, "MEDIUM", "minus.circle.fill"),
        ("Copper",     .safeGreen,    "LOW",    "checkmark.circle.fill"),
        ("PVC",        .safeGreen,    "LOW",    "checkmark.circle.fill"),
        ("Unknown",    .labelGray,    "HIGH",   "questionmark.circle.fill")
    ]

    private var materialSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("PIPE MATERIAL")
                .font(.system(size: 9, weight: .black))
                .foregroundColor(.labelGray).tracking(1)
            LazyVGrid(columns: [
                GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())
            ], spacing: 8) {
                ForEach(materials, id: \.label) { mat in
                    let isSelected = selectedMaterial == mat.label
                    Button(action: { selectedMaterial = mat.label }) {
                        VStack(spacing: 5) {
                            Image(systemName: mat.icon).font(.system(size: 18, weight: .bold))
                            Text(mat.label).font(.system(size: 13, weight: .black))
                            Text(mat.risk).font(.system(size: 11, weight: .heavy)).tracking(0.5)
                        }
                        .frame(maxWidth: .infinity).padding(.vertical, 14)
                        .background(isSelected ? mat.color : Color.inputBG)
                        .foregroundColor(isSelected ? .white : mat.color)
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8)
                            .stroke(isSelected ? mat.color : Color.borderSubtle,
                                    lineWidth: isSelected ? 0 : 1.5))
                        .shadow(color: isSelected ? mat.color.opacity(0.4) : .clear, radius: 6, x: 0, y: 3)
                        .scaleEffect(isSelected ? 1.03 : 1.0)
                        .animation(.spring(response: 0.2), value: isSelected)
                    }
                }
            }
            if !selectedMaterial.isEmpty,
               let mat = materials.first(where: { $0.label == selectedMaterial }) {
                HStack(spacing: 6) {
                    Image(systemName: mat.icon).font(.system(size: 10)).foregroundColor(mat.color)
                    Text(riskLabel(selectedMaterial)).font(.system(size: 10)).foregroundColor(.secondary)
                }.padding(.top, 2)
            }
        }
    }

    private var submitSection: some View {
        Button(action: saveRecord) {
            HStack(spacing: 10) {
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 18))
                Text("Save to Sync Queue").font(.system(size: 16, weight: .black))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 18)
            .background(canSubmit ? Color.accentTeal : Color.gray.opacity(0.3))
            .foregroundColor(.white).cornerRadius(10)
            .shadow(color: canSubmit ? Color.accentTeal.opacity(0.4) : .clear, radius: 8, x: 0, y: 4)
        }.disabled(!canSubmit)
    }

    private var canSubmit: Bool {
        !serviceLineID.isEmpty && !evidenceID.isEmpty &&
        capturedImage != nil && location.hasValidFix && !selectedMaterial.isEmpty
    }

    private func riskLabel(_ material: String) -> String {
        switch material {
        case "Lead":       return "HIGH risk — replacement required per LCRI §141.84"
        case "Galvanized": return "MEDIUM risk — GRR classification, replacement required"
        case "Copper":     return "LOW risk — non-lead, no replacement required"
        case "PVC":        return "LOW risk — non-lead, no replacement required"
        case "Unknown":    return "HIGH risk — treat as lead per LCRI §141.84(b)"
        default:           return ""
        }
    }

    private func saveRecord() {
        guard let slID = Int(serviceLineID), let evID = Int(evidenceID) else {
            errorMessage = "Service Line ID and Evidence ID must be valid numbers."
            showError = true; return
        }
        guard let image = capturedImage, let base64 = PhotoEncoder.encode(image) else {
            errorMessage = "Failed to encode photo. Please retake."
            showError = true; return
        }
        let risk: String = {
            switch selectedMaterial {
            case "Lead", "Unknown": return "HIGH"
            case "Galvanized":      return "MEDIUM"
            default:                return "LOW"
            }
        }()
        let record = InspectionRecord(
            evidenceID: evID, serviceLineID: slID,
            gpsLatitude: location.latitude, gpsLongitude: location.longitude,
            gpsAccuracy: location.accuracy, photoBase64: base64,
            visionLabels: selectedMaterial.lowercased(),
            visionColor: "", visionPipeConfirmed: "1", visionConfidence: risk
        )
        context.insert(record)
        try? context.save()
        showSuccess = true
    }

    private func resetForm() {
        serviceLineID = ""; evidenceID = ""
        capturedImage = nil; selectedMaterial = ""
        withAnimation { drawerExpanded = true }
    }
}
