// DesignSystem.swift
// OKW FieldSync — Unified design system
// All colors, typography, and reusable view components

import SwiftUI

// ── MARK: Color Palette ────────────────────────────────────────────────────────
extension Color {
    // Brand
    static let brand        = Color(hex: "0062BD")
    static let brandDark    = Color(hex: "004A8F")
    static let brandLight   = Color(hex: "E8F2FB")

    // Background layers
    static let appBG        = Color(hex: "0F1923")   // deepest background
    static let surfaceBG    = Color(hex: "1A2535")   // card surface
    static let elevatedBG   = Color(hex: "243044")   // elevated surface
    static let inputBG      = Color(hex: "0A1220")   // input fields

    // Borders
    static let borderSubtle = Color(hex: "2D3F5A")
    static let borderStrong = Color(hex: "4A6080")

    // Text
    static let textPrimary  = Color(hex: "F0F4F8")
    static let textSecondary = Color(hex: "8BA0B8")
    static let textMuted    = Color(hex: "4A6080")

    // Semantic
    static let danger       = Color(hex: "EF4444")
    static let dangerBG     = Color(hex: "EF4444").opacity(0.12)
    static let warning      = Color(hex: "F59E0B")
    static let warningBG    = Color(hex: "F59E0B").opacity(0.12)
    static let success      = Color(hex: "10B981")
    static let successBG    = Color(hex: "10B981").opacity(0.12)
    static let teal         = Color(hex: "06B6D4")
    static let tealBG       = Color(hex: "06B6D4").opacity(0.12)

    // ── Legacy field-app aliases (used by InspectionFormView & SyncQueueView) ──
    static let fieldBackground = Color(hex: "0F1923")   // = appBG
    static let cardBackground  = Color(hex: "1A2535")   // = surfaceBG
    static let navyHeader      = Color(hex: "0A1830")   // dark nav bar
    static let accentTeal      = Color(hex: "06B6D4")   // = teal
    static let pendingAmber    = Color(hex: "F59E0B")   // = warning
    static let safeGreen       = Color(hex: "10B981")   // = success
    static let dangerRed       = Color(hex: "EF4444")   // = danger
    static let labelGray       = Color(hex: "8BA0B8")   // = textSecondary

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: .alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255
        let g = Double((int >> 8)  & 0xFF) / 255
        let b = Double(int & 0xFF)          / 255
        self.init(red: r, green: g, blue: b)
    }
}

// ── MARK: Typography ───────────────────────────────────────────────────────────
extension Font {
    static let displayLarge  = Font.system(size: 28, weight: .bold,   design: .default)
    static let displayMedium = Font.system(size: 22, weight: .bold,   design: .default)
    static let headingLarge  = Font.system(size: 17, weight: .bold,   design: .default)
    static let headingMedium = Font.system(size: 15, weight: .semibold, design: .default)
    static let headingSmall  = Font.system(size: 13, weight: .semibold, design: .default)
    static let bodyLarge     = Font.system(size: 15, weight: .regular, design: .default)
    static let bodyMedium    = Font.system(size: 13, weight: .regular, design: .default)
    static let bodySmall     = Font.system(size: 11, weight: .regular, design: .default)
    static let labelLarge    = Font.system(size: 11, weight: .bold,   design: .default)
    static let labelSmall    = Font.system(size: 9,  weight: .bold,   design: .default)
    static let mono          = Font.system(size: 13, weight: .medium, design: .monospaced)
    static let monoSmall     = Font.system(size: 11, weight: .regular, design: .monospaced)
}

// ── MARK: Reusable Components ──────────────────────────────────────────────────

// Section header label
struct SectionLabel: View {
    let text: String
    var body: some View {
        Text(text.uppercased())
            .font(.labelSmall)
            .tracking(1.2)
            .foregroundColor(.textMuted)
            .padding(.horizontal, 4)
    }
}

// Card container
struct FieldCard<Content: View>: View {
    var accentColor: Color = .brand
    var showAccent: Bool = true
    let content: Content

    init(accentColor: Color = .brand, showAccent: Bool = true, @ViewBuilder content: () -> Content) {
        self.accentColor = accentColor
        self.showAccent  = showAccent
        self.content     = content()
    }

    var body: some View {
        HStack(spacing: 0) {
            if showAccent {
                Rectangle()
                    .fill(accentColor)
                    .frame(width: 3)
            }
            VStack(alignment: .leading, spacing: 0) {
                content
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(Color.surfaceBG)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(Color.borderSubtle, lineWidth: 1)
        )
    }
}

// Generic color+label badge — use TagBadge for arbitrary colors, StatusBadge (SyncQueueView) for sync states
struct TagBadge: View {
    let label: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 5, height: 5)
            Text(label)
                .font(.labelSmall)
                .tracking(0.5)
        }
        .foregroundColor(color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.12))
        .clipShape(Capsule())
        .overlay(Capsule().stroke(color.opacity(0.3), lineWidth: 1))
    }
}

// Primary action button
struct PrimaryButton: View {
    let label: String
    let icon:  String
    var color: Color = .brand
    var isLoading: Bool = false
    var isDisabled: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.85)
                } else {
                    Image(systemName: icon)
                        .font(.system(size: 15, weight: .semibold))
                }
                Text(isLoading ? "Processing…" : label)
                    .font(.headingMedium)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .foregroundColor(isDisabled ? .textMuted : .white)
            .background(
                isDisabled
                    ? Color.borderSubtle
                    : color
            )
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .disabled(isDisabled || isLoading)
    }
}

// Secondary button
struct SecondaryButton: View {
    let label: String
    let icon:  String
    var color: Color = .textSecondary
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 13, weight: .semibold))
                Text(label)
                    .font(.headingSmall)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 44)
            .foregroundColor(color)
            .background(color.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(color.opacity(0.3), lineWidth: 1)
            )
        }
    }
}

// Form text field
struct FieldInput: View {
    let label:        String
    let placeholder:  String
    @Binding var text: String
    var keyboardType: UIKeyboardType = .default
    var icon:         String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            SectionLabel(text: label)
            HStack(spacing: 10) {
                if let icon {
                    Image(systemName: icon)
                        .font(.system(size: 14))
                        .foregroundColor(.textMuted)
                        .frame(width: 20)
                }
                TextField(placeholder, text: $text)
                    .keyboardType(keyboardType)
                    .font(.bodyLarge)
                    .foregroundColor(.textPrimary)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 13)
            .background(Color.inputBG)
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(text.isEmpty ? Color.borderSubtle : Color.brand.opacity(0.6), lineWidth: 1)
            )
        }
    }
}

// Checklist row
struct ChecklistRow: View {
    let done:  Bool
    let label: String

    var body: some View {
        HStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(done ? Color.success : Color.borderSubtle)
                    .frame(width: 18, height: 18)
                Image(systemName: done ? "checkmark" : "circle")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(done ? .white : .textMuted)
            }
            Text(label)
                .font(.bodySmall)
                .foregroundColor(done ? .textSecondary : .textMuted)
        }
    }
}

// Divider
struct FieldDivider: View {
    var body: some View {
        Rectangle()
            .fill(Color.borderSubtle)
            .frame(height: 1)
    }
}

// Page header
struct PageHeader: View {
    let title:    String
    let subtitle: String
    var trailing: AnyView? = nil
    
    var body: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.displayMedium)
                    .foregroundColor(.textPrimary)
                Text(subtitle)
                    .font(.bodySmall)
                    .foregroundColor(.textMuted)
            }
            Spacer()
            trailing
        }
        .padding(.horizontal, 20)
        .padding(.top, 8)
        .padding(.bottom, 4)
    }
}
