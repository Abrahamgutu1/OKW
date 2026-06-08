// OKWFieldSyncApp.swift
// OKW FieldSync — App entry point with JWT auth

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

// ── Root — auth gate ───────────────────────────────────────────────────────────
struct RootView: View {
    @State private var isLoggedIn: Bool = false
    @State private var authUser: OKWUser? = nil

    var body: some View {
        Group {
            if isLoggedIn, let user = authUser {
                MainTabView(user: user, onLogout: handleLogout)
            } else {
                OKWLoginView(onLogin: handleLogin)
            }
        }
        .onAppear { restoreSession() }
    }

    private func restoreSession() {
        guard
            let token    = UserDefaults.standard.string(forKey: "okw_token"),
            let username = UserDefaults.standard.string(forKey: "okw_username"),
            let fullName = UserDefaults.standard.string(forKey: "okw_full_name"),
            let utilityId = UserDefaults.standard.string(forKey: "okw_utility_id"),
            !token.isEmpty
        else { return }
        authUser  = OKWUser(username: username, fullName: fullName,
                            utilityId: utilityId, token: token)
        isLoggedIn = true
    }

    private func handleLogin(_ user: OKWUser) {
        UserDefaults.standard.set(user.token,     forKey: "okw_token")
        UserDefaults.standard.set(user.username,  forKey: "okw_username")
        UserDefaults.standard.set(user.fullName,  forKey: "okw_full_name")
        UserDefaults.standard.set(user.utilityId, forKey: "okw_utility_id")
        authUser   = user
        isLoggedIn = true
    }

    private func handleLogout() {
        UserDefaults.standard.removeObject(forKey: "okw_token")
        UserDefaults.standard.removeObject(forKey: "okw_username")
        UserDefaults.standard.removeObject(forKey: "okw_full_name")
        UserDefaults.standard.removeObject(forKey: "okw_utility_id")
        authUser   = nil
        isLoggedIn = false
    }
}

// ── User model ─────────────────────────────────────────────────────────────────
struct OKWUser {
    var username:  String
    var fullName:  String
    var utilityId: String
    var token:     String
}

// ── Login View ─────────────────────────────────────────────────────────────────
struct OKWLoginView: View {
    var onLogin: (OKWUser) -> Void

    @State private var username  = ""
    @State private var password  = ""
    @State private var isLoading = false
    @State private var errorMsg  = ""

    // Base URL — update to your Mac's IP for real device testing
    private var baseURL: String {
        NetworkManager.baseURL
    }

    var body: some View {
        ZStack {
            // Dark navy background
            Color(red: 0.04, green: 0.13, blue: 0.26)
                .ignoresSafeArea()

            // Grid pattern overlay
            Canvas { context, size in
                let spacing: CGFloat = 40
                var path = Path()
                var x: CGFloat = 0
                while x <= size.width {
                    path.move(to: CGPoint(x: x, y: 0))
                    path.addLine(to: CGPoint(x: x, y: size.height))
                    x += spacing
                }
                var y: CGFloat = 0
                while y <= size.height {
                    path.move(to: CGPoint(x: 0, y: y))
                    path.addLine(to: CGPoint(x: size.width, y: y))
                    y += spacing
                }
                context.stroke(path, with: .color(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.06)), lineWidth: 1)
            }
            .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 0) {
                    Spacer().frame(height: 60)

                    // Logo
                    VStack(spacing: 12) {
                        HStack(spacing: 10) {
                            ZStack {
                                RoundedRectangle(cornerRadius: 10)
                                    .fill(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.15))
                                    .frame(width: 40, height: 40)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 10)
                                            .stroke(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.4), lineWidth: 1)
                                    )
                                Image(systemName: "mappin.circle.fill")
                                    .foregroundColor(Color(red: 0.03, green: 0.57, blue: 0.70))
                                    .font(.system(size: 20))
                            }
                            Text("OKW FieldSync")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(.white)
                        }
                        Text("EPA LCRI COMPLIANCE PLATFORM")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.white.opacity(0.4))
                            .kerning(1.5)
                    }

                    Spacer().frame(height: 40)

                    // Card
                    VStack(alignment: .leading, spacing: 0) {
                        Text("Sign in")
                            .font(.system(size: 22, weight: .bold))
                            .foregroundColor(.white)
                            .padding(.bottom, 4)

                        Text("Access your utility's compliance dashboard")
                            .font(.system(size: 13))
                            .foregroundColor(.white.opacity(0.4))
                            .padding(.bottom, 28)

                        // Username
                        VStack(alignment: .leading, spacing: 6) {
                            Text("USERNAME")
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(.white.opacity(0.5))
                                .kerning(1.2)
                            TextField("", text: $username)
                                .placeholder(when: username.isEmpty) {
                                    Text("Enter username").foregroundColor(.white.opacity(0.25))
                                }
                                .autocapitalization(.none)
                                .disableAutocorrection(true)
                                .foregroundColor(.white)
                                .padding(12)
                                .background(Color.white.opacity(0.06))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                                )
                        }
                        .padding(.bottom, 16)

                        // Password
                        VStack(alignment: .leading, spacing: 6) {
                            Text("PASSWORD")
                                .font(.system(size: 10, weight: .semibold))
                                .foregroundColor(.white.opacity(0.5))
                                .kerning(1.2)
                            SecureField("", text: $password)
                                .placeholder(when: password.isEmpty) {
                                    Text("Enter password").foregroundColor(.white.opacity(0.25))
                                }
                                .foregroundColor(.white)
                                .padding(12)
                                .background(Color.white.opacity(0.06))
                                .cornerRadius(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.white.opacity(0.12), lineWidth: 1)
                                )
                        }
                        .padding(.bottom, 24)

                        // Error
                        if !errorMsg.isEmpty {
                            HStack(spacing: 8) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.system(size: 12))
                                Text(errorMsg)
                                    .font(.system(size: 12))
                            }
                            .foregroundColor(Color(red: 0.97, green: 0.50, blue: 0.45))
                            .padding(12)
                            .background(Color(red: 0.86, green: 0.15, blue: 0.15).opacity(0.12))
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color(red: 0.86, green: 0.15, blue: 0.15).opacity(0.3), lineWidth: 1)
                            )
                            .padding(.bottom, 16)
                        }

                        // Sign in button
                        Button(action: login) {
                            ZStack {
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(isLoading
                                          ? Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.4)
                                          : Color(red: 0.03, green: 0.57, blue: 0.70))
                                if isLoading {
                                    HStack(spacing: 10) {
                                        ProgressView()
                                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                            .scaleEffect(0.8)
                                        Text("Signing in...")
                                            .font(.system(size: 15, weight: .bold))
                                            .foregroundColor(.white)
                                    }
                                } else {
                                    Text("Sign In")
                                        .font(.system(size: 15, weight: .bold))
                                        .foregroundColor(.white)
                                }
                            }
                            .frame(height: 46)
                        }
                        .disabled(isLoading || username.isEmpty || password.isEmpty)
                    }
                    .padding(28)
                    .background(Color.white.opacity(0.04))
                    .cornerRadius(16)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.white.opacity(0.08), lineWidth: 1)
                    )
                    .padding(.horizontal, 24)

                    Spacer().frame(height: 16)

                    // Demo credentials hint
                    VStack(alignment: .leading, spacing: 6) {
                        Text("DEMO CREDENTIALS")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(Color(red: 0.03, green: 0.57, blue: 0.70))
                            .kerning(1.2)
                        Text("admin / OKW_Admin_2026!")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(.white.opacity(0.5))
                        Text("inspector1 / Inspector_2026!")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(.white.opacity(0.5))
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(14)
                    .background(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.08))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.2), lineWidth: 1)
                    )
                    .padding(.horizontal, 24)

                    Spacer().frame(height: 24)

                    Text("OKW FieldSync v2.0 · PWSID OK1020401 · ODEQ 2026")
                        .font(.system(size: 10))
                        .foregroundColor(.white.opacity(0.2))

                    Spacer().frame(height: 40)
                }
            }
        }
    }

    private func login() {
        guard !username.isEmpty, !password.isEmpty else { return }
        isLoading = true
        errorMsg  = ""

        guard let url = URL(string: "\(baseURL)/api/auth/login") else {
            errorMsg  = "Invalid server URL"
            isLoading = false
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15

        let bodyStr = "username=\(username.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? username)&password=\(password.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? password)"
        request.httpBody = bodyStr.data(using: .utf8)

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                isLoading = false
                if let error = error {
                    errorMsg = "Cannot reach server — \(error.localizedDescription)"
                    return
                }
                guard let data = data,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
                else {
                    errorMsg = "Invalid server response"
                    return
                }
                if let token = json["access_token"] as? String {
                    let user = OKWUser(
                        username:  json["username"]   as? String ?? username,
                        fullName:  json["full_name"]  as? String ?? username,
                        utilityId: json["utility_id"] as? String ?? "OK1020401",
                        token:     token
                    )
                    onLogin(user)
                } else {
                    let detail = json["detail"] as? String ?? "Invalid username or password"
                    errorMsg = detail
                }
            }
        }.resume()
    }
}

// ── Main Tab View (post-login) ─────────────────────────────────────────────────
struct MainTabView: View {
    let user:     OKWUser
    let onLogout: () -> Void

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

            // User info / logout tab
            ProfileView(user: user, onLogout: onLogout)
                .tabItem {
                    Label("Account", systemImage: "person.circle.fill")
                }
        }
        .accentColor(.accentTeal)
    }
}

// ── Profile / logout tab ──────────────────────────────────────────────────────
struct ProfileView: View {
    let user:     OKWUser
    let onLogout: () -> Void

    var body: some View {
        ZStack {
            Color(red: 0.05, green: 0.07, blue: 0.10).ignoresSafeArea()
            VStack(spacing: 24) {
                Spacer()

                // Avatar
                ZStack {
                    Circle()
                        .fill(Color(red: 0.03, green: 0.57, blue: 0.70).opacity(0.15))
                        .frame(width: 80, height: 80)
                    Text(String(user.fullName.prefix(1)).uppercased())
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(Color(red: 0.03, green: 0.57, blue: 0.70))
                }

                VStack(spacing: 4) {
                    Text(user.fullName)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.white)
                    Text("@\(user.username)")
                        .font(.system(size: 13))
                        .foregroundColor(.white.opacity(0.5))
                }

                // Info card
                VStack(spacing: 0) {
                    infoRow(label: "Utility ID", value: user.utilityId)
                    Divider().background(Color.white.opacity(0.08))
                    infoRow(label: "PWSID", value: "OK1020401")
                    Divider().background(Color.white.opacity(0.08))
                    infoRow(label: "Platform", value: "OKW FieldSync v2.0")
                    Divider().background(Color.white.opacity(0.08))
                    infoRow(label: "Regulation", value: "ODEQ LCRI §141.84")
                }
                .background(Color.white.opacity(0.04))
                .cornerRadius(12)
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.white.opacity(0.08), lineWidth: 1))
                .padding(.horizontal, 24)

                Spacer()

                // Sign out button
                Button(action: onLogout) {
                    HStack(spacing: 8) {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                        Text("Sign Out")
                            .fontWeight(.semibold)
                    }
                    .foregroundColor(Color(red: 0.97, green: 0.32, blue: 0.28))
                    .frame(maxWidth: .infinity)
                    .padding(14)
                    .background(Color(red: 0.86, green: 0.15, blue: 0.15).opacity(0.12))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color(red: 0.86, green: 0.15, blue: 0.15).opacity(0.3), lineWidth: 1)
                    )
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 40)
            }
        }
        .navigationTitle("Account")
    }

    private func infoRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.white.opacity(0.5))
                .frame(width: 110, alignment: .leading)
            Spacer()
            Text(value)
                .font(.system(size: 12, design: .monospaced))
                .foregroundColor(.white.opacity(0.8))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
}

// ── Placeholder extension ──────────────────────────────────────────────────────
extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content
    ) -> some View {
        ZStack(alignment: alignment) {
            placeholder().allowsHitTesting(false)
            self
        }
    }
}
