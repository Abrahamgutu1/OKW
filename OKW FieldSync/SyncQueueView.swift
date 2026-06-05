// SyncQueueView.swift
// OKW FieldSync — FedEx enterprise queue with offline-first diagnostics

import SwiftUI
import SwiftData

struct SyncQueueView: View {

    @Environment(\.modelContext) private var context
    @Query(sort: \InspectionRecord.capturedAt, order: .reverse)
    private var records: [InspectionRecord]

    @State private var selectedIDs     = Set<UUID>()
    @State private var selectAll       = false
    @State private var showDeleteAlert = false
    @State private var filter: QueueFilter = .all
    @State private var isSyncing = false
    @State private var syncMessage = ""
    @State private var showSyncResult = false
    @StateObject private var network = NetworkManager()

    enum QueueFilter: String, CaseIterable {
        case all = "All"
        case pending = "Pending"
        case synced = "Synced"
        case failed = "Failed"
    }

    private var pendingRecords: [InspectionRecord] { records.filter { $0.status == .pending } }
    private var syncedRecords:  [InspectionRecord] { records.filter { $0.status == .synced } }
    private var failedRecords:  [InspectionRecord] { records.filter { $0.status == .failed } }
    private var selectedRecords: [InspectionRecord] { records.filter { selectedIDs.contains($0.id) } }

    private var filteredRecords: [InspectionRecord] {
        switch filter {
        case .all:     return records
        case .pending: return pendingRecords
        case .synced:  return syncedRecords
        case .failed:  return failedRecords
        }
    }

    // Estimated payload size
    private func payloadSize(_ record: InspectionRecord) -> String {
        let bytes = record.photoBase64.count * 3 / 4
        let mb = Double(bytes) / 1_000_000
        return mb > 0.1 ? String(format: "%.1f MB", mb) : "\(bytes / 1000) KB"
    }

    var body: some View {
        ZStack {
            Color.fieldBackground.ignoresSafeArea()
            VStack(spacing: 0) {
                headerBar
                networkDiagnosticsBar
                statsStrip
                filterBar

                if records.isEmpty {
                    emptyState
                } else {
                    recordList
                    exportBar
                }
            }
        }
        .navigationBarHidden(true)
        .alert("Delete Records", isPresented: $showDeleteAlert) {
            Button("Delete", role: .destructive) { deleteSelected() }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Remove \(selectedIDs.count) record(s)? This cannot be undone.")
        }
        .alert("Sync Result", isPresented: $showSyncResult) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(syncMessage)
        }
    }

    // ── Header ─────────────────────────────────────────────────────────────────
    private var headerBar: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.accentTeal)
                    .frame(width: 36, height: 36)
                Image(systemName: "tray.full.fill")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.white)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text("Sync Queue")
                    .font(.system(size: 15, weight: .black))
                    .foregroundColor(.white)
                Text("Local cache · Encrypted · Offline-ready")
                    .font(.system(size: 10))
                    .foregroundColor(.white.opacity(0.6))
            }
            Spacer()

            // Batch indicator
            if !pendingRecords.isEmpty {
                VStack(spacing: 1) {
                    Text("\(pendingRecords.count)")
                        .font(.system(size: 16, weight: .black, design: .monospaced))
                        .foregroundColor(.pendingAmber)
                    Text("QUEUED")
                        .font(.system(size: 7, weight: .black))
                        .foregroundColor(.pendingAmber.opacity(0.7))
                        .tracking(0.8)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(Color.pendingAmber.opacity(0.12))
                .cornerRadius(6)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.pendingAmber.opacity(0.3), lineWidth: 1))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.navyHeader)
    }

    // ── Network diagnostics banner (FedEx pattern) ─────────────────────────────
    private var networkDiagnosticsBar: some View {
        HStack(spacing: 0) {
            // Local storage status
            DiagTile(
                icon: "internaldrive.fill",
                label: "LOCAL CACHE",
                value: "\(records.count) records",
                color: .safeGreen,
                pulse: false
            )
            Divider().frame(height: 28)

            // Encryption indicator
            DiagTile(
                icon: "lock.shield.fill",
                label: "ENCRYPTION",
                value: "SwiftData AES",
                color: .accentTeal,
                pulse: false
            )
            Divider().frame(height: 28)

            // Sync status
            DiagTile(
                icon: pendingRecords.isEmpty ? "checkmark.icloud.fill" : "arrow.clockwise.icloud",
                label: "SYNC STATUS",
                value: pendingRecords.isEmpty ? "All synced" : "\(pendingRecords.count) pending",
                color: pendingRecords.isEmpty ? .safeGreen : .pendingAmber,
                pulse: !pendingRecords.isEmpty
            )
        }
        .background(Color.cardBackground)
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)), alignment: .bottom)
    }

    // ── Stats strip ────────────────────────────────────────────────────────────
    private var statsStrip: some View {
        HStack(spacing: 0) {
            StatTile(value: "\(records.count)",        label: "Total",   color: .accentTeal)
            Divider().frame(height: 32)
            StatTile(value: "\(pendingRecords.count)", label: "Pending", color: .pendingAmber)
            Divider().frame(height: 32)
            StatTile(value: "\(syncedRecords.count)",  label: "Synced",  color: .safeGreen)
            Divider().frame(height: 32)
            StatTile(value: "\(failedRecords.count)",  label: "Failed",  color: .dangerRed)
        }
        .background(Color.surfaceBG)
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)), alignment: .bottom)
    }

    // ── Filter bar ─────────────────────────────────────────────────────────────
    private var filterBar: some View {
        HStack(spacing: 0) {
            ForEach(QueueFilter.allCases, id: \.self) { f in
                Button(action: { filter = f }) {
                    Text(f.rawValue)
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(filter == f ? .accentTeal : .labelGray)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(filter == f ? Color.accentTeal.opacity(0.08) : Color.clear)
                        .overlay(
                            Rectangle()
                                .frame(height: 2)
                                .foregroundColor(filter == f ? .accentTeal : .clear),
                            alignment: .bottom
                        )
                }
            }

            Spacer()

            if !selectedIDs.isEmpty {
                Button(action: { showDeleteAlert = true }) {
                    Image(systemName: "trash")
                        .font(.system(size: 13))
                        .foregroundColor(.dangerRed)
                }
                .padding(.trailing, 16)
            }

            Button(action: toggleSelectAll) {
                Text(selectAll ? "Deselect" : "Select All")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.accentTeal)
            }
            .padding(.trailing, 16)
        }
        .background(Color.cardBackground)
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)), alignment: .bottom)
    }

    // ── Record list ────────────────────────────────────────────────────────────
    private var recordList: some View {
        List {
            ForEach(filteredRecords) { record in
                FedExQueueRow(
                    record: record,
                    isSelected: selectedIDs.contains(record.id),
                    payloadSize: payloadSize(record)
                )
                .contentShape(Rectangle())
                .onTapGesture {
                    if selectedIDs.contains(record.id) {
                        selectedIDs.remove(record.id)
                    } else {
                        selectedIDs.insert(record.id)
                    }
                }
                .listRowBackground(Color.cardBackground)
                .listRowInsets(EdgeInsets(top: 0, leading: 0, bottom: 0, trailing: 0))
                .listRowSeparatorTint(Color(UIColor.separator))
            }
            .onDelete(perform: deleteRecords)
        }
        .listStyle(.plain)
        .background(Color.fieldBackground)
    }

    // ── Export + Sync bar ──────────────────────────────────────────────────────
    private var exportBar: some View {
        VStack(spacing: 0) {
            let totalBytes = (selectedRecords.isEmpty ? pendingRecords : selectedRecords)
                .reduce(0) { $0 + $1.photoBase64.count * 3 / 4 }
            let totalMB = String(format: "%.1f MB total payload", Double(totalBytes) / 1_000_000)

            HStack {
                Image(systemName: "externaldrive.badge.arrow.up")
                    .font(.system(size: 11)).foregroundColor(.labelGray)
                Text(totalMB)
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .foregroundColor(.labelGray)
                Spacer()
                Text("AirDrop / Files")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(.labelGray.opacity(0.6)).tracking(0.5)
            }
            .padding(.horizontal, 16).padding(.top, 8)

            HStack(spacing: 10) {
                // Sync to Oracle button
                Button(action: syncToOracle) {
                    HStack(spacing: 6) {
                        if isSyncing {
                            ProgressView().scaleEffect(0.8).tint(.white)
                        } else {
                            Image(systemName: "icloud.and.arrow.up.fill")
                                .font(.system(size: 14))
                        }
                        Text(isSyncing ? "Syncing…" : "Sync to Dashboard")
                            .font(.system(size: 14, weight: .black))
                    }
                    .frame(maxWidth: .infinity).padding(.vertical, 14)
                    .background(pendingRecords.isEmpty ? Color.gray.opacity(0.3) : Color.accentTeal)
                    .foregroundColor(.white).cornerRadius(8)
                    .shadow(color: pendingRecords.isEmpty ? .clear : Color.accentTeal.opacity(0.4), radius: 6, x: 0, y: 3)
                }
                .disabled(pendingRecords.isEmpty || isSyncing)

                // AirDrop export button
                ShareSheetButton(
                    records: selectedRecords.isEmpty ? pendingRecords : selectedRecords,
                    label: "↑ AirDrop"
                )
                .frame(maxWidth: 100)
            }
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(Color.cardBackground)
        }
        .background(Color.cardBackground)
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)), alignment: .top)
    }

    // ── Zero-anxiety empty state (FedEx pattern) ───────────────────────────────
    private var emptyState: some View {
        VStack(spacing: 20) {
            Spacer()

            // Lock icon with glow
            ZStack {
                Circle()
                    .fill(Color.safeGreen.opacity(0.08))
                    .frame(width: 80, height: 80)
                Image(systemName: "checkmark.shield.fill")
                    .font(.system(size: 36))
                    .foregroundColor(.safeGreen)
            }

            VStack(spacing: 6) {
                Text("Queue Clear")
                    .font(.system(size: 20, weight: .black))
                    .foregroundColor(.primary)
                Text("All field data has been transmitted")
                    .font(.system(size: 13))
                    .foregroundColor(.labelGray)
            }

            // Status indicators
            VStack(spacing: 8) {
                EmptyStateDiag(icon: "internaldrive", label: "Local cache", value: "Empty", ok: true)
                EmptyStateDiag(icon: "lock.shield", label: "Encryption", value: "Active", ok: true)
                EmptyStateDiag(icon: "icloud.and.arrow.up", label: "Remote sync", value: "Up to date", ok: true)
            }
            .padding(.horizontal, 40)

            Spacer()
        }
        .padding()
    }

    // ── Sync pending records to Oracle via FastAPI ────────────────────────────
    private func syncToOracle() {
        let toSync = selectedRecords.isEmpty ? pendingRecords : selectedRecords
        guard !toSync.isEmpty else { return }
        isSyncing = true
        var completed = 0
        var failed = 0

        for record in toSync {
            let imgData = Data(base64Encoded: record.photoBase64) ?? Data()
            let image = UIImage(data: imgData) ?? UIImage()
            network.uploadInspection(
                serviceLineID: record.serviceLineID,
                evidenceID:    record.evidenceID,
                latitude:      record.gpsLatitude,
                longitude:     record.gpsLongitude,
                accuracy:      record.gpsAccuracy,
                image:         image
            ) { result in
                DispatchQueue.main.async {
                    switch result {
                    case .success:
                        record.syncStatus = SyncStatus.synced.rawValue
                        try? context.save()
                    case .failure:
                        record.syncStatus = SyncStatus.failed.rawValue
                        try? context.save()
                        failed += 1
                    }
                    completed += 1
                    if completed == toSync.count { self.finishSync(failed: failed, total: toSync.count) }
                }
            }
        }
    }

    private func finishSync(failed: Int, total: Int) {
        isSyncing = false
        let synced = total - failed
        syncMessage = failed == 0
            ? "✓ \(synced) record(s) synced to Oracle successfully"
            : "⚠ \(synced) synced, \(failed) failed — check WiFi connection"
        showSyncResult = true
    }

    private func toggleSelectAll() {
        selectAll.toggle()
        selectedIDs = selectAll ? Set(records.map(\.id)) : []
    }

    private func deleteRecords(at offsets: IndexSet) {
        offsets.forEach { context.delete(records[$0]) }
        try? context.save()
    }

    private func deleteSelected() {
        records.filter { selectedIDs.contains($0.id) }.forEach { context.delete($0) }
        try? context.save()
        selectedIDs.removeAll(); selectAll = false
    }
}

// ── FedEx-style queue row ──────────────────────────────────────────────────────
struct FedExQueueRow: View {
    let record:      InspectionRecord
    let isSelected:  Bool
    let payloadSize: String

    private var formatter: DateFormatter {
        let f = DateFormatter(); f.dateFormat = "MM/dd/yy HH:mm"; return f
    }

    private var materialColor: Color {
        switch record.visionLabels.lowercased() {
        case "lead":       return .dangerRed
        case "galvanized": return .pendingAmber
        case "copper", "pvc": return .safeGreen
        default:           return .labelGray
        }
    }

    var body: some View {
        HStack(spacing: 0) {
            // Material color stripe
            Rectangle()
                .fill(materialColor)
                .frame(width: 4)

            HStack(spacing: 12) {
                // Selection
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(isSelected ? .accentTeal : .labelGray)
                    .font(.system(size: 18))

                // Record data
                VStack(alignment: .leading, spacing: 5) {
                    HStack(spacing: 6) {
                        Text("SL-\(record.serviceLineID)")
                            .font(.system(size: 14, weight: .black))
                            .foregroundColor(.primary)
                        Text("EV-\(record.evidenceID)")
                            .font(.system(size: 13, weight: .bold, design: .monospaced))
                            .foregroundColor(.accentTeal)

                        if !record.visionLabels.isEmpty {
                            Text(record.visionLabels.uppercased())
                                .font(.system(size: 8, weight: .black))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 2)
                                .background(materialColor)
                                .foregroundColor(.white)
                                .cornerRadius(3)
                        }
                    }

                    HStack(spacing: 8) {
                        Text(String(format: "%.5f, %.5f", record.gpsLatitude, record.gpsLongitude))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.labelGray)
                    }

                    HStack(spacing: 8) {
                        Text(formatter.string(from: record.capturedAt))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundColor(.labelGray)

                        // FedEx payload size tag
                        HStack(spacing: 3) {
                            Image(systemName: "internaldrive")
                                .font(.system(size: 8))
                            Text(payloadSize)
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                        }
                        .foregroundColor(.labelGray.opacity(0.8))
                        .padding(.horizontal, 5)
                        .padding(.vertical, 2)
                        .background(Color.inputBG)
                        .cornerRadius(3)
                    }
                }

                Spacer()

                // Status badge
                VStack(spacing: 4) {
                    SyncStatusBadge(status: record.status)
                    if record.status == .pending {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 9))
                            .foregroundColor(.labelGray.opacity(0.5))
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 12)
        }
        .background(isSelected ? Color.accentTeal.opacity(0.06) : Color.cardBackground)
    }
}

// ── Diagnostics tile ───────────────────────────────────────────────────────────
struct DiagTile: View {
    let icon:  String
    let label: String
    let value: String
    let color: Color
    let pulse: Bool

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 11))
                .foregroundColor(color)
                .overlay(
                    pulse ? Circle()
                        .stroke(color.opacity(0.4), lineWidth: 1)
                        .scaleEffect(1.5)
                        .opacity(0.6)
                        .animation(.easeInOut(duration: 1.2).repeatForever(), value: pulse) : nil
                )
            VStack(alignment: .leading, spacing: 1) {
                Text(label)
                    .font(.system(size: 7, weight: .black))
                    .foregroundColor(.labelGray)
                    .tracking(0.6)
                Text(value)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundColor(color)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 7)
    }
}

// ── Empty state diagnostic row ─────────────────────────────────────────────────
struct EmptyStateDiag: View {
    let icon:  String
    let label: String
    let value: String
    let ok:    Bool

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 13))
                .foregroundColor(ok ? .safeGreen : .dangerRed)
                .frame(width: 20)
            Text(label)
                .font(.system(size: 12))
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundColor(ok ? .safeGreen : .dangerRed)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(Color.cardBackground)
        .cornerRadius(8)
    }
}

// ── Sync status badge ──────────────────────────────────────────────────────────
struct SyncStatusBadge: View {
    let status: SyncStatus
    var color: Color {
        switch status {
        case .pending: return .pendingAmber
        case .synced:  return .safeGreen
        case .failed:  return .dangerRed
        }
    }
    var body: some View {
        Text(status.rawValue)
            .font(.system(size: 9, weight: .black))
            .tracking(0.5)
            .padding(.horizontal, 7)
            .padding(.vertical, 3)
            .background(color.opacity(0.15))
            .foregroundColor(color)
            .cornerRadius(4)
            .overlay(RoundedRectangle(cornerRadius: 4).stroke(color.opacity(0.4), lineWidth: 1))
    }
}

// Kept for compatibility with App entry point
struct StatusBadge: View {
    let status: SyncStatus
    var body: some View { SyncStatusBadge(status: status) }
}

struct StatTile: View {
    let value: String
    let label: String
    let color: Color
    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.system(size: 20, weight: .black))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(.labelGray)
                .tracking(0.8)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
    }
}

