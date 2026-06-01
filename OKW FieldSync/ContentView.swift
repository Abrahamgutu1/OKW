import SwiftUI

enum AppTab: Int, CaseIterable {
    case home, inventory, shop, macros

    var title: String {
        switch self {
        case .home:      return "Recipes"
        case .inventory: return "Inventory"
        case .shop:      return "Shop"
        case .macros:    return "Macros"
        }
    }

    var icon: String {
        switch self {
        case .home:      return "fork.knife"
        case .inventory: return "square.grid.2x2.fill"
        case .shop:      return "cart.fill"
        case .macros:    return "checkmark.circle.fill"
        }
    }
}

struct ContentView: View {
    @State private var selectedTab: AppTab = .home
    @State private var isLoggedIn = false

    var body: some View {
        ZStack {
            AppTheme.bg.ignoresSafeArea()
            if isLoggedIn {
                MainTabView(selectedTab: $selectedTab, isLoggedIn: $isLoggedIn)
            } else {
                LoginView(isLoggedIn: $isLoggedIn)
            }
        }
        .onAppear { checkSession() }
    }

    private func checkSession() {
        // Verify the session is still valid
        guard let token = UserDefaults.standard.string(forKey: "access_token"),
              let userId = UserDefaults.standard.string(forKey: "user_id"),
              !token.isEmpty, !userId.isEmpty else {
            // No valid session — show login
            isLoggedIn = false
            return
        }
        // Session exists — verify it's still valid with Supabase
        Task {
            do {
                let url = URL(string: "\(Config.supabaseURL)/auth/v1/user")!
                var request = URLRequest(url: url)
                request.setValue(Config.supabaseKey, forHTTPHeaderField: "apikey")
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                let (_, response) = try await URLSession.shared.data(for: request)
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    await MainActor.run {
                        SupabaseService.shared.accessToken = token
                        SupabaseService.shared.currentUser = SupabaseUser(id: userId, email: UserDefaults.standard.string(forKey: "user_email"))
                        SupabaseService.shared.isAuthenticated = true
                        isLoggedIn = true
                    }
                } else {
                    // Token expired — clear and show login
                    await MainActor.run { clearSessionAndLogout() }
                }
            } catch {
                await MainActor.run { clearSessionAndLogout() }
            }
        }
    }

    private func clearSessionAndLogout() {
        UserDefaults.standard.removeObject(forKey: "access_token")
        UserDefaults.standard.removeObject(forKey: "user_id")
        UserDefaults.standard.removeObject(forKey: "user_email")
        SupabaseService.shared.signOut()
        isLoggedIn = false
    }
}

struct MainTabView: View {
    @Binding var selectedTab: AppTab
    @Binding var isLoggedIn: Bool

    var body: some View {
        ZStack(alignment: .bottom) {
            Group {
                switch selectedTab {
                case .home:      HomeView()
                case .inventory: InventoryView()
                case .shop:      ShopPlaceholderView()
                case .macros:    MacrosView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            CustomTabBar(selectedTab: $selectedTab)
        }
        .ignoresSafeArea(edges: .bottom)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Sign Out") {
                    SupabaseService.shared.signOut()
                    isLoggedIn = false
                }
                .foregroundColor(AppTheme.green)
            }
        }
    }
}

struct CustomTabBar: View {
    @Binding var selectedTab: AppTab

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AppTab.allCases, id: \.rawValue) { tab in
                TabBarItem(tab: tab, isSelected: selectedTab == tab)
                    .onTapGesture {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedTab = tab
                        }
                    }
            }
        }
        .padding(.top, 12)
        .padding(.bottom, 28)
        .background(
            AppTheme.bg2
                .overlay(
                    Rectangle()
                        .frame(height: 0.5)
                        .foregroundColor(Color.white.opacity(0.08)),
                    alignment: .top
                )
        )
    }
}

struct TabBarItem: View {
    let tab: AppTab
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: tab.icon)
                .font(.system(size: 20, weight: isSelected ? .bold : .regular))
                .foregroundColor(isSelected ? AppTheme.green : AppTheme.textTertiary)
            Text(tab.title)
                .font(.appBody(10, weight: isSelected ? .medium : .regular))
                .foregroundColor(isSelected ? AppTheme.green : AppTheme.textTertiary)
            Circle()
                .fill(AppTheme.green)
                .frame(width: 4, height: 4)
                .opacity(isSelected ? 1 : 0)
        }
        .frame(maxWidth: .infinity)
        .contentShape(Rectangle())
    }
}

struct ShopPlaceholderView: View {
    var body: some View {
        ZStack {
            AppTheme.bg.ignoresSafeArea()
            VStack(spacing: 12) {
                Image(systemName: "cart.fill")
                    .font(.system(size: 48))
                    .foregroundColor(AppTheme.green)
                Text("Shop")
                    .font(.appDisplay(24))
                    .foregroundColor(AppTheme.textPrimary)
                Text("Coming soon")
                    .font(.appBody(14))
                    .foregroundColor(AppTheme.textSecondary)
            }
        }
    }
}

#Preview { ContentView() }
