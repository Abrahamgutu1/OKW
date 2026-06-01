// OKWFieldSyncApp.swift
// OKW FieldSync — App entry point

import SwiftUI
import SwiftData

@main
struct OKWFieldSyncApp: App {

    var body: some Scene {
        WindowGroup {
            RootView()
                .modelContainer(for: InspectionRecord.self)
        }
    }
}

// ── Tab navigation ─────────────────────────────────────────────────────────────
struct RootView: View {
    var body: some View {
        TabView {
            InspectionFormView()
                .tabItem {
                    Label("Capture", systemImage: "camera.fill")
                }

            SyncQueueView()
                .tabItem {
                    Label("Queue", systemImage: "tray.full.fill")
                }
        }
        .accentColor(.accentTeal)
    }
}
