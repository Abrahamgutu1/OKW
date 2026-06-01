// LaunchScreen.swift
// OKW FieldSync — Launch screen
// Add as the initial view before ContentView loads

import SwiftUI

struct LaunchScreenView: View {

    @State private var progress: CGFloat = 0
    @State private var opacity:  Double  = 0

    var body: some View {
        ZStack {
            // Brand blue background
            Color(hex: "0062BD")
                .ignoresSafeArea()

            // Subtle grid overlay
            GeometryReader { geo in
                Path { path in
                    let spacing: CGFloat = 40
                    var x: CGFloat = 0
                    while x <= geo.size.width {
                        path.move(to: CGPoint(x: x, y: 0))
                        path.addLine(to: CGPoint(x: x, y: geo.size.height))
                        x += spacing
                    }
                    var y: CGFloat = 0
                    while y <= geo.size.height {
                        path.move(to: CGPoint(x: 0, y: y))
                        path.addLine(to: CGPoint(x: geo.size.width, y: y))
                        y += spacing
                    }
                }
                .stroke(Color.white.opacity(0.05), lineWidth: 0.5)
            }

            VStack(spacing: 0) {
                Spacer()

                // Icon
                ZStack {
                    RoundedRectangle(cornerRadius: 20, style: .continuous)
                        .fill(Color.white.opacity(0.15))
                        .frame(width: 80, height: 80)

                    // Water drop
                    WaterDropShape()
                        .fill(Color.white)
                        .frame(width: 44, height: 52)
                        .overlay(
                            VStack(spacing: 4) {
                                Spacer()
                                Rectangle()
                                    .fill(Color(hex: "0062BD"))
                                    .frame(width: 22, height: 2)
                                    .cornerRadius(1)
                                Rectangle()
                                    .fill(Color(hex: "0062BD").opacity(0.5))
                                    .frame(width: 18, height: 1.5)
                                    .cornerRadius(0.75)
                                Spacer().frame(height: 8)
                            }
                        )
                }
                .opacity(opacity)

                Spacer().frame(height: 24)

                // App name
                Text("OKW FieldSync")
                    .font(.system(size: 26, weight: .bold, design: .default))
                    .foregroundColor(.white)
                    .opacity(opacity)

                Spacer().frame(height: 6)

                Text("Lead Service Line Inventory")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.white.opacity(0.65))
                    .opacity(opacity)

                Spacer().frame(height: 48)

                // Progress bar
                VStack(spacing: 8) {
                    ZStack(alignment: .leading) {
                        Capsule()
                            .fill(Color.white.opacity(0.2))
                            .frame(width: 120, height: 3)
                        Capsule()
                            .fill(Color.white.opacity(0.85))
                            .frame(width: 120 * progress, height: 3)
                    }
                    .opacity(opacity)

                    Text("PWSID: OK1020401")
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(.white.opacity(0.4))
                        .opacity(opacity)
                }

                Spacer()

                // Bottom badge
                HStack(spacing: 6) {
                    Text("Oklahoma DEQ LCRR/LCRI Compliance")
                        .font(.system(size: 10))
                        .foregroundColor(.white.opacity(0.35))
                }
                .padding(.bottom, 40)
                .opacity(opacity)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.5)) { opacity = 1 }
            withAnimation(.easeInOut(duration: 1.2).delay(0.3)) { progress = 1 }
        }
    }
}

// Water drop shape
struct WaterDropShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let w = rect.width
        let h = rect.height
        let cx = w / 2

        path.move(to: CGPoint(x: cx, y: 0))
        path.addCurve(
            to: CGPoint(x: w, y: h * 0.65),
            control1: CGPoint(x: w, y: h * 0.25),
            control2: CGPoint(x: w, y: h * 0.45)
        )
        path.addCurve(
            to: CGPoint(x: cx, y: h),
            control1: CGPoint(x: w, y: h * 0.85),
            control2: CGPoint(x: cx + w * 0.3, y: h)
        )
        path.addCurve(
            to: CGPoint(x: 0, y: h * 0.65),
            control1: CGPoint(x: cx - w * 0.3, y: h),
            control2: CGPoint(x: 0, y: h * 0.85)
        )
        path.addCurve(
            to: CGPoint(x: cx, y: 0),
            control1: CGPoint(x: 0, y: h * 0.45),
            control2: CGPoint(x: 0, y: h * 0.25)
        )
        path.closeSubpath()
        return path
    }
}
