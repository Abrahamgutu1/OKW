// SyncQueueView.swift
// OKW FieldSync — Local sync queue dashboard
// Shows all pending records with export / AirDrop trigger

import SwiftUI
import SwiftData

struct SyncQueueView: View {

    @Environment(\.modelContext) private var context
    @Query(sort: \InspectionRecord.capturedAt, order: .reverse)
    private var records: [InspectionRecord]

    @State private var selectedIDs   = Set<UUID>()
    @State private var selectAll     = false
    @State private var showDeleteAlert = false

    private var pendingRecords: [InspectionRecord] {
        records.filter { $0.status == .pending }
    }

    private var selectedRecords: [InspectionRecord] {
        records.filter { selectedIDs.contains($0.id) }
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.fieldBackground.ignoresSafeArea()

                VStack(spacing: 0) {

                    // ── Header ─────────────────────────────────────────────
                    headerBar

                    // ── Stats strip ────────────────────────────────────────
                    statsStrip

                    if records.isEmpty {
                        emptyState
                    } else {
                        // ── Toolbar ────────────────────────────────────────
                        selectionToolbar

                        // ── Record list ────────────────────────────────────
                        List {
                            ForEach(records) { record in
                                QueueRow(
                                    record:     record,
                                    isSelected: selectedIDs.contains(record.id)
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
                                .listRowInsets(EdgeInsets(
                                    top: 0, leading: 16, bottom: 0, trailing: 16))
                                .listRowSeparatorTint(Color(UIColor.separator))
                            }
                            .onDelete(perform: deleteRecords)
                        }
                        .listStyle(.plain)
                        .background(Color.fieldBackground)

                        // ── Export button ──────────────────────────────────
                        exportBar
                    }
                }
            }
            .navigationBarHidden(true)
            .alert("Delete Records", isPresented: $showDeleteAlert) {
                Button("Delete", role: .destructive) { deleteSelected() }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Remove \(selectedIDs.count) record(s) from the queue? This cannot be undone.")
            }
        }
    }

    // ── Header ─────────────────────────────────────────────────────────────────
    private var headerBar: some View {
        HStack(spacing: 12) {
            Image(systemName: "tray.full.fill")
                .font(.title2)
                .foregroundColor(.white)
                .frame(width: 36, height: 36)
                .background(Color.accentTeal)
                .cornerRadius(6)

            VStack(alignment: .leading, spacing: 1) {
                Text("Sync Queue")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundColor(.white)
                Text("Pending field inspection records")
                    .font(.system(size: 11))
                    .foregroundColor(.white.opacity(0.7))
            }
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.navyHeader)
    }

    // ── Stats strip ────────────────────────────────────────────────────────────
    private var statsStrip: some View {
        HStack(spacing: 0) {
            StatTile(value: "\(records.count)",  label: "Total",   color: .accentTeal)
            Divider().frame(height: 40)
            StatTile(value: "\(pendingRecords.count)", label: "Pending", color: .pendingAmber)
            Divider().frame(height: 40)
            StatTile(value: "\(records.filter{$0.status == .synced}.count)",
                     label: "Synced", color: .safeGreen)
        }
        .background(Color.cardBackground)
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)),
                 alignment: .bottom)
    }

    // ── Selection toolbar ──────────────────────────────────────────────────────
    private var selectionToolbar: some View {
        HStack(spacing: 12) {
            Button(action: toggleSelectAll) {
                Text(selectAll ? "Deselect All" : "Select All")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.accentTeal)
            }
            Spacer()
            if !selectedIDs.isEmpty {
                Text("\(selectedIDs.count) selected")
                    .font(.system(size: 12))
                    .foregroundColor(.labelGray)

                Button(action: { showDeleteAlert = true }) {
                    Image(systemName: "trash")
                        .foregroundColor(.dangerRed)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color(UIColor.systemGray6))
        .overlay(Rectangle().frame(height: 1).foregroundColor(Color(UIColor.separator)),
                 alignment: .bottom)
    }

    // ── Export/AirDrop bar ─────────────────────────────────────────────────────
    private var exportBar: some View {
        VStack(spacing: 0) {
            Divider()
            HStack(spacing: 12) {
                ShareSheetButton(
                    records: selectedRecords.isEmpty ? pendingRecords : selectedRecords,
                    label: selectedRecords.isEmpty
                        ? "Export All Pending (\(pendingRecords.count))"
                        : "Export Selected (\(selectedRecords.count))"
                )
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.cardBackground)
        }
    }

    // ── Empty state ────────────────────────────────────────────────────────────
    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "tray")
                .font(.system(size: 48))
                .foregroundColor(.labelGray)
            Text("No Records in Queue")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.primary)
            Text("Capture inspections using the Capture tab.\nRecords will appear here ready to sync.")
                .font(.system(size: 14))
                .foregroundColor(.labelGray)
                .multilineTextAlignment(.center)
            Spacer()
        }
        .padding()
    }

    // ── Helpers ────────────────────────────────────────────────────────────────
    private func toggleSelectAll() {
        selectAll.toggle()
        if selectAll {
            selectedIDs = Set(records.map(\.id))
        } else {
            selectedIDs.removeAll()
        }
    }

    private func deleteRecords(at offsets: IndexSet) {
        for index in offsets {
            context.delete(records[index])
        }
        try? context.save()
    }

    private func deleteSelected() {
        records
            .filter { selectedIDs.contains($0.id) }
            .forEach { context.delete($0) }
        try? context.save()
        selectedIDs.removeAll()
        selectAll = false
    }
}

// ── Queue row ──────────────────────────────────────────────────────────────────
struct QueueRow: View {
    let record:     InspectionRecord
    let isSelected: Bool

    private var formatter: DateFormatter {
        let f = DateFormatter()
        f.dateFormat = "MM/dd/yy  HH:mm"
        return f
    }

    var body: some View {
        HStack(spacing: 12) {
            // Selection indicator
            Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isSelected ? .accentTeal : .labelGray)
                .font(.title3)

            // Record info
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Text("SL-\(record.serviceLineID)")
                        .font(.system(size: 15, weight: .bold))
                    Text("·")
                        .foregroundColor(.labelGray)
                    Text("EV-\(record.evidenceID)")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.accentTeal)
                }
                Text(formatter.string(from: record.capturedAt))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(.labelGray)
                Text(String(format: "%.4f,  %.4f",
                            record.gpsLatitude, record.gpsLongitude))
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(.labelGray)
            }

            Spacer()

            // Status badge
            StatusBadge(status: record.status)
        }
        .padding(.vertical, 12)
        .background(isSelected
                    ? Color.accentTeal.opacity(0.05)
                    : Color.cardBackground)
    }
}

// ── Status badge ───────────────────────────────────────────────────────────────
struct StatusBadge: View {
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
            .font(.system(size: 10, weight: .bold))
            .tracking(0.5)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.15))
            .foregroundColor(color)
            .cornerRadius(4)
            .overlay(RoundedRectangle(cornerRadius: 4).stroke(color.opacity(0.4), lineWidth: 1))
    }
}

// ── Stat tile ──────────────────────────────────────────────────────────────────
struct StatTile: View {
    let value: String
    let label: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(color)
            Text(label)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(.labelGray)
                .tracking(0.8)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
    }
}
